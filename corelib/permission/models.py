from django.db import models
from django.contrib.auth.models import User


class APIPermission(models.Model):
    """
    Based on django User.
    """

    # db fields.
    id = models.AutoField('ID', primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="api_perm", unique=True)
    realname = models.CharField("中文姓名", max_length=64, default='')
    perm_group = models.CharField("权限属组", max_length=64, default='')

    # serializing settings.
    list_fields = ["id", "perm_group", {"user": ["username"]}, "realname"]
    detail_fields = list_fields
    search_fields = ["user.username"]
    filter_fields = ["perm_group"]
