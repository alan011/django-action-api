import time
import re
from functools import wraps
from datetime import datetime


# 定时任务装饰器。
def cron(name, every=None, crontab=None, single_process=False):
    """
    一个cron装饰器，用于在timer中执行定时任务。
    内置了self参数，只能作用于Timer与其子类的实例方法。

    :name       定时任务名称，用于并发执行时，做状态检测。

    :every      大于0的秒数。提供数值后，timer启动时运行一次，以后每间隔every秒数再次执行。

    :crontab    一个crontab字符串，六个字段，空格符为间隔。依次为：秒，分，时，日，月，周。
                类似linux的crontab，支持'*'写法表示任意值；支持类似*/5'的间隔写法，间隔数需是正整数。

    :single_process   如果为True，监测到之前的相同任务仍然处于running状态，则忽略本次不执行（下次周期会再次检查）。

    注意：every与crontab同时提供时，以every为准。
    """
    def decorator(func):
        @wraps(func)
        def runInCron(self, *args, **kwargs):
            to_run = False
            if every:
                # 评估时间，决定是否执行。
                if int(time.time() - self.cron_origin_start_time) % every == 0:
                    if not self.cron_pool[name]['running']:  # 当上一次执行的进程还未结束时，本次不执行。
                        to_run = True
            elif crontab:
                _crontab = crontab.split()
                if len(_crontab) == 6:
                    # 评估crontab是否与当前时间相符
                    now = datetime.now()
                    now_str = now.strftime("%S %M %H %d %m %W")
                    now_list = [int(t) for t in now_str.split()]
                    match_count = 0
                    for i in range(6):
                        if _crontab[i] == '*' or int(_crontab[i]) == now_list[i]:
                            match_count += 1
                        elif re.search(r'^\*/[1-9][0-9]*$', _crontab[i]):
                            _every = int(_crontab[i].split('/')[1])
                            if now_list[i] % _every == 0:
                                match_count += 1
                    if match_count == 6:
                        to_run = True

            # 执行函数
            result = None
            if to_run:
                self.cron_pool[name]['running'] = True
                result = func(self, *args, **kwargs)
                self.cron_pool[name]['running'] = False
                self.cron_pool[name]['last_result'] = result
            return result

        # 设置工作函数内置属性
        runInCron._is_a_timer_method = True
        runInCron._is_a_single_proecess_timer = single_process

        return runInCron
    return decorator
