from functools import wraps

from flask import abort
from flask_login import current_user

from .models import Permission


def permission_required(permission):
    """If you decorate view with this, it will ensure that the current user 
    has specified permission.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """If you decorate view with this, it will ensure that the current user 
    has administrator permission.
    """
    return permission_required(Permission.ADMIN)(f)
