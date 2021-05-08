import re
import time
from multiprocessing import Process, Manager
from threading import Thread
from django.conf import settings
from django.utils import timezone
from importlib import import_module
from .defaults import TIMER_LOG_LEVEL, TIMER_REGISTER_MODULE, DYNAMIC_UPDATING_INTERVAL
from corelib.tools.logger import Logger


class Timer(object):
    """
    定时任务分为两类：
        - 静态任务：配置数据无需入库，直接通过cron装饰器加载到timer进程中执行。
        - 动态任务：配置数据记录在数据库（此表中），需要在数据库中设定运行参数后，才能运行。
    考虑到安全因素，不支持自定义脚本的上传执行。所有定时任务，都需系统开发人员编码。

    静态任务：
        相当于是一种简化的动态定时任务。无需入库，直接在编码时写死。
        所以更加简单、易用，但缺乏灵活性，不可由用户来调度，也不可传参。
        故，在定义静态任务时，不可为任务函数定义任何参数。

    动态任务：
        在timer服务启动时，仅做模块儿加载入库，不会直接开始运行。
        需要在数据库中配置运行参数，才能开始执行。
        timer进程同步数据库中任务参数的时间间隔最小为1分钟（可做全局配置，不可小于1分钟）。
        这即表示用户修改了数据库之后，会在1分钟内生效，而不是及时生效。
        紧急情况下，要想及时生效，可以重启timer服务进程来实现。

    timer服务进程：
        timer将会并发地执行各个定时任务函数。支持'thread'与'process'两种并发模式。可在class初始化时做设定。
        'thread'模式，适合IO等待型的任务处理。但，不适合高负荷的计算密集型。是Timer的默认工作模式。
        'process'模式，可用于高负荷的计算密集型。但，比较重，最好单独找服务器独立部署。

    另外，考虑到性能雪崩效应，timer中的任务，都不允许交叠执行。即同一个任务，上一次执行周期的任务执行还未结束时，则本次执行周期不执行。
    故，对于需要重复执行的任务，请合理评估最小执行周期，否则某些执行周期会失效。
    """

    def __init__(self, worker=None):
        """
        :worker 合法值：'thread', 'process'，默认为'thread'；
            'thread': 以multi-thread方式执行每个定时任务函数。
            'process': 以multi-process方式执行每个定时任务函数。

        当以'process'方式运行时，默认会起两个进程，一个父进程，一个manager子进程。manager子进程用于各工作子进程之间共享全局变量：`self.cron_state`.
        """
        self.cron_pool = {}
        self.cron_state = {}
        self.dynamic_tasks = {}
        self.dynamic_state = {}
        self.cron_origin_start_time = None
        self.worker = 'thread' if worker is None else worker
        self.logger = Logger(trigger_level=TIMER_LOG_LEVEL, msg_prefix='Timer: ')
        if worker not in {'process', 'thread'}:
            raise SystemExit("ERROR: `worker` must be 'process' or 'thread'")
        self.is_process_mod = False
        if self.worker == 'process':
            self.is_process_mod = True
            self.manager = Manager()
            self.cron_state = self.manager.dict()
            self.dynamic_state = self.manager.dict()
            self.dynamic_tasks = self.manager.dict()

        self.enable_dynamic = False
        if 'corelib.timer.timer_api' in settings.INSTALLED_APPS:
            self.enable_dynamic = True

    def schedule_task(self, func, dynamic_task=None):
        """
        判定当前时间点，是否需要执行指定的定时任务。
        """
        # 开始评估执行周期
        name = dynamic_task['name'] if dynamic_task else f'{func.__module__}.{func.__name__}'
        to_run = False
        every = dynamic_task['every'] if dynamic_task else func._timer_every
        crontab = dynamic_task['crontab'] if dynamic_task else func._timer_crontab
        at_time = dynamic_task['at_time'] if dynamic_task else None

        # 根据timer服务启动时间，计算every相对执行时间点。
        if every:
            if int(time.time() - self.cron_origin_start_time) % every == 0:
                to_run = True

        # 根据系统绝对时间，评估crontab字符串是否匹配。
        elif crontab:
            _crontab = crontab.split()
            if len(_crontab) == 7:
                now = timezone.now()
                now_str = now.strftime("%S %M %H %d %m %W %Y")
                now_list = [int(t) for t in now_str.split()]
                match_count = 0
                for i in range(7):
                    if _crontab[i] == '*':
                        match_count += 1
                    elif re.search(r'^\*/[1-9][0-9]*$', _crontab[i]):
                        _every = int(_crontab[i].split('/')[1])
                        if now_list[i] % _every == 0:
                            match_count += 1
                    else:
                        try:
                            num = int(_crontab[i])
                        except Exception:
                            self.logger.log(f"Invalid crontab string: '{crontab}'. Crontab task '{name}' unable to run! ", level='ERROR')
                            break

                        if num == now_list[i]:
                            match_count += 1

                # 每个字段都匹配成功，放可执行crontab任务。
                if match_count == 7:
                    to_run = True

        # 根据系统绝对时间评估at_time单次任务。
        elif at_time:
            if not self.dynamic_state[name]['running'] and timezone.now() >= at_time:
                to_run = True

        # 不允许交叠执行。
        if to_run:
            _running = self.dynamic_state[name]['running'] if dynamic_task else self.cron_state[name]['running']
            if _running:
                self.logger.log(f"Task '{name}' is still running, ignore it this time.", level='WARNING')
                return False

        return to_run

    def register(self):
        '''
        注册timer定时任务
        '''
        if self.enable_dynamic:
            from corelib.timer.timer_api.models import AvailableTasks

        for app in filter(lambda s: not s.startswith('django.'), settings.INSTALLED_APPS):
            mod_str = f'{app}.{TIMER_REGISTER_MODULE}'
            try:
                mod = import_module(mod_str)
            except Exception as e:
                self.logger.log(f"Ignore invalid django-installed app: '{app}'.")
                self.logger.log(f"{str(e)}", level='DEBUG')
            else:
                for attr_name in filter(lambda a: not a.startswith('_'), dir(mod)):
                    func = getattr(mod, attr_name)
                    index = f'{mod_str}.{attr_name}'
                    if getattr(func, '_is_a_timer_task', False):
                        self.cron_pool[index] = func

                        # 动态任务的注册/更新
                        if self.enable_dynamic and getattr(func, '_is_dynamic', False):
                            attrs = {
                                'module_path': index,
                                'usage_doc': '' if func.__doc__ is None else func.__doc__,
                            }
                            AvailableTasks.objects.update_or_create(**attrs)
                            _type = 'dynamic'

                        # 静态任务初始化运行状态
                        else:
                            _state = {"running": False}
                            self.cron_state[index] = self.manager.dict(_state) if self.is_process_mod else _state
                            _type = 'static'

                        self.logger.log(f"To register {_type} task '{index}' succeeded.")

    def update_dynamic_tasks(self):
        """
        读取数据库配置，更新全局属性`dynamic_tasks`与`dynamic_state`
        """
        self.logger.log('Try to update dynamic tasks from DB', 'DEBUG')
        from corelib.timer.timer_api.models import CronJob

        self.dynamic_tasks = self.manager.dict() if self.is_process_mod else {}
        qs = CronJob.objects.filter(enabled=1)
        for obj in qs:
            name = obj.name
            self.logger.log(f"Updating dynamic task '{name}' from DB.", 'DEBUG')
            # 加载定时任务
            _attr = {
                'name': name,
                'task': obj.task,
                'args': obj.args,
                'kwargs': obj.kwargs,
                'every': obj.every,
                'crontab': obj.crontab,
                'at_time': obj.at_time,
                'expired_time': obj.expired_time,
                'expired_count': obj.expired_count,
                'total_run_count': obj.total_run_count
            }
            self.dynamic_tasks[name] = self.manager.dict(_attr) if self.is_process_mod else _attr

            # 初始化state
            if name not in self.dynamic_state:
                _state = {'running': False}
                self.dynamic_state[name] = self.manager.dict(_state) if self.is_process_mod else _state
        self.logger.log('To update dynamic tasks from DB succeeded!', 'DEBUG')

    def is_expired(self, name):
        '''
        针对动态任务，根据配置，将已失效的任务自动设置为失效状态。
        '''
        from corelib.timer.timer_api.models import CronJob

        expired_time = self.dynamic_tasks[name]['expired_time']
        expired_count = self.dynamic_tasks[name]['expired_count']
        total_run_count = self.dynamic_tasks[name]['total_run_count']
        every = self.dynamic_tasks[name]['every']
        crontab = self.dynamic_tasks[name]['crontab']
        at_time = self.dynamic_tasks[name]['at_time']

        if expired_time and expired_time <= timezone.now():
            CronJob.objects.filter(name=name).update(enabled=0)
            self.logger.log(f"Dynamic task '{name}' has expired!")
            return True
        if expired_count and total_run_count >= expired_count:
            CronJob.objects.filter(name=name).update(enabled=0)
            self.logger.log(f"Dynamic task '{name}' has expired, according to count limit '{expired_count}'!")
            return True
        if not (every or crontab):
            if not at_time:
                CronJob.objects.filter(name=name).update(enabled=0)
                self.logger.log(f"Task '{name}' with no running way set is now be disabled!")
                return True
            if total_run_count >= 1:
                CronJob.objects.filter(name=name).update(enabled=0)
                self.logger.log(f"At time task '{name}' finished and will not run any more!")
                return True
        return False

    def run_static_tasks(self):
        '''
        并发执行静态任务
        '''
        for task in self.cron_pool:
            func = self.cron_pool[task]
            if not func._timer_enabled:
                continue
            args = [self, f'{func.__module__}.{func.__name__}']
            if self.schedule_task(func):
                if self.worker == 'thread':
                    Thread(target=func, args=args).start()
                elif self.worker == 'process':
                    Process(target=func, args=args).start()

    def run_dynamic_tasks(self):
        '''
        并发执行动态任务
        '''
        expired_names = []
        for name, task in self.dynamic_tasks.items():
            # 先做过期检查
            if self.is_expired(name):
                expired_names.append(name)
                continue

            # 然后执行cron调度
            func = self.cron_pool[task['task']]
            if self.schedule_task(func, task):
                args = [self, name]
                for arg in task['args']:
                    args.append(arg)
                if self.worker == 'thread':
                    Thread(target=func, args=args, kwargs=task['kwargs']).start()
                elif self.worker == 'process':
                    Process(target=func, args=args, kwargs=task['kwargs']).start()

        # 最后，清理过期的动态任务
        for name in expired_names:
            self.dynamic_tasks.pop(name)
            self.dynamic_state.pop(name)

    def start(self):
        """
        timer服务启动函数
        """
        # 注册timer工作函数
        self.logger.log('Initiallizing timer...')
        self.register()

        # 动态任务，首次更新
        if self.enable_dynamic:
            self.update_dynamic_tasks()

        # 启动主循环
        dynamic_update_internal = 60 if DYNAMIC_UPDATING_INTERVAL < 60 else DYNAMIC_UPDATING_INTERVAL
        self.cron_origin_start_time = time.time()
        time.sleep(1)  # 延迟一秒，错开`cron_origin_start_time`
        last_time = int(self.cron_origin_start_time)
        while True:
            current_time = int(time.time())
            if current_time > last_time:
                self.logger.log('timer start to check.', level='DEBUG')
                if self.enable_dynamic and current_time % dynamic_update_internal == 0:
                    self.update_dynamic_tasks()
                    self.logger.log(f'dynamic tasks: {self.dynamic_tasks}', 'DEBUG')
                self.run_static_tasks()
                if self.enable_dynamic:
                    self.run_dynamic_tasks()
            last_time = current_time
            time.sleep(0.2)
