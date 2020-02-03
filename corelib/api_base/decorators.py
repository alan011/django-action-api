from functools import wraps
from django.conf import settings
from corelib import config
from .api_field_types import BoolType


def _dataValidate(self, req, opt):
    """
    Not a decorator.
    Used in decorator `dataValidator`.
    """
    if self.set_parameters_directly:
        return True

    _fd = self.fields_defination
    # To check `req` fields first.
    for field in req:
        if field not in self.params:
            return self.error(f"ERROR: Field '{field}' is required.", return_value=False)

    # To set BoolType field in `opt` with default value.
    self.checked_params = {f: _fd[f].default for f in filter(lambda f: isinstance(_fd[f], BoolType), opt)}

    # To check value of all fields. Note: field not in `req` + `opt` will be dropped directly.
    for field in filter(lambda f: f in self.params, req + opt):
        field_type = _fd[field]
        checked_value, err = field_type.check(self.params[field])
        if err is not None:
            return self.error(err, return_value=False)
        self.checked_params[field] = checked_value
    return True


def dataValidator(req=None, opt=None):
    """
    Can only be used for API action handlers.
    This decorator is used to validate 'self.params' for handlers.
    If no error, self.check_parameters will set with meaningful values.
    Params:
        req: A list, which contains field names must be provided.
        opt: A list, which contains field names can be provided optionally.
    """
    def decorator(func):
        @wraps(func)
        def validate(self, *args, **kwargs):
            required = req if req is not None else []
            optional = opt if opt is not None else []
            if not _dataValidate(self, required, optional):
                return None
            func_result = func(self, *args, **kwargs)
            return func_result
        return validate
    return decorator


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
            if config.PERMISSION_GROUPS[user_perm] < config.PERMISSION_GROUPS[perm]:
                return self.error("ERROR: Not allowed to call this API with action '{self.action}'!", http_status=403)
            func_result = func(self, *args, **kwargs)
            return func_result
        return checker
    return decorator


def recorder():
    """
    Can only be used for API action handlers.
    This decorator is used to record api callings that need to be record. users permission.
    This decorator needs 'corelib.recorder' to be installed as a django app.
    """
    def decorator(func):
        @wraps(func)
        def recording(self, *args, **kwargs):
            if "corelib.recorder" not in settings.INSTALLED_APPS:
                return self.error("ERROR: Action API's 'recorder' is not set into django's INSTALLED_APPS.", http_status=500)
            from corelib.recorder.models import APICallingRecord
            # To record this call.
            record_data = {
                "username": "[AUTH_TOKEN]" + self.auth_token.split('.')[0] if self.auth_token else self.request.user.username,
                "api": self.request.path,
                "action": self.action,
                "post_data": self.params
            }
            record = APICallingRecord.objects.create(**record_data)

            # To do the real work.
            func_result = func(self, *args, **kwargs)

            # To record result of this call after doing real work.
            record.result = "SUCCESS" if self.result else "FAILED"
            record.message = self.message
            record.error_message = self.error_message
            record.save()

            return func_result
        return recording
    return decorator


def pre_handler(req=None, opt=None, perm=None, record=False):
    """
    Can only be used for API action handlers.
    To integrate other decorators together, with `permissionChecker` and `recorder` pluggable by django settings.
    Params:
        req: pass to decorator `dataValidator`.
        opt: pass to decorator `dataValidator`.
        perm: pass to decorator `permissionChecker`. If None, Means do not check user's permission for this handler.
        record: Only useful when django app 'corelib.recorder' is installed. If True, handler calling will be recorded.
    """
    def decorator(func):
        func = dataValidator(req, opt)(func)
        if 'corelib.recorder' in settings.INSTALLED_APPS and record:
            func = recorder()(func)
        if 'corelib.permission' in settings.INSTALLED_APPS and perm is not None:
            func = permissionChecker(perm)(func)
        return func
    return decorator
