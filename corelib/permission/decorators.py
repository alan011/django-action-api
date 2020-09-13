from functools import wraps
from django.conf import settings
from corelib.permission.defaults import PERMISSION_GROUPS


def permissionChecker(perm):
    """
    Can only be used for API action handlers.
    This decorator is used to check wether user has permission to visit this API or not.
    This decorator needs 'corelib.permission' to be installed as a django app.
    """
    def decorator(func):
        @wraps(func)
        def checker(self, *args, **kwargs):
            if "corelib.permission" not in settings.INSTALLED_APPS:
                return self.error("ERROR: Action API's 'permission' is not set into django's INSTALLED_APPS.", http_status=500)
            # To check user's permission.
            user_perm = self.request.user.api_perm.perm_group
            if PERMISSION_GROUPS[user_perm] < PERMISSION_GROUPS[perm]:
                return self.error("ERROR: Not allowed to call this API with action '{self.action}'!", http_status=403)
            func_result = func(self, *args, **kwargs)
            return func_result
        return checker
    return decorator
