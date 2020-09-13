from functools import wraps
from django.conf import settings


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
