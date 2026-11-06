"""重建数据库并写入演示数据。

用法：
    python seed.py

警告：会删除并重建 DATABASE 指向的数据库文件，里面的数据全部丢失。
这是故意的——开发阶段你需要能随时"一键回到干净状态"。
"""
import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

from config import Config

BASE_DIR = Path(__file__).resolve().parent

# (标题, 题面/思路, 我写的代码, 错误原因, 难度, [标签])
DEMO_RECORDS = [
    (
        "01 背包 一维数组写法",
        "有 n 件物品，每件有重量 w 和价值 v，背包容量 V，求最大价值。",
        "for (int i = 1; i <= n; i++)\n"
        "    for (int j = w[i]; j <= V; j++)          // 错：这里应该是倒序\n"
        "        dp[j] = max(dp[j], dp[j - w[i]] + v[i]);",
        "一维滚动数组必须倒序遍历容量，否则同一件物品会被重复选。"
        "正序相当于完全背包。记住：01 背包倒着走，完全背包正着走。",
        4,
        ["DP"],
    ),
    (
        "二分查找 边界写错",
        "在有序数组里找第一个 >= x 的位置。",
        "while (l < r) {\n"
        "    int mid = (l + r) / 2;\n"
        "    if (a[mid] >= x) r = mid - 1;   // 错：应该是 r = mid\n"
        "    else l = mid + 1;\n"
        "}",
        "想找「第一个满足条件」的位置时，r 要收缩到 mid（保留 mid 作为候选），"
        "写成 mid-1 会把答案自己排除掉。",
        3,
        ["二分"],
    ),
    (
        "BFS 网格最短路的 visited 时机",
        "上下左右走迷宫，求起点到终点的最少步数。",
        "q.push(start);\n"
        "while (!q.empty()) {\n"
        "    auto cur = q.front(); q.pop();\n"
        "    for (dir : 4个方向) {\n"
        "        if (合法 && !vis[nx][ny]) {       // 错：入队时才标记\n"
        "            vis[nx][ny] = 1;\n"
        "            q.push({nx, ny, cur.step + 1});\n"
        "        }\n"
        "    }\n"
        "}",
        "标记必须放在「入队时」，不能放在「出队时」，否则同一个点会被重复入队，"
        "队列爆炸甚至死循环。",
        3,
        ["BFS"],
    ),
    (
        "区间调度 贪心策略选错",
        "给 n 个区间，选尽量多的互不重叠区间。",
        "sort(intervals.begin(), intervals.end());   // 错：按起点排序",
        "应该按右端点升序排，每次选结束最早的，才能给后面留最多空间。"
        "按左端点排会选到很长的区间。",
        4,
        ["贪心"],
    ),
    (
        "字符串 读入带空格的一行",
        "输入一行可能含空格的字符串，统计单词个数。",
        "cin >> s;              // 错：遇到空格就停",
        "要用 getline(cin, s)。而且如果前面用过 cin >>，"
        "要先用 cin.ignore() 吃掉换行符，否则 getline 会读到空串。",
        2,
        ["字符串"],
    ),
    (
        "DP 状态定义没想清楚就写",
        "爬楼梯，每次走 1 或 2 级，求方案数。",
        "// 一开始把 dp[i] 定义成「走到第 i 级需要的步数」，完全卡住\n"
        "dp[i] = dp[i-1] + dp[i-2];",
        "dp[i] 应该定义成「到达第 i 级的方案数」，不是步数。"
        "写转移方程之前，先用一句话说清 dp[i] 到底表示什么，说不清就别写。",
        3,
        ["DP"],
    ),
]


def main():
    db_path = Path(Config.DATABASE)
    if db_path.exists():
        db_path.unlink()
        print(f"已删除旧数据库：{db_path}")

    conn = sqlite3.connect(db_path)
    conn.executescript((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))

    # 演示账号：demo / 123456（密码哈希后存储，库里看不到明文）
    conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("demo", generate_password_hash("123456")),
    )
    user_id = 1

    tag_ids = {}
    for name in ["DP", "二分", "BFS", "贪心", "字符串"]:
        cur = conn.execute("INSERT INTO tags (name) VALUES (?)", (name,))
        tag_ids[name] = cur.lastrowid

    for title, content, code, reason, difficulty, tags in DEMO_RECORDS:
        cur = conn.execute(
            """INSERT INTO records (user_id, title, content, code, reason, difficulty)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, title, content, code, reason, difficulty),
        )
        record_id = cur.lastrowid
        for t in tags:
            conn.execute(
                "INSERT INTO record_tags (record_id, tag_id) VALUES (?, ?)",
                (record_id, tag_ids[t]),
            )

    conn.commit()

    n_records = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    n_tags = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    conn.close()

    print(f"数据库已初始化：{db_path}")
    print(f"  用户：1 个（demo / 123456）")
    print(f"  错题：{n_records} 条")
    print(f"  标签：{n_tags} 个")


if __name__ == "__main__":
    main()
