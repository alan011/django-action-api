from functools import wraps
from django.utils import timezone


def recorder(record_label=None):
    """
    Can only be used for API action handlers.
    This decorator is used to record api callings that need to be record. users permission.
    This decorator needs 'corelib.recorder' to be installed as a django app.
    """
    def decorator(func):
        @wraps(func)
        def recording(self, *args, **kwargs):
            from corelib.recorder.models import APICallingRecord
            # To record this call.
            username = ''
            if self.auth_token:
                token_user = self.auth_token.split('.')[0]
                username = f"[TOKEN_USER]{token_user}"
            elif self.request and not self.request.user.is_anonymous:
                username = self.request.user.username
            if self.by_pass_bind_username:
                username = self.by_pass_bind_username

            record_data = {
                "username": username,
                "api": self.request.path,
                "action": self.action,
                "action_label": record_label if record_label else '',
                "post_data": self.params
            }
            record = APICallingRecord.objects.create(**record_data)

            # To do the real work.
            func_result = func(self, *args, **kwargs)

            # To record result of this call after doing real work.
            record.result = "SUCCESS" if self.result else "FAILED"
            record.message = self.message
            record.error_message = self.error_message
            record.finish_time = timezone.now()
            record.save()

            return func_result
        return recording
    return decorator
