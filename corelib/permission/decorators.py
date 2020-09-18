from functools import wraps
from .defaults import (
    PERMISSION_GROUPS, CUSTOM_PERMISSION_MODEL, DEFAULT_USER_WHEN_AUTH_NOT_REQUIRED,
    DEFAULT_PERM_WHEN_AUTH_NOT_REQUIRED, DEFAULT_USER_PASSWORD)
from .tools import get_model

from corelib.api_base.defaults import ACTION_AUTH_REQUIRED
from django.contrib.auth.models import User


def permissionChecker(perm=None):
    """
    Can only be used for API action handlers.
    This decorator is used to check whether user has permission to visit this API or not.
    This decorator needs 'corelib.permission' to be installed as a django app.

    Params:
        perm    A string define in `PERMISSION_GROUPS` setting.
    """
    def decorator(func):
        @wraps(func)
        def checker(self, *args, **kwargs):
            if perm is not None:
                # To get permission model.
                model = get_model()
                if not model:
                    return self.error(f"ERROR: `CUSTOM_PERMISSION_MODEL` setting '{CUSTOM_PERMISSION_MODEL}' is not valid.", http_status=500)

                error_msg = f"ERROR: You are not allowed to call this action API '{self.action}'!"

                # To get user perm object.
                if not ACTION_AUTH_REQUIRED and self.request.user.is_anonymous:
                    # For developing mode.
                    user_defaults = {
                        'email': 'fake@example.lei',
                        'password': DEFAULT_USER_PASSWORD,
                    }
                    user, _ = User.objects.get_or_create(username=DEFAULT_USER_WHEN_AUTH_NOT_REQUIRED, defaults=user_defaults)
                    perm_defaults = {
                        'perm_group': DEFAULT_PERM_WHEN_AUTH_NOT_REQUIRED,
                    }
                    user_perm, _ = model.objects.get_or_create(user=user, defaults=perm_defaults)
                else:
                    # Online mode.
                    user_perm = model.objects.filter(user=self.request.user).first()
                if user_perm is None:
                    return self.error(f"{error_msg} User_perm: None!", http_status=403)

                # To check user's permission
                self.user_perm = user_perm
                if PERMISSION_GROUPS[user_perm.perm_group] < PERMISSION_GROUPS[perm]:
                    return self.error(error_msg, http_status=403)

            # To do action.
            func_result = func(self, *args, **kwargs)
            return func_result
        return checker
    return decorator
