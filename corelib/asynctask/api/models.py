from django.db import models
from jsonfield import JSONField


class AsyncTask(models.Model):
    """
    To record serialized async-tasks.
    """
    STATUS_OPTIONS = ((0, "等待执行"), (1, "正在执行"), (2, "执行完毕"))

    # db fields.
    id = models.AutoField('ID', primary_key=True)
    uuid = models.CharField('UUID', max_length=128, unique=True, default='')
    name = models.CharField("任务名称", max_length=128, default='')
    status = models.IntegerField("执行状态", choices=STATUS_OPTIONS, default=0)
    result = models.BooleanField("执行结果", default=True)
    result_data = JSONField("执行返回数据", default={})
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    finish_time = models.DateTimeField("完成时间", null=True)

    # serializing settings.
    list_fields = ["id", "uuid", "name", "status", "result", "result_data", "create_time", "finish_time"]
    detail_fields = list_fields
    search_fields = ["uuid", "name"]
    filter_fields = ["status", "result"]
