import time
import asyncio


class Timer(object):
    def __init__(self):
        self.cron_pool = {}
        self.cron_origin_start_time = None

    def start(self):
        """
        此方法用于启动Timer主进程。定时任务最小检查间隔：1秒。具体时间间隔由各个功能函数通过cron装饰器来定义。

        timer将采用tornado的ioloop来将阻塞任务变得awaitbale，然后通过ioloop并发、异步执行各个timer功能函数。各个功能函数是否在运行，由.cron_pool[<method>]['running']来记录。

        对于各个功能函数的执行结果，timer都不做记录。若需要跟踪执行状态或者记录执行结果，请自行在功能函数中作好日志跟踪，并将结果记录到数据库或者其他存储。

        不要给timer功能函数传参！
        """
        # 注册timer工作函数
        for attr_name in filter(lambda a: not a.startswith('_'), dir(self)):
            method = getattr(self, attr_name)
            if getattr(method, '_is_a_timer_method', False):
                print(f'===> attr_name: {attr_name}')
                self.cron_pool[attr_name] = {
                    "func": method,
                    "running": False,
                }

        # 启动事件循环，定时检查各个timer工作函数(最小间隔：1秒)
        self.cron_origin_start_time = time.time()
        loop = asyncio.get_event_loop()
        while True:
            for name in self.cron_pool:
                func = self.cron_pool[name]['func']
                is_running = self.cron_pool[name]['running']
                if getattr(func, '_is_a_single_proecess_timer', False) and is_running:
                    continue
                loop.run_in_executor(None, func)
            time.sleep(1)
