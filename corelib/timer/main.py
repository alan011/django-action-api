import time
import re
from multiprocessing import Process
from functools import wraps
from datetime import datetime


# Timer基础类。
class Timer(object):
    def __init__(self):
        self.cron_pool = None  # self.register(...)中初始化
        self.cron_origin_start_time = None  # self.start(...)中初始化

    def register(self, *args):
        self.cron_pool = {}
        for method in args:
            self.cron_pool[method] = {
                "func": getattr(self, method, None),
                "running": False,
            }

    def start(self):
        """
        Timer主进程，每秒执行一次。具体时间间隔由各个功能函数自己通过cron来定义。
        """
        self.cron_origin_start_time = time.time()
        while True:
            for name in filter(lambda n: self.cron_pool[n], self.cron_pool):
                p = Process(target=self.cron_pool[name]['func'])
                p.start()
            time.sleep(1)


# 定时任务装饰器。
def cron(name, every=None, crontab=None):
    """
    一个cron装饰器，用于在timer中执行定时任务。
    内置了self参数，只能作用于Timer与其子类的实例方法。

    :name       定时任务名称，用于并发执行时，做状态检测。

    :every      大于0的秒数。提供数值后，timer启动时运行一次，以后每间隔every秒数再次执行。

    :crontab    一个crontab字符串，六个字段，空格符为间隔。依次为：秒，分，时，日，月，周。
                类似linux的crontab，支持'*'写法表示任意值；支持类似*/5'的间隔写法，间隔数需是正整数。

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
        return runInCron
    return decorator
