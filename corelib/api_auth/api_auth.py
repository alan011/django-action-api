from django.conf import settings
from .defaults import ACTION_STATIC_TOKENS
import re


class APIAuth(object):
    def auth_by_token(self, auth_token):
        # To check configuration for token_manager.
        if 'corelib.token_manager' not in settings.INSTALLED_APPS:
            # If `token_manager` is not used, user can use STATIC_TOKEN to simply authenticating API requests.
            if auth_token in ACTION_STATIC_TOKENS:
                return True
            return False
        # Plugably import.
        from corelib.token_manager.models import AuthToken
        from datetime import datetime, timedelta

        # To do token authentication.
        if re.search(r'^\w+\.\w+$', auth_token):
            username = auth_token.split('.')[0]
            token = auth_token.split('.')[1]
            queryset = AuthToken.objects.filter(username=username, token=token)
            if queryset.exists():
                obj = queryset.get(username=username, token=token)
                if obj.expired_time == 0:
                    return True
                if obj.sign_date + timedelta(seconds=obj.expired_time) > datetime.now():
                    return True
        return False

    def auth_by_session(self, user_obj):
        if user_obj.is_authenticated:
            return True
        return False
