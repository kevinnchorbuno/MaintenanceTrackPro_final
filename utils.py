from flask import abort
from flask_login import current_user
from functools import wraps

# utils.py
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def role_required(roles):
    """
    Decorator to restrict route access based on user role.
    :param roles: A string (single role) or list (multiple roles) allowed to access the route.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)  # Forbidden if not logged in
            if isinstance(roles, str) and current_user.role != roles:
                abort(403)  # Forbidden if role doesn't match single role
            elif isinstance(roles, list) and current_user.role not in roles:
                abort(403)  # Forbidden if role not in allowed list
            return func(*args, **kwargs)
        return wrapper
    return decorator