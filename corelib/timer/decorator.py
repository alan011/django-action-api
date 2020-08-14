from functools import wraps


# 定时任务装饰器。
def cron(every=None, crontab=None, single_process=True):
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
            name = func.__name__
            print(f'===> func name: {name}, state: {self.cron_state}')
            # 对multiprocess的工作模式，修改manager-dict的一级元素，才能触发manager的proxy进程间共享变量的修改，下同。
            state = self.cron_state[name]
            state['running'] = True
            self.cron_state[name] = state
            print(f'===> func name: {name}, state: {self.cron_state}')

            result = func(self, *args, **kwargs)

            state = self.cron_state[name]
            state['running'] = False
            state['last_result'] = result
            self.cron_state[name] = state
            return result

        # 设置工作函数内置属性
        runInCron._is_a_timer_method = True
        runInCron._timer_every = every
        runInCron._timer_crontab = crontab
        runInCron._timer_single_process = single_process

        return runInCron
    return decorator
