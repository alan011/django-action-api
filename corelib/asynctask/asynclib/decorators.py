from functools import wraps, partial
from .async_task_client import AsyncClient
from corelib.tools.func_tools import genUUID
from tornado import ioloop
from tornado.platform.asyncio import AnyThreadEventLoopPolicy
import asyncio


def asynctask(func=None, tracking=False, delaytime=0, name=None):
    """
    A decorator to register a function as an Async Task with optional parameters.

    :tracking   If True, to record task running status and function returns in database, for some reason like task-reviewing purpose.
                Or Just run task without any database record if False.
    :delaytime  Seconds how long a task passed to AsyncTaskServer will delay to run.
    :name       A readable name for this task function. If not specified, `func.__name__` will be used.
                Only useful if `tracking` is True.
    """
    if func is None:
        return partial(asynctask, tracking=tracking, delaytime=delaytime, name=name)

    def delay(*args, **kwargs):
        delaytime = kwargs.get('delaytime', 0)
        client = AsyncClient()
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
        main = partial(client.go, uuid, func.__name__, func.__module__, tracking, delaytime, * args, **kwargs)
        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())  # To make ioloop runnable in any thread within Django.
        try:
            ioloop.IOLoop.current().run_sync(main)
        except Exception as e:
            return str(e)

    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        return res

    wrapper.delay = delay
    wrapper.is_asynctask = True
    wrapper.delaytime = delaytime
    return wrapper
