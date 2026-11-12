"""pytest 的公共装置（fixture）。

作用：每个测试都在一个"全新的临时数据库"上跑，
互不影响，也不会碰你本地的 wrongbook.db。
"""

import sqlite3
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from config import Config

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def app(tmp_path):
    """建一个用临时数据库的 app。"""
    db_file = tmp_path / "test.db"

    conn = sqlite3.connect(db_file)
    conn.executescript((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))

    conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("demo", generate_password_hash("123456")),
    )
    conn.execute("INSERT INTO tags (name) VALUES ('DP')")

    # 属于 demo（user_id=1）的记录
    conn.execute(
        """INSERT INTO records (user_id, title, content, code, reason, difficulty)
           VALUES (1, '测试记录', '这是一道测试题', 'cout << 1;', '边界没考虑', 4)"""
    )
    conn.execute("INSERT INTO record_tags (record_id, tag_id) VALUES (1, 1)")

    # 另一个用户 + 一条属于他的记录，用来验证权限隔离
    # 注意：schema.sql 里打开了外键约束，所以必须先有 user 99 才能插他的记录
    conn.execute(
        "INSERT INTO users (id, username, password_hash) VALUES (99, 'other', ?)",
        (generate_password_hash("123456"),),
    )
    conn.execute(
        "INSERT INTO records (user_id, title, difficulty) VALUES (99, '别人的记录', 3)"
    )
    conn.commit()
    conn.close()

    class TestConfig(Config):
        TESTING = True
        DEBUG = False
        SECRET_KEY = "test-secret"
        DATABASE = str(db_file)

    application = create_app(TestConfig)
    yield application


@pytest.fixture
def client(app):
    """模拟"已登录"的浏览器（demo 用户，id=1）。

    session_transaction() 让我们能直接改 session，
    相当于跳过了"输入密码点登录"这一步。
    """
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "demo"
    return c


@pytest.fixture
def anon_client(app):
    """模拟"没登录"的浏览器，专门用来测守卫。"""
    return app.test_client()
