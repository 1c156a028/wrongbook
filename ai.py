"""调用大模型分析错题。

三条设计原则（面试也会问）：
1. 没配置 key → 功能整体"消失"，主流程完全不受影响
2. 出任何异常 → 只打日志、返回 None，绝不让页面报 500
3. 要求模型输出 JSON → 程序能直接解析，而不是拿回一段散文
"""

import json
import os

import requests

# 百炼的 OpenAI 兼容地址。换别家（智谱/DeepSeek）只需要改这一行
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
TIMEOUT = 45  # 秒：大模型偶尔慢，给足时间，但别无限等
MAX_TOKENS = 600  # 限制输出长度：省钱，也防止模型"跑飞"

# 系统提示词：定义模型的角色和输出格式。改这段 = 改 AI 的行为
# 注意：不要在这里穷举语言/学科，列举永远不全。
# 正确做法是给它"判断依据"（先自己判断）+ "护栏"（不确定就说不知道）
SYSTEM_PROMPT = (
    "你是一位编程与算法教练，也懂大学低年级的基础课（高数、线代、数据结构）。"
    "学生会给你一道错题，包含：题目、他自己写的解法或代码、以及他自己认为的错因。\n"
    "注意：他的代码可能是 C++、Python、Java 或伪代码，也可能根本不是编程题。"
    "先自己判断这是什么学科、什么语言，不要假设。\n"
    "如果给的信息不足以判断错在哪，就直说信息不足，不要编一个错误出来。\n"
    "学生是大一，讲解要具体、口语化，不要堆术语。\n"
    "严格只输出一个 JSON 对象，不要加 markdown 代码块，不要输出任何解释性文字。格式："
    '{"subject":"编程/算法/数学/其他 之一","language":"C++/Python/Java/伪代码/无（非编程题）",'
    '"error_point":"20字内指出真正的错误","why":"80字内说明为什么错",'
    '"fix":"80字内说明怎么改","tags":["最多3个知识点"],"difficulty":1到5的整数}'
)


def is_configured():
    """有没有配置 key。模板用它决定要不要显示【AI 诊断】按钮。"""
    return bool(os.environ.get("DASHSCOPE_API_KEY"))


def analyze_record(title, content, code, reason):
    """分析一道错题。成功返回 dict，失败返回 None。"""
    key = os.environ.get("DASHSCOPE_API_KEY")
    if not key:
        return None

    # 把 4 个字段拼成一段"人话"。比直接丢 JSON 给模型效果好得多
    user_prompt = (
        f"【题目】{title}\n\n"
        f"【题面/思路】{content or '（没写）'}\n\n"
        f"【我的代码】\n{code or '（没写）'}\n\n"
        f"【我认为的错因】{reason or '（没写）'}"
    )

    payload = {
        "model": os.environ.get("AI_MODEL", "qwen-plus"),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,  # 0~1，越低越稳定
        "max_tokens": MAX_TOKENS,
        "response_format": {"type": "json_object"},  # 强制输出 JSON
    }

    try:
        resp = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {key}"},
            json=payload,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
        return json.loads(text)
    except Exception as e:
        # 超时、额度用完、模型抽风……全落到这里，只记日志
        print(f"[AI] 分析失败: {type(e).__name__}: {e}")
        return None
