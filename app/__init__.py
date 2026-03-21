"""应用入口包。"""

from .api.app_factory import create_app
from .version import __version__

__all__ = ["__version__", "create_app"]
