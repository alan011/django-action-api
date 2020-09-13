from django.conf import settings


# Defaults.
_DEFAULT_PAGE_LENGTH = 10


# By pass API authentication settings.
DEFAULT_PAGE_LENGTH = getattr(settings, 'DEFAULT_PAGE_LENGTH', _DEFAULT_PAGE_LENGTH)
