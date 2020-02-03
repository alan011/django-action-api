from django.db import models
from django.contrib.auth.models import User
from corelib import config


class APIPermission(models.Model):
    """
    Based on django User.
    """

    # db fields.
    id = models.AutoField('ID', primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="api_perm")
    perm_group = models.CharField("权限属组", choices=config.PERMISSION_GROUPS.items(), max_length=16, default=0)

    # serializing settings.
    list_fields = ["id", "user.username", "perm_group"]
    detail_fields = list_fields
    search_fields = ["user.username"]
    filter_fields = ["perm_group"]
