"""应用级配置与路径定义。"""

from pathlib import Path

from douyin import __version__

APP_VERSION = __version__
DEFAULT_AI_MODEL = "Pro/deepseek-ai/DeepSeek-V3.2"

BASE_DIR = Path(__file__).resolve().parents[2]
WEB_DIR = BASE_DIR / "web"
TEMPLATE_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"
