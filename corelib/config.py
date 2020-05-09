from collections import OrderedDict

# By pass API authentication settings.
AUTH_REQUIRED = False  # A global authencating switch. Set it to False for developing.
NO_AUTH_ACTIONS = ['login']  # Even though `AUTH_REQUIRED` is True, actions in this list can be by pass API authentication.

# permission settings.
PERMISSION_GROUPS = OrderedDict({
    "guest": 0,
    "normal": 1,
    "admin": 2,
})

# list data pagination.
DEFAULT_PAGE_LENGTH = 10
