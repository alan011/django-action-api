from collections import OrderedDict
from django.conf import settings


# default permission groups.
_PERMISSION_GROUPS = OrderedDict({
    "normal": 1,
    "admin": 2,
})

# This user and perm will be used for developing, when `ACTION_AUTH_REQUIRED` is set to 'False'.
_DEFAULT_USER_WHEN_AUTH_NOT_REQUIRED = 'superdeveloper'
_DEFAULT_PERM_WHEN_AUTH_NOT_REQUIRED = 'admin'
_DEFAULT_USER_PASSWORD = 'qwer!1234'

# Tuple: (<module_path>, <model_class_name>)
_CUSTOM_PERMISSION_MODEL = None

# Vars that really works.
PERMISSION_GROUPS = getattr(settings, 'PERMISSION_GROUPS', _PERMISSION_GROUPS)
CUSTOM_PERMISSION_MODEL = getattr(settings, 'CUSTOM_PERMISSION_MODEL', _CUSTOM_PERMISSION_MODEL)
DEFAULT_USER_WHEN_AUTH_NOT_REQUIRED = getattr(settings, 'DEFAULT_USER_WHEN_AUTH_NOT_REQUIRED', _DEFAULT_USER_WHEN_AUTH_NOT_REQUIRED)
DEFAULT_PERM_WHEN_AUTH_NOT_REQUIRED = getattr(settings, 'DEFAULT_PERM_WHEN_AUTH_NOT_REQUIRED', _DEFAULT_PERM_WHEN_AUTH_NOT_REQUIRED)
DEFAULT_USER_PASSWORD = getattr(settings, 'DEFAULT_USER_PASSWORD', _DEFAULT_USER_PASSWORD)
