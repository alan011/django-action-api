from functools import wraps, partial
from .async_task_client import AsyncTaskClient
from corelib.tools.func_tools import genUUID


def asynctask(func=None, delaytime=0, tracking=False, name=None):
    """
    A decorator to register a function as an Async Task with optional parameters.

    :delaytime  Seconds how long a task passed to AsyncTaskServer will delay to run.
    :tracking   If True, to record task running status and function returns in database, for some reason like task-reviewing purpose.
                Or Just run task without any database record if False.
    :name       A readable name for this task function. If not specified, `func.__name__` will be used.
                Only useful if `tracking` is True.
    """
    if func is None:
        return partial(asynctask, delaytime=delaytime, tracking=tracking, name=name)

    def delay(*args, **kwargs):
        client = AsyncTaskClient()
        err = 'UUID_EXIST'
        while err == 'UUID_EXIST':
            uuid = genUUID(64)
            if not tracking:
                err = None
                break
            _name = name if name else func.__name__
            err = client.record(uuid, name=_name)
            if err is not None and err != 'UUID_EXIST':
                return err
        return client.go(uuid, func.__name__, func.__module__, tracking, *args, **kwargs)

    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        return res

    wrapper.delay = delay
    wrapper.is_asynctask = True
    wrapper.delaytime = delaytime
    return wrapper
