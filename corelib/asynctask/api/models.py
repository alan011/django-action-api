from django.db import models
from jsonfield import JSONField


class AsyncTask(models.Model):
    """
    To record serialized async-tasks.
    """
    STATUS_OPTIONS = ((0, "等待执行"), (1, "正在执行"), (2, "执行完毕"))
    RESULT_OPTIONS = ((0, "成功"), (1, "失败"))

    # db fields.
    id = models.AutoField('ID', primary_key=True)
    uuid = models.CharField('UUID', max_length=128, unique=True, default='')
    name = models.CharField("任务名称", max_length=128, default='')
    status = models.IntegerField("执行状态", choices=STATUS_OPTIONS, default=0)
    result = models.IntegerField("执行结果", choices=RESULT_OPTIONS, default=0)
    return_data = JSONField("执行返回数据", null=True)
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    finish_time = models.DateTimeField("完成时间", null=True)

    # serializing settings.
    list_fields = ["id", "func_name", "func_args", "func_kwargs", "readable_name", "status", "result", "return_data", "create_time", "finish_time"]
    detail_fields = list_fields
    search_fields = ["readable_name", "func_name"]
    filter_fields = ["status", "result"]
