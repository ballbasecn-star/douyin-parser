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
