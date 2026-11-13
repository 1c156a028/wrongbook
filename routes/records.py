"""错题相关页面。

已完成：列表页、详情页（这是"读"的完整链路，先看懂这两条再动手写"写"）
待实现：新增、编辑、删除
"""

from flask import (
    Blueprint,
    abort,
    render_template,
    request,
    session,
    flash,
    redirect,
    url_for,
)

import json

import ai
from db import query, execute

bp = Blueprint("records", __name__)


# 每页显示几条
PER_PAGE = 5

# 基础 SQL：只管"从哪些表取哪些列"，筛选条件在函数里往上加
LIST_SQL = """
    SELECT r.id, r.title, r.difficulty, r.created_at,
           GROUP_CONCAT(t.name, ' / ') AS tag_names
    FROM records r
    LEFT JOIN record_tags rt ON rt.record_id = r.id
    LEFT JOIN tags t        ON t.id = rt.tag_id
"""

# 当前用户用过的所有标签，给筛选下拉框用
TAGS_SQL = """
    SELECT DISTINCT t.name
    FROM tags t
    JOIN record_tags rt ON rt.tag_id = t.id
    JOIN records r      ON r.id = rt.record_id
    WHERE r.user_id = ?
    ORDER BY t.name
"""


@bp.route("/records")
def list_records():
    """错题列表：关键词搜索 + 标签筛选 + 分页。"""
    keyword = request.args.get("q", "").strip()
    tag = request.args.get("tag", "").strip()

    # ① 拼 WHERE：搜索和筛选都只影响 WHERE，先把它攒好
    where = "WHERE r.user_id = ?"
    params = [session["user_id"]]

    if keyword:
        where += " AND (r.title LIKE ? OR r.content LIKE ? OR r.reason LIKE ?)"
        like = f"%{keyword}%"
        params += [like, like, like]

    if tag:
        where += """ AND EXISTS (
                        SELECT 1
                        FROM record_tags rt2
                        JOIN tags t2 ON t2.id = rt2.tag_id
                        WHERE rt2.record_id = r.id AND t2.name = ?
                    )"""
        params.append(tag)

    # ② 先数一共几条（用同样的 where，数的是"筛选后的结果"）
    total = query(f"SELECT COUNT(*) AS c FROM records r {where}", params, one=True)["c"]

    # ③ 算总页数：向上取整。7 条、每页 5 条 → (7+4)//5 = 2 页
    total_pages = (total + PER_PAGE - 1) // PER_PAGE if total else 1

    # ④ 当前第几页：从网址里取 ?page=2；越界就夹回合法范围
    page = request.args.get("page", 1, type=int) or 1
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * PER_PAGE

    # ⑤ 取这一页的数据：LIMIT 取几条，OFFSET 跳过前面几条
    sql = (
        LIST_SQL
        + where
        + " GROUP BY r.id ORDER BY r.created_at DESC, r.id DESC LIMIT ? OFFSET ?"
    )
    records = query(sql, params + [PER_PAGE, offset])

    tags = query(TAGS_SQL, (session["user_id"],))
    return render_template(
        "record_list.html",
        records=records,
        tags=tags,
        keyword=keyword,
        current_tag=tag,
        total=total,
        page=page,
        total_pages=total_pages,
    )


@bp.route("/records/<int:record_id>")
def record_detail(record_id):
    """详情页。

    注意 WHERE 里的 user_id = ?——这一句就是"权限隔离"。
    少了它，别人把 URL 里的 id 一改就能看到你的记录。
    """
    record = query(
        "SELECT * FROM records WHERE id = ? AND user_id = ?",
        (record_id, session["user_id"]),
        one=True,
    )
    if record is None:
        abort(404)  # 不存在或不属于你，统一返回 404，不泄露"存在但无权"

    tags = query(
        """SELECT t.name
           FROM tags t
           JOIN record_tags rt ON rt.tag_id = t.id
           WHERE rt.record_id = ?
           ORDER BY t.name""",
        (record_id,),
    )
    # AI 诊断结果在库里存的是 JSON 字符串，取出来先解析成 dict 给模板用。
    # 解析失败（比如历史脏数据）就当没诊断过，绝不让页面 500。
    analysis = None
    if record["ai_analysis"]:
        try:
            analysis = json.loads(record["ai_analysis"])
        except ValueError:
            analysis = None
        if not isinstance(analysis, dict):  # 万一存成了别的 JSON，也当没诊断过
            analysis = None

    return render_template(
        "record_detail.html",
        record=record,
        tags=tags,
        analysis=analysis,
        ai_ready=ai.is_configured(),
    )


