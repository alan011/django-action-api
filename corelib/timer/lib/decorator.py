import traceback
from django.utils import timezone
from functools import wraps


# 定时任务装饰器。
def cron(every=None, crontab=None, enabled=True, dynamic=False):
    """
    一个cron装饰器，用于在timer中执行定时任务。
    内置了self参数，只能作用于Timer与其子类的实例方法。

    参数说明：
        every       大于0的秒数。提供数值后，timer启动时运行一次，以后每间隔every秒数再次执行。

        crontab     一个crontab字符串，六个字段，空格符为间隔。依次为：秒，分，时，日，月，周。
                    类似linux的crontab，支持'*'写法表示任意值；支持类似*/5'的间隔写法，间隔数需是正整数。

        enabled     用于直接设置是否启用此定时任务。（对于静态任务，修改之后需要重启timer服务。）

        dynamic     用于标记当前定时任务为动态定时任务。
                    标记为`dynamic`时，其他参数可不填。需要通过API或者相关Handler在数据库中做运行参数配置。

    注意：every与crontab同时提供时，以every为准。静态任务不支持at_time.
    """
    def decorator(func):
        # 设置工作函数内置属性
        func._is_a_timer_task = True
        func._timer_every = every
        func._timer_crontab = crontab
        func._timer_enabled = enabled
        func._is_dynamic = dynamic

        @wraps(func)
        def runInCron(self, name, *args, **kwargs):
            # 标记在运行
            if func._is_dynamic:
                self.dynamic_state[name]['running'] = True
            else:
                self.cron_state[name]['running'] = True

            # 开始执行
            self.logger.log(f"Task '{name}' start to run...")
            start_at = timezone.now()
            try:
                func(*args, **kwargs)
            except Exception:
                traceback.print_exc()
                result = 'failed'
            else:
                result = 'success'
            end_at = timezone.now()

            # 执行结果数据统计
            time_spend = round(end_at.timestamp() - start_at.timestamp(), 3)
            if func._is_dynamic and self.enable_dynamic:
                from corelib.timer.api.models import CronJob
                self.dynamic_tasks[name]['total_run_count'] += 1
                _attrs = {
                    'last_run_start_at': start_at,
                    'last_run_spend_time': time_spend,
                    'last_run_result': result,
                    'total_run_count': self.dynamic_tasks[name]['total_run_count']
                }
                CronJob.objects.filter(name=name).update(**_attrs)
                self.logger.log(f'dynamic task result updated: {_attrs}', level='DEBUG')
            self.logger.log(f"Task '{name}' finished. time_spend: {time_spend}s, result: {result}")

            # 标记已停止
            if func._is_dynamic:
                self.dynamic_state[name]['running'] = False
            else:
                self.cron_state[name]['running'] = False
            return result

        return runInCron
    return decorator
