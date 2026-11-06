"""项目配置。

原则：所有可能随环境变化的值（密钥、数据库路径、调试开关）都从这里读，
不要硬编码在代码里。这样本地和线上可以用同一份代码、不同的配置。
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# BASE_DIR 指向项目根目录。用 __file__ 推算绝对路径，
# 避免"换个工作目录启动就找不到数据库"这个经典坑。
BASE_DIR = Path(__file__).resolve().parent

# 自动读取项目根目录下的 .env 文件（不存在也不报错）
load_dotenv(BASE_DIR / ".env")


class Config:
    # 会话/表单保护用的密钥。线上必须由环境变量提供，绝不能用默认值。
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

    # 数据库文件位置。相对路径统一按项目根目录解析成绝对路径。
    _db_raw = os.environ.get("DATABASE_PATH", "wrongbook.db")
    DATABASE = str(BASE_DIR / _db_raw) if not os.path.isabs(_db_raw) else _db_raw

    # 调试开关：1 开 0 关。上线必须为 0，否则报错页面会泄露源码。
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

    # 启动端口
    PORT = int(os.environ.get("PORT", "5000"))
