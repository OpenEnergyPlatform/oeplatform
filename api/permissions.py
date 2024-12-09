import login.models as login_models
from api import actions


def permission_wrapper(permission, f):
    def wrapper(caller, request, *args, **kwargs):
        schema = kwargs.get("schema", actions.DEFAULT_SCHEMA)
        table = kwargs.get("table") or kwargs.get("sequence")
        actions.assert_permission(request.user, table, permission, schema=schema)
        return f(caller, request, *args, **kwargs)

    return wrapper


def require_read_permission(f):
    return permission_wrapper(login_models.READ_PERM, f)


def require_write_permission(f):
    return permission_wrapper(login_models.WRITE_PERM, f)


def require_delete_permission(f):
    return permission_wrapper(login_models.DELETE_PERM, f)


def require_admin_permission(f):
    return permission_wrapper(login_models.ADMIN_PERM, f)
