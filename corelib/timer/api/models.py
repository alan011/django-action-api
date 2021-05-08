from django.db import models
from jsonfield import JSONField
from django.utils import timezone
from .choices import TASK_ENABLE_CHOICES, TASK_RESULT_CHOICES


class CronJob(models.Model):
    '''
    特别字段说明：
        every       执行间隔，单位为秒。默认为0，表示不设置。
        crontab     一个类似linux的crontab配置字符串。默认为''，空字符串，表示不设置。
                    具体分7个字段：'秒 分 时 日 月 周 年'
                    如： '31 * * * * * *'，表示每分钟的31秒时刻，启动执行
                        '0 0 */2 * * * 2021'，表示当前时间的小时位，为2的倍数时执行，且仅在2021年生效。
        at_time     仅在此时间点执行一次。通过`last_run_at`来判断是否已经执行。

        注意：every、crontab、at_time必须设置其中一个，否则该任务无效。
            若都设置，按此优先级顺序生效: every, crontab, at_time

        expired_count     可用于设置运行多少次后自动失效。默认为0，表示不做限制。
        expired_time            设置自动失效时间点，过期后不再执行。

        注意：当这两个同时设定时，谁先达到限制条件，就以谁为准。触发后，将自动设置`enabled`为0

        last_run_result     用于记录任务的执行结果。

        注意，此表中只记录任务的执行结果，不做任何其他任务执行信息记录。定时任务函数的任务return值，都会被Timer主进程忽略。
        若要跟踪定时任务的执行中间过程，请输出到Timer的日志中查看。
    '''
    # db fields.
    id = models.AutoField('ID', primary_key=True)
    name = models.CharField('任务名称', max_length=128, default='', unique=True)
    description = models.TextField('任务描述', default='')
    task = models.TextField('任务函数', default='')
    args = JSONField('位置参数', default=[])
    kwargs = JSONField('键值参数', default={})
    every = models.IntegerField('执行间隔', default=0)
    crontab = models.TextField('crontab配置', default='')
    at_time = models.DateTimeField('任务创建时间', null=True, default=None)
    enabled = models.IntegerField('是否启用', choices=tuple(TASK_ENABLE_CHOICES.items()), default=1)
    expired_count = models.IntegerField('失效次数设置', default=0)
    expired_time = models.DateTimeField('失效日期设置', null=True, default=None)
    last_run_start_at = models.DateTimeField('最后一次执行时间', null=True, default=None)
    last_run_spend_time = models.FloatField('最后一次执行耗时', default=0)
    last_run_result = models.CharField('最后一次执行结果', max_length=16, choices=tuple(TASK_RESULT_CHOICES.items()), default='')
    total_run_count = models.IntegerField('总共执行次数', default=0)
    create_at = models.DateTimeField('任务创建时间', default=timezone.now)

    # serializing fields.
    search_fields = ['name', 'description', 'task', 'args', 'kwargs', 'crontab']
    filter_fields = ['enabled', 'last_run_result']

    class Meta:
        ordering = ['-id']


class AvailableTasks(models.Model):
    id = models.AutoField('ID', primary_key=True)
    module_path = models.TextField('任务函数路径', default='')
    usage_doc = models.TextField('使用说明', default='')

    # serializing fields.
    search_fields = ['id', 'module_path', 'usage_doc']
