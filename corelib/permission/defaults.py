from collections import OrderedDict
from django.conf import settings


# default permission groups.
_PERMISSION_GROUPS = OrderedDict({
    "guest": 0,
    "normal": 1,
    "admin": 2,
})


# Vars that really works.
PERMISSION_GROUPS = getattr(settings, 'PERMISSION_GROUPS', _PERMISSION_GROUPS)
