from flask import Flask
from flask_smorest import Api, Blueprint

from .extensions import db, jwt, limiter, migrate

health_bp = Blueprint("health", __name__, url_prefix="/api/v1", description="Cek status server")


@health_bp.route("/health")
def health():
    """Cek apakah API berjalan"""
    return {"status": "ok"}


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    from . import models  # noqa: F401  (supaya tabel terdeteksi migrasi)
    from .cli import register_cli

    register_cli(app)

    api = Api(app)
    api.register_blueprint(health_bp)
    return app