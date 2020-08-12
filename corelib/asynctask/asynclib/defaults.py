from django.conf import settings

# default values
_ASYNC_TASK_BIND_ADDR = '127.0.0.1'  # listen ip
_ASYNC_TASK_BIND_PORT = 11118  # listen port
_ASYNC_TASK_WORKERS = 0  # 0 means auto fetch the number from OS CPU cores.
_ASYNC_TASK_REGISTER_MODULE = 'asynctasks'  # This means you should write all async task functions in 'asynctasks.py' in django app's basedir.
_ASYNC_TASK_LOG_LEVEL = 'INFO'

# To user value in settings, or default value.
ASYNC_TASK_BIND_ADDR = getattr(settings, 'ASYNC_TASK_BIND_ADDR', _ASYNC_TASK_BIND_ADDR)
ASYNC_TASK_BIND_PORT = getattr(settings, 'ASYNC_TASK_BIND_PORT', _ASYNC_TASK_BIND_PORT)
ASYNC_TASK_WORKERS = getattr(settings, 'ASYNC_TASK_WORKERS', _ASYNC_TASK_WORKERS)
ASYNC_TASK_REGISTER_MODULE = getattr(settings, 'ASYNC_TASK_REGISTER_MODULE', _ASYNC_TASK_REGISTER_MODULE)
ASYNC_TASK_LOG_LEVEL = getattr(settings, 'ASYNC_TASK_LOG_LEVEL', _ASYNC_TASK_LOG_LEVEL)