@bp.route("/records/<int:record_id>/analyze", methods=["POST"])
def analyze_record(record_id):
    """点【AI 诊断】：调用大模型分析这道错题，结果存回库里再跳回详情页。

    为什么要存库？因为 API 要花钱、要等几秒。
    存下来以后每次打开详情页直接读，不再重复调模型。
    """
    record = query(
        "SELECT * FROM records WHERE id = ? AND user_id = ?",
        (record_id, session["user_id"]),
        one=True,
    )
    if record is None:
        abort(404)

    if not ai.is_configured():
        flash("还没有配置 AI 密钥，暂时用不了这个功能", "warning")
        return redirect(url_for("records.record_detail", record_id=record_id))

    result = ai.analyze_record(
        record["title"], record["content"], record["code"], record["reason"]
    )

    if result is None:
        # ai.py 里已经把异常吞掉了，这里只需要给用户一句人话
        flash("AI 分析失败了，过一会儿再试一次", "danger")
    else:
        execute(
            "UPDATE records SET ai_analysis = ? WHERE id = ? AND user_id = ?",
            (json.dumps(result, ensure_ascii=False), record_id, session["user_id"]),
        )
        flash("AI 诊断完成", "success")

    return redirect(url_for("records.record_detail", record_id=record_id))


# ---------------------------------------------------------------------------
# 下面是还没实现的部分。保持"能跑"，点进去会看到一张说明页。
# ---------------------------------------------------------------------------


@bp.route("/records/new", methods=["GET", "POST"])
def new_record():
    if request.method == "POST":
        title = request.form.get("title")
        # TODO:这里要做表单验证，title不能为空，难度要在1~5之间，tags要拆成列表
        content = request.form.get("content")
        code = request.form.get("code")
        reason = request.form.get("reason")
        difficulty = int(request.form.get("difficulty", 3))
        tags = request.form.get("tags")

        if not title:
            flash("标题不能为空", "danger")
            return redirect(url_for("records.new_record"))

        record_id = execute(
            """INSERT INTO records(user_id,title,content,code,reason,difficulty)
            VALUES(?,?,?,?,?,?)""",
            (session["user_id"], title, content, code, reason, difficulty),
        )

        # ③.5 处理标签
        tags_names = [t.strip() for t in (tags or "").split(",") if t.strip()]
        tags_names = list(set(tags_names))  # 去重，防止 DP,DP 撞主键

        for name in tags_names:
            row = query("SELECT id FROM tags WHERE name = ?", (name,), one=True)
            if row:
                tag_id = row["id"]  # 有，直接用
            else:
                tag_id = execute("INSERT INTO tags (name) VALUES (?)", (name,))
            execute(
                "INSERT INTO record_tags (record_id, tag_id) VALUES (?, ?)",
                (record_id, tag_id),
            )

        flash("保存成功")
        return redirect(url_for("records.list_records"))

    return render_template("record_form.html", record=None, tags_text="")


@bp.route("/records/<int:record_id>/edit", methods=["GET", "POST"])
def edit_record(record_id):
    record = query(
        "SELECT * FROM records WHERE id = ? AND user_id = ?",
        (record_id, session["user_id"]),
        one=True,
    )
    if record is None:
        abort(404)

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        code = request.form.get("code")
        reason = request.form.get("reason")
        difficulty = int(request.form.get("difficulty", 3))
        tags = request.form.get("tags")

        if not title:
            flash("标题不能为空", "danger")
            return redirect(url_for("records.edit_record", record_id=record_id))

        # 先把标签拆好（放在 DELETE 之前，万一出错也不会丢数据）
        tags_names = [t.strip() for t in (tags or "").split(",") if t.strip()]
        tags_names = list(set(tags_names))  # 去重，防止 DP,DP 撞主键

        # 改记录本身（SET 说的是"改哪些字段"，WHERE 说的是"改哪一行"）
        execute(
            """UPDATE records
               SET title = ?, content = ?, code = ?, reason = ?, difficulty = ?
               WHERE id = ? AND user_id = ?""",
            (title, content, code, reason, difficulty, record_id, session["user_id"]),
        )

        execute("DELETE FROM record_tags WHERE record_id = ?", (record_id,))
        for name in tags_names:
            row = query("SELECT id FROM tags WHERE name = ?", (name,), one=True)
            if row:
                tag_id = row["id"]  # 有，直接用
            else:
                tag_id = execute("INSERT INTO tags (name) VALUES (?)", (name,))
            execute(
                "INSERT INTO record_tags (record_id,tag_id)VALUES(?,?)",
                (record_id, tag_id),
            )

        flash("修改成功")
        return redirect(url_for("records.list_records"))

        # GET：把原来的标签拼成字符串，传给模板
    rows = query(
        """SELECT t.name FROM tags t
                    JOIN record_tags rt ON rt.tag_id = t.id
                    WHERE rt.record_id = ?""",
        (record_id,),
    )
    tags_text = ", ".join(r["name"] for r in rows)
    return render_template("record_form.html", record=record, tags_text=tags_text)


@bp.route("/records/<int:record_id>/delete", methods=["POST"])
def delete_record(record_id):
    record = query(
        "SELECT * FROM records WHERE id = ? AND user_id = ?",
        (record_id, session["user_id"]),
        one=True,
    )
    if record is None:
        abort(404)

    execute(
        "DELETE FROM records WHERE id = ? AND user_id = ?",
        (record_id, session["user_id"]),
    )

    flash("已删除")
    return redirect(url_for("records.list_records"))
