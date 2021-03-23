from django.db import models
from jsonfield import JSONField
from django.utils import timezone


class APICallingRecord(models.Model):
    # db fields.
    id = models.AutoField('ID', primary_key=True)
    username = models.CharField("用户", max_length=64, default="")
    api = models.CharField("调用API", max_length=128, default="")
    action = models.CharField("执行动作", max_length=64, default="")
    action_label = models.CharField("执行动作label", max_length=128, default="")
    post_data = JSONField("操作内容", default={})
    result = models.CharField("操作结果", max_length=16, default="")  # "SUCCESS" or "FAILED"
    message = models.TextField("成功消息", default="")
    error_message = models.TextField("失败消息", default="")
    operating_time = models.DateTimeField("操作时间", default=timezone.now)

    # serializing field.s
    list_fields = ["id", "username", "api", "action", "action_label", "post_data", "result", "message", "error_message", "operating_time"]
    detail_fields = list_fields
    search_fields = ["username", "api", "action", "action_label", "post_data", "message", "error_message"]
    filter_fields = ["result"]

    class Meta:
        ordering = ['-id']
