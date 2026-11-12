"""统计页。

这是项目的"亮点功能"：一眼看出自己哪个知识点最弱。
"""

from flask import Blueprint, render_template, session

from db import query

bp = Blueprint("stats", __name__)


@bp.route("/stats")
def stats():
    user_id = session["user_id"]

    # ① 总题数 + 平均难度：一行 SQL 就出两个数
    #    AVG 在没有数据时返回 NULL，所以模板里要处理"空"的情况
    summary = query(
        "SELECT COUNT(*) AS total, AVG(difficulty) AS avg_diff "
        "FROM records WHERE user_id = ?",
        (user_id,),
        one=True,
    )
    total = summary["total"]
    avg_diff = summary["avg_diff"]

    # ② 近 7 天新增：日期计算交给 SQLite 的 date('now', '-7 days')
    recent = query(
        """SELECT COUNT(*) AS c FROM records
           WHERE user_id = ? AND created_at >= date('now', '-7 days')""",
        (user_id,),
        one=True,
    )["c"]

    # ③ 难度分布：先摆好 1~5 五个格子（某档是 0 也得有），再把数字填进去
    #    列表下标从 0 开始，所以难度 d 放进 diff_counts[d - 1]
    diff_counts = [0, 0, 0, 0, 0]
    rows = query(
        "SELECT difficulty, COUNT(*) AS c FROM records "
        "WHERE user_id = ? GROUP BY difficulty",
        (user_id,),
    )
    for row in rows:
        diff_counts[row["difficulty"] - 1] = row["c"]

    # ④ 标签分布：错得越多的标签排越前，一眼看出弱项
    #    一个标签可能被多道题挂着，所以这里 JOIN 出来再按标签分组
    tag_stats = query(
        """SELECT t.name, COUNT(*) AS cnt
           FROM tags t
           JOIN record_tags rt ON rt.tag_id = t.id
           JOIN records r      ON r.id = rt.record_id
           WHERE r.user_id = ?
           GROUP BY t.id
           ORDER BY cnt DESC, t.name""",
        (user_id,),
    )
    # 画进度条时要知道"最长的那根"是多长，用它当 100%
    tag_max = tag_stats[0]["cnt"] if tag_stats else 1

    return render_template(
        "stats.html",
        total=total,
        avg_diff=avg_diff,
        recent=recent,
        diff_counts=diff_counts,
        tag_stats=tag_stats,
        tag_max=tag_max,
    )
