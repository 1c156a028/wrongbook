"""数据库访问层。

所有 SQL 都集中在这里调用，路由里不直接写 sqlite3。
好处：改数据库、加连接池、加日志，只需要动这一个文件。

两条铁律（写进注释里，因为特别容易忘）：
1. 永远用 ? 占位传参，绝不把用户输入拼进 SQL 字符串（否则会被 SQL 注入）。
2. 用完的连接要关，这里用 Flask 的 teardown 机制统一收尾。
"""
import sqlite3

from flask import current_app, g


def get_db():
    """获取当前请求的数据库连接（同一个请求内复用同一个连接）。"""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        # row_factory 让查询结果可以像字典一样用 row["title"] 取值
        g.db.row_factory = sqlite3.Row
        # SQLite 默认不检查外键，必须手动打开，否则级联删除不生效
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(exception=None):
    """请求结束时关闭连接。由 app.teardown_appcontext 自动调用。"""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, args=(), one=False):
    """执行 SELECT，返回行列表；one=True 时只返回第一行或 None。"""
    cursor = get_db().execute(sql, args)
    rows = cursor.fetchall()
    cursor.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, args=()):
    """执行 INSERT/UPDATE/DELETE，返回新插入行的 id。"""
    db = get_db()
    cursor = db.execute(sql, args)
    db.commit()
    return cursor.lastrowid


def init_app(app):
    """把 close_db 挂到 Flask 的生命周期上。"""
    app.teardown_appcontext(close_db)
