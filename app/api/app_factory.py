"""Flask app 工厂。"""

from flask import Flask

from app.infra.db import init_database
from app.infra.settings import STATIC_DIR, TEMPLATE_DIR


def create_app() -> Flask:
    init_database()
    app = Flask(
        __name__,
        template_folder=str(TEMPLATE_DIR),
        static_folder=str(STATIC_DIR),
    )

    from .routes import api_blueprint

    app.register_blueprint(api_blueprint)
    return app
