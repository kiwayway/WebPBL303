from argon2.exceptions import VerifyMismatchError
from flask import jsonify
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError

from .extensions import db, limiter
from .models import Role, User, ph
from .schemas import LoginSchema, RegisterSchema, UserSchema

auth_bp = Blueprint(
    "auth", __name__, url_prefix="/api/v1/auth", description="Login dan sesi"
)

# Hash palsu supaya waktu respons sama, baik email ada maupun tidak
_DUMMY_HASH = ph.hash("dummy-password")


def _fake_verify(password):
    try:
        ph.verify(_DUMMY_HASH, password)
    except VerifyMismatchError:
        pass


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("10 per hour")
@auth_bp.arguments(RegisterSchema)
@auth_bp.response(201, UserSchema)
def register(data):
    """Daftar akun baru (customer atau seller)"""
    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        abort(409, message="Email sudah terdaftar")

    user = User(email=email, name=data["name"].strip(), role=Role(data["role"]))
    user.set_password(data["password"])
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:  # dua request bersamaan dengan email sama
        db.session.rollback()
        abort(409, message="Email sudah terdaftar")
    return user


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
@auth_bp.arguments(LoginSchema)
@auth_bp.response(200, UserSchema)
def login(data):
    """Login: token disimpan di cookie HttpOnly"""
    email = data["email"].strip().lower()
    user = User.query.filter_by(email=email).first()

    if user is None:
        _fake_verify(data["password"])
        abort(401, message="Email atau password salah")
    if not user.check_password(data["password"]) or not user.is_active:
        abort(401, message="Email atau password salah")

    token = create_access_token(
        identity=str(user.id), additional_claims={"role": user.role.value}
    )
    resp = jsonify(UserSchema().dump(user))
    set_access_cookies(resp, token)
    return resp


@auth_bp.route("/logout", methods=["POST"])
@auth_bp.response(200)
def logout():
    """Logout: hapus cookie token"""
    resp = jsonify({"message": "Berhasil logout"})
    unset_jwt_cookies(resp)
    return resp


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
@auth_bp.response(200, UserSchema)
def me():
    """Data user yang sedang login"""
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None or not user.is_active:
        abort(401, message="Sesi tidak valid")
    return user