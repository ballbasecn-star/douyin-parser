"""CLI 主入口。"""

import sys

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - 可选依赖
    load_dotenv = None

from app.cli.cookie_commands import handle_cookie_command
from app.cli.parse_commands import handle_parse_command


def load_env_if_available():
    """按需加载 .env。"""
    if load_dotenv is not None:
        load_dotenv()


def main(argv: list[str] | None = None) -> int:
    """CLI 主入口。"""
    load_env_if_available()
    args = list(sys.argv[1:] if argv is None else argv)

    if not args:
        return handle_parse_command([])
    if args[0] == "cookie":
        return handle_cookie_command(args[1:])
    return handle_parse_command(args)
