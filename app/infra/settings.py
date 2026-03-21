"""应用级配置与路径定义。"""

import os
from pathlib import Path

from app.version import __version__

APP_VERSION = __version__
DEFAULT_AI_MODEL = "Pro/deepseek-ai/DeepSeek-V3.2"

BASE_DIR = Path(__file__).resolve().parents[2]
WEB_DIR = BASE_DIR / "web"
TEMPLATE_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"
COOKIE_DIR = Path(os.environ.get("COOKIE_DIR", str(BASE_DIR / "cookie_data")))
COOKIE_FILE = COOKIE_DIR / "douyin_cookie.json"
DATA_DIR = BASE_DIR / "data"


def get_database_url() -> str:
    """返回当前数据库连接串。

    当前团队约定 dev/prod 主业务数据库都应使用 PostgreSQL。
    这里保留 SQLite 回退，仅用于测试或临时无配置启动。
    """
    default_path = DATA_DIR / "app_dev.sqlite3"
    return os.environ.get("DATABASE_URL", f"sqlite:///{default_path}")
