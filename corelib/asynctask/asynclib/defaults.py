from django.conf import settings

# default values
_ASYNCTASK_BIND_ADDR = '127.0.0.1'  # listen ip
_ASYNCTASK_BIND_PORT = 11118  # listen port
_ASYNCTASK_WORKERS = 0  # 0 means auto fetch the number from OS CPU cores.
_ASYNCTASK_REGISTER_MODULE = 'asynctasks'  # This means you should write all async task functions in 'asynctasks.py' in django app's basedir.
_ASYNCTASK_LOG_LEVEL = 'INFO'

# To user value in settings, or default value.
ASYNCTASK_BIND_ADDR = getattr(settings, 'ASYNCTASK_BIND_ADDR', _ASYNCTASK_BIND_ADDR)
ASYNCTASK_BIND_PORT = getattr(settings, 'ASYNCTASK_BIND_PORT', _ASYNCTASK_BIND_PORT)
ASYNCTASK_WORKERS = getattr(settings, 'ASYNCTASK_WORKERS', _ASYNCTASK_WORKERS)
ASYNCTASK_REGISTER_MODULE = getattr(settings, 'ASYNCTASK_REGISTER_MODULE', _ASYNCTASK_REGISTER_MODULE)
ASYNCTASK_LOG_LEVEL = getattr(settings, 'ASYNCTASK_LOG_LEVEL', _ASYNCTASK_LOG_LEVEL)
