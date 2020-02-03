from django.db import models


class AuthToken(models.Model):
    username = models.CharField('用户名称', max_length=8, default='', unique=True)
    token = models.CharField('用户TOKEN', max_length=64, default='', unique=True)
    sign_date = models.DateTimeField('注册日期', auto_now_add=True)
    expired_time = models.IntegerField('有效期限', default=86400)  # Defautl is One day. '0' means never expired.
