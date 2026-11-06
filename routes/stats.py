"""统计页。

这是项目的"亮点功能"：一眼看出自己哪个知识点最弱。
对应执行计划的 D15。
"""
from flask import Blueprint, render_template

bp = Blueprint("stats", __name__)


@bp.route("/stats")
def stats():
    return render_template(
        "placeholder.html",
        title="统计",
        steps=[
            "本周新增：SELECT COUNT(*) FROM records WHERE user_id=? AND created_at >= ?",
            "标签分布：按 tag 分组计数，配合 GROUP BY + ORDER BY COUNT(*) DESC",
            "薄弱 Top3：错题数最多的 3 个标签",
            "难度分布：按 difficulty 分组计数",
            "（可选）用 Chart.js 把数字画成柱状图",
        ],
    )
