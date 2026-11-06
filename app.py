"""应用入口。

用"工厂函数"的写法（create_app）而不是直接把 app 建在模块顶层，
好处是测试时可以传入不同的配置，造一个独立的测试用 app。
这是 Flask 官方推荐的写法，也是你后面看别人项目时最常见的结构。
"""
from flask import Flask, redirect, render_template, url_for

import db as database
from config import Config


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    # 数据库连接的创建与关闭交给 db.py 统一管理
    database.init_app(app)

    # 注册各功能模块（Flask 里叫"蓝图 blueprint"，可以理解成按功能拆出来的子应用）
    from routes.auth import bp as auth_bp
    from routes.records import bp as records_bp
    from routes.stats import bp as stats_bp

    app.register_blueprint(records_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(stats_bp)

    @app.route("/")
    def index():
        """首页暂时直接跳到错题列表。"""
        return redirect(url_for("records.list_records"))

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500

    return app


# 供 `python app.py` 和部署时 `gunicorn app:app` 使用
app = create_app()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",      # 只监听本机；部署时由平台/容器负责对外
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
    )
