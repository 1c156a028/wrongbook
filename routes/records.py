"""错题相关页面。

已完成：列表页、详情页（这是"读"的完整链路，先看懂这两条再动手写"写"）
待实现：新增、编辑、删除
"""
from flask import Blueprint, abort, render_template,request,flash,redirect,url_for

from db import query,execute

bp = Blueprint("records", __name__)

# 临时写死：登录功能做完后，这里要改成从 session 里取当前用户
# TODO(D10~D11): 换成 session["user_id"]，并在取不到时跳转登录页
DEMO_USER_ID = 1

# 列表页要查的 SQL。拆出来单独放，方便你在 sqlite 工具里直接试
LIST_SQL = """
    SELECT r.id, r.title, r.difficulty, r.created_at,
           GROUP_CONCAT(t.name, ' / ') AS tag_names
    FROM records r
    LEFT JOIN record_tags rt ON rt.record_id = r.id
    LEFT JOIN tags t        ON t.id = rt.tag_id
    WHERE r.user_id = ?
    GROUP BY r.id
    ORDER BY r.created_at DESC, r.id DESC
"""


@bp.route("/records")
def list_records():
    """错题列表：查出当前用户的所有记录，交给模板渲染。"""
    records = query(LIST_SQL, (DEMO_USER_ID,))
    return render_template("record_list.html", records=records)


@bp.route("/records/<int:record_id>")
def record_detail(record_id):
    """详情页。

    注意 WHERE 里的 user_id = ?——这一句就是"权限隔离"。
    少了它，别人把 URL 里的 id 一改就能看到你的记录。
    """
    record = query(
        "SELECT * FROM records WHERE id = ? AND user_id = ?",
        (record_id, DEMO_USER_ID),
        one=True,
    )
    if record is None:
        abort(404)          # 不存在或不属于你，统一返回 404，不泄露"存在但无权"

    tags = query(
        """SELECT t.name
           FROM tags t
           JOIN record_tags rt ON rt.tag_id = t.id
           WHERE rt.record_id = ?
           ORDER BY t.name""",
        (record_id,),
    )
    return render_template("record_detail.html", record=record, tags=tags)


# ---------------------------------------------------------------------------
# 下面是还没实现的部分。保持"能跑"，点进去会看到一张说明页。
# ---------------------------------------------------------------------------

@bp.route("/records/new",methods=["GET","POST"])
def new_record():
    if request.method == "POST":
        title = request.form.get("title")
        #TODO:这里要做表单验证，title不能为空，难度要在1~5之间，tags要拆成列表
        content = request.form.get("content")
        code = request.form.get("code")
        reason = request.form.get("reason")
        difficulty = int(request.form.get("difficulty",3))
        tags = request.form.get("tags")
        
        if not title:
            flash("标题不能为空","danger")
            return redirect(url_for("records.new_record"))
        
                    # ③ 写库：只留一次，把新记录的 id 接住
        record_id = execute(
            """INSERT INTO records(user_id,title,content,code,reason,difficulty)
            VALUES(?,?,?,?,?,?)""",
            (DEMO_USER_ID,title,content,code,reason,difficulty)
        )

        # ③.5 处理标签
        tags_names = [t.strip() for t in (tags or "").split(",") if t.strip()]
        tags_names = list(set(tags_names))          # 去重，防止 DP,DP 撞主键

        for name in tags_names:
            row = query("SELECT id FROM tags WHERE name = ?", (name,), one=True)
            if row:
                tag_id = row["id"]                  # 有，直接用
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
    record = query("SELECT * FROM records WHERE id = ? AND user_id = ?",
                   (record_id,DEMO_USER_ID), one =True)
    if record is None:
        abort(404)

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        code = request.form.get("code")
        reason = request.form.get("reason")
        difficulty = int(request.form.get("difficulty",3))
        tags = request.form.get("tags")

        if not title:
            flash("标题不能为空","danger")
            return redirect(url_for("records.edit_record",record_id=record_id))
        
        # 先把标签拆好（放在 DELETE 之前，万一出错也不会丢数据）
        tags_names = [t.strip() for t in (tags or "").split(",") if t.strip()]
        tags_names = list(set(tags_names))         # 去重，防止 DP,DP 撞主键

        # 改记录本身（SET 说的是"改哪些字段"，WHERE 说的是"改哪一行"）
        execute(
            """UPDATE records
               SET title = ?, content = ?, code = ?, reason = ?, difficulty = ?
               WHERE id = ? AND user_id = ?""",
            (title, content, code, reason, difficulty, record_id, DEMO_USER_ID)
        )
       
        execute("DELETE FROM record_tags WHERE record_id = ?",(record_id,))
        for name in tags_names:
            row = query("SELECT id FROM tags WHERE name = ?", (name,), one=True)
            if row:
                tag_id = row["id"]                  # 有，直接用
            else:
                tag_id = execute("INSERT INTO tags (name) VALUES (?)", (name,))
            execute(
                "INSERT INTO record_tags (record_id,tag_id)VALUES(?,?)",
                (record_id,tag_id)
            )

        flash("修改成功")
        return redirect(url_for("records.list_records"))

        # GET：把原来的标签拼成字符串，传给模板
    rows = query("""SELECT t.name FROM tags t
                    JOIN record_tags rt ON rt.tag_id = t.id
                    WHERE rt.record_id = ?""", (record_id,))
    tags_text = ", ".join(r["name"] for r in rows)
    return render_template("record_form.html", record=record, tags_text=tags_text)


@bp.route("/records/<int:record_id>/delete", methods=["POST"])
def delete_record(record_id):
    return render_template(
        "placeholder.html",
        title="删除错题",
        steps=[
            "只接受 POST（这里 methods 已经限定了），不要用 <a> 链接删",
            "DELETE FROM records WHERE id = ? AND user_id = ?",
            "record_tags 靠外键 ON DELETE CASCADE 自动清理",
            "删除后 flash + redirect 回列表",
        ],
    )
