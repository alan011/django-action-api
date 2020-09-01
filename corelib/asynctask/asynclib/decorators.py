from functools import wraps, partial
from .async_task_client import AsyncClient
from corelib.tools.func_tools import genUUID
from tornado import ioloop
from tornado.platform.asyncio import AnyThreadEventLoopPolicy
from django.conf import settings
from django.utils import timezone
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
        if tracking:
            kwargs['__async_task_uuid__'] = uuid
            kwargs['__async_func_name__'] = func.__name__
        main = partial(client.go, uuid, func.__name__, func.__module__, tracking, delaytime, * args, **kwargs)
        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())  # To make ioloop runnable in any thread within Django.
        try:
            ioloop.IOLoop.current().run_sync(main)
        except Exception as e:
            return str(e)

    @wraps(func)
    def wrapper(*args, **kwargs):
        # To record.
        _to_record = False
        if tracking and 'corelib.asynctask.api' in settings.INSTALLED_APPS:
            _to_record = True
            uuid = kwargs.pop('__async_task_uuid__')
            func_name = kwargs.pop('__async_func_name__')
            from corelib.asynctask.api.models import AsyncTask
            obj = AsyncTask.objects.filter(uuid=uuid).first()
            obj.status = 1
            obj.save()

        try:
            # To do the real work.
            res = func(*args, **kwargs)

        except Exception as e:
            if _to_record:
                obj.result = False
                obj.result_data = {
                    'result': False,
                    'error_msg': f"ERROR: To run asynctask '{func_name}' failed. task uuid: '{uuid}'. {str(e)}",
                    'data': None
                }
            else:
                raise e
        else:
            if _to_record:
                obj.result = True
                obj.return_data = {'result': True, 'data': res}
        finally:
            if _to_record:
                obj.status = 2
                obj.finish_time = timezone.now()
                obj.save()

        return res

    wrapper.delay = delay
    wrapper.is_asynctask = True
    wrapper.delaytime = delaytime
    return wrapper
