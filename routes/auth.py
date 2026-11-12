"""注册 / 登录 / 登出。"""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute, query

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # 1) 从表单里取出用户填的两个值；.strip() 去掉首尾空格
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        # 2) 校验：不能为空
        if not username or not password:
            flash("用户名和密码都不能为空")
            return redirect(url_for("auth.register"))

        # 3) 校验：密码太短不让注册
        if len(password) < 6:
            flash("密码至少 6 位")
            return redirect(url_for("auth.register"))

        # 4) 查重：这个用户名被别人占了吗
        exists = query("SELECT id FROM users WHERE username = ?", (username,), one=True)
        if exists:
            flash("这个用户名已经被注册了")
            return redirect(url_for("auth.register"))

        # 5) 存进数据库：密码先变成哈希，绝不存原文
        execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )

        # 6) 注册成功，跳去登录页
        flash("注册成功，请登录")
        return redirect(url_for("auth.login"))

    # 不是 POST（也就是 GET）：显示一张空表单
    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # 按用户名找这个人；找不到就是 None
        user = query("SELECT * FROM users WHERE username = ?", (username,), one=True)

        # 用户不存在 / 密码不对，都提示同一句话：
        # 不告诉对方"到底是哪个错了"，避免帮别人试探出哪些用户名存在
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("用户名或密码错误")
            return redirect(url_for("auth.login"))

        # 核对通过：在 session 里记下"你是谁"
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        flash(f"欢迎回来，{user['username']}")
        return redirect(url_for("records.list_records"))

    return render_template("login.html")


@bp.route("/logout")
def logout():
    # 清空 session：手环作废
    session.clear()
    flash("已退出登录")
    return redirect(url_for("auth.login"))
