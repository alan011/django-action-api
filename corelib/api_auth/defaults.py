from django.conf import settings


# Defaults.
_ACTION_STATIC_TOKENS = []  # Static tokens are never expired.


# Var that really works.
ACTION_STATIC_TOKENS = getattr(settings, 'ACTION_STATIC_TOKENS', _ACTION_STATIC_TOKENS)
