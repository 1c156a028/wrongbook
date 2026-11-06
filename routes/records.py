"""错题相关页面。

已完成：列表页、详情页（这是"读"的完整链路，先看懂这两条再动手写"写"）
待实现：新增、编辑、删除
"""
from flask import Blueprint, abort, render_template

from db import query

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

@bp.route("/records/new")
def new_record():
    return render_template(
        "placeholder.html",
        title="新增错题",
        steps=[
            "GET 时显示表单：用 record_form.html，mode='create'",
            "POST 时读 request.form 里的字段",
            "校验：title 不能为空，difficulty 必须是 1~5",
            "INSERT INTO records (...) 后拿到 lastrowid",
            "处理标签：按名字查 tags，没有就插入，再写 record_tags",
            "flash 一句提示，redirect 回列表页（PRG 模式，防止刷新重复提交）",
        ],
    )


@bp.route("/records/<int:record_id>/edit")
def edit_record(record_id):
    return render_template(
        "placeholder.html",
        title="编辑错题",
        steps=[
            "先按 id + user_id 查出记录，查不到就 abort(404)",
            "GET 时把记录填进表单（value 用 record['title'] 等）",
            "POST 时 UPDATE records SET ... WHERE id = ? AND user_id = ?",
            "别忘了 WHERE 里也要带 user_id，否则能改别人的数据",
        ],
    )


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
