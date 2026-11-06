"""注册 / 登录 / 登出。

现在全是占位页。这里是对应的学习顺序：
    D10: 注册（密码哈希）、登录（校验 + 写 session）、登出（清 session）
    D11: 把 records.py 里的 DEMO_USER_ID 换成 session 里的真实用户
"""
from flask import Blueprint, render_template

bp = Blueprint("auth", __name__)


@bp.route("/register")
def register():
    return render_template(
        "placeholder.html",
        title="注册",
        steps=[
            "GET 显示表单；POST 读 username / password",
            "校验：用户名非空、长度合理；两次密码一致",
            "查重：SELECT id FROM users WHERE username = ?，有就提示'用户名已被占用'",
            "存密码：generate_password_hash(password)，绝不能存明文",
            "INSERT INTO users 后 redirect 到登录页",
        ],
    )


@bp.route("/login")
def login():
    return render_template(
        "placeholder.html",
        title="登录",
        steps=[
            "POST 时按用户名查用户，查不到统一提示'用户名或密码错误'",
            "用 check_password_hash(user['password_hash'], password) 校验",
            "成功后 session['user_id'] = user['id']，再 redirect 到列表页",
            "登出：session.clear()",
            "SECRET_KEY 必须已配置，否则 session 用不了",
        ],
    )


@bp.route("/logout")
def logout():
    return render_template(
        "placeholder.html",
        title="登出",
        steps=[
            "session.clear()",
            "redirect 到登录页",
            "顺手加一个 before_request：未登录访问 /records 时跳登录页",
        ],
    )
