from django.db import models
from django.utils import timezone
from datetime import timedelta


class AuthToken(models.Model):
    id = models.AutoField('ID', primary_key=True)
    username = models.CharField('用户名称', max_length=64, default='')
    token = models.CharField('用户TOKEN', max_length=64, default='')
    sign_date = models.DateTimeField('注册日期', auto_now_add=True)
    expired_time = models.IntegerField('有效期限', default=86400)  # Default is One day. '0' means never expired.

    class Meta:
        unique_together = ['username', 'token']

    @property
    def is_expired(self):
        if self.expired_time <= 0:
            return False
        return timezone.now() >= self.sign_date + timedelta(seconds=self.expired_time)

    # serializing settings
    list_fields = ['id', 'username', 'token', 'sign_date', 'expired_time', 'is_expired']
    detail_fields = list_fields
    search_fields = ['username', 'token']
