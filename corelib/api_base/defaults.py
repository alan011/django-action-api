from django.conf import settings


# Defaults.
_ACTION_AUTH_REQUIRED = False  # A global authencating switch. Set it to False for developing.
_ACTIONS_AUTH_BY_PASS = ['login']  # Even though `AUTH_REQUIRED` is True, actions in this list can be by pass API authentication.


# By pass API authentication settings.
ACTION_AUTH_REQUIRED = getattr(settings, 'ACTION_AUTH_REQUIRED', _ACTION_AUTH_REQUIRED)
ACTIONS_AUTH_BY_PASS = getattr(settings, 'ACTIONS_AUTH_BY_PASS', _ACTIONS_AUTH_BY_PASS)
