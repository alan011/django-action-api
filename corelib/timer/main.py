import re
import time
# import asyncio
from multiprocessing import Process, Manager
from threading import Thread
from datetime import datetime


class Timer(object):
    """
    请用`.start()`方法来启动Timer主进程。定时任务最小检查间隔：1秒。具体时间间隔由各个功能函数通过cron装饰器来定义。

    timer将以并发的方式执行各个定时任务函数。支持'thread'与'process'两种并发模式。具体参考`.__init__`的参数说明。

    self.cron_state[<func_name>]['running']用于记录各个定时任务函数是否正在运行。

    self.cron_state[<func_name>]['last_result']用于记录该定时任务的最后一次return值。

    不要给定时任务函数定义任何参数(self除外)！
    """

    def __init__(self, worker=None):
        """
        :worker 合法值：'thread', 'process'，默认为'thread'；
            'thread': 以multi-thread方式执行定时任务函数。比较轻量，适合IO等待密集型场景，不适合计算密集型；
            'process': 以multi process方式执行定时任务函数，每个定时任务运行在一个单独的子进程中。可用于计算密集型场景，但比较重，对系统的要求较高。

        当以'process'方式运行时，默认会起两个进程，一个父进程，一个manager子进程。manager子进程用于各工作子进程之间共享全局变量：`self.cron_state`.
        """
        self.cron_pool = {}
        self.cron_state = {}
        self.cron_origin_start_time = None
        self.worker = 'thread' if worker is None else worker
        if worker not in {'process', 'thread', 'coroutine'}:
            raise SystemExit("ERROR: `worker` must be one of 'process', 'thread', or 'coroutine'")
        if self.worker == 'coroutine':
            raise SystemExit('Coroutine mode not support yet. Comming soon!')
        if self.worker == 'process':
            self.manager = Manager()
            self.cron_state = self.manager.dict()

    def _check_to_run_this_timer(self, func):
        to_run = False
        every = func._timer_every
        crontab = func._timer_crontab
        single_process = func._timer_single_process
        name = func.__name__
        if every:
            # 评估时间，决定是否执行。
            if int(time.time() - self.cron_origin_start_time) % every == 0:
                running = self.cron_state[name]['running']
                print(f'func: {name}, single_process: {single_process}, running: {running}')
                if not single_process or not self.cron_state[name]['running']:  # 当上一次执行的进程还未结束时，本次不执行。
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
        return to_run

    def start(self):
        # 注册timer工作函数
        print('Initiallizing timer...')
        for attr_name in filter(lambda a: not a.startswith('_'), dir(self)):
            method = getattr(self, attr_name)
            if getattr(method, '_is_a_timer_method', False):
                print(f'Timer worker registerd: {attr_name}.')
                self.cron_pool[attr_name] = method
                self.cron_state[attr_name] = {"running": False, "last_result": None}

        # 启动主循环，定时检查各个timer工作函数(最小间隔：1秒)
        self.cron_origin_start_time = time.time()
        while True:
            for name in self.cron_pool:
                func = self.cron_pool[name]
                if self._check_to_run_this_timer(func):
                    if self.worker == 'thread':
                        Thread(target=func).start()
                    elif self.worker == 'process':
                        Process(target=func).start()
                print(self.cron_state)
            time.sleep(1)
