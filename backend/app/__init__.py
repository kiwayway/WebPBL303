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
    @jwt.unauthorized_loader
    @jwt.invalid_token_loader
    def _unauthorized(reason):
        return {"message": "Belum login atau sesi tidak valid"}, 401

    @jwt.expired_token_loader
    def _expired(header, payload):
        return {"message": "Sesi sudah habis, silakan login lagi"}, 401
    limiter.init_app(app)
    
    from flask_cors import CORS
    CORS(
        app,
        origins=app.config["CORS_ORIGINS"],
        supports_credentials=True,
        allow_headers=["Content-Type", "X-CSRF-TOKEN"],
    )

    from . import models  # noqa: F401  (supaya tabel terdeteksi migrasi)
    from .cli import register_cli

    register_cli(app)

    api = Api(app)
    api.register_blueprint(health_bp)
    from .auth import auth_bp
    api.register_blueprint(auth_bp)
    return app