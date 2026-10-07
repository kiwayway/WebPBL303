from functools import wraps

from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_smorest import abort

from .extensions import db
from .models import User


def role_required(*roles):
    """Contoh: @role_required("admin") atau @role_required("seller", "admin")"""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = db.session.get(User, int(get_jwt_identity()))
            if user is None or not user.is_active:
                abort(401, message="Sesi tidak valid")
            if user.role.value not in roles:
                abort(403, message="Akses ditolak")
            return fn(*args, **kwargs)

        return wrapper

    return decorator