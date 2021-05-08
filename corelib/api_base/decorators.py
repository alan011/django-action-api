from functools import wraps
from django.conf import settings
from .api_field_types import BoolType, IntType


def _dataValidate(self, req, opt):
    """
    Not a decorator.
    Used in decorator `dataValidator`.
    """
    if self.set_parameters_directly:
        return True

    _fd = self.post_fields
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

            # Default pagination
            if getattr(self, 'do_pagination', False):
                if self.post_fields.get('page_index', None) is None:
                    self.post_fields['page_index'] = IntType(min=1)
                if self.post_fields.get('page_length', None) is None:
                    self.post_fields['page_length'] = IntType(min=1)
                if 'page_index' not in optional and 'page_index' not in required:
                    optional.append['page_index']
                if 'page_length' not in optional and 'page_length' not in required:
                    optional.append['page_length']

            if not _dataValidate(self, required, optional):
                return None
            func_result = func(self, *args, **kwargs)
            return func_result
        return validate
    return decorator


def pre_handler(req=None, opt=None, private=False, perm=None, record=False, record_label=None):
    """
    Can only be used for API action handlers.
    To integrate other decorators together, with `permissionChecker` and `recorder` pluggable by django settings.
    Params:
        req             Pass to decorator `dataValidator`.
        opt             Pass to decorator `dataValidator`.
        private         If 'True', authenticating by auth_token is not allowed for this action.
        perm            Pass to decorator `permissionChecker`. If None, Means do not check user's permission for this handler.
        record          Only useful when django app 'corelib.recorder' is installed. If True, handler calling will be recorded.
        record_label    A readable name for action to record.
    """
    def decorator(func):
        func = dataValidator(req, opt)(func)
        if 'corelib.recorder' in settings.INSTALLED_APPS and record:
            from corelib.recorder.decorators import recorder
            func = recorder(record_label)(func)
        if 'corelib.permission' in settings.INSTALLED_APPS and perm is not None:
            from corelib.permission.decorators import permissionChecker
            func = permissionChecker(perm)(func)

        func._is_private = private
        return func
    return decorator
