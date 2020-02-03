from django.conf import settings
import os

# default values
_ASYNC_TASK_LOGDIR = os.path.join(settings.BASE_DIR, 'logs', 'asynctask')
_ASYNC_TASK_LOGFILE_PREFIX = 'async_task_'
_ASYNC_TASK_SOCKET = '/var/run/async_socket.sock'
_ASYNC_TASK_WORKERS = 4  # Normally equal to CPU cores.
_ASYNC_TASK_REGISTER_MODULE = 'asynctasks'  # This means you should write all async task funcs in 'asynctasks.py' in django app's basedir.
_ASYNC_TASK_LOG_LEVEL = 'DEBUG'

# log settings.
ASYNC_TASK_LOGDIR = getattr(settings, 'ASYNC_TASK_LOGDIR', _ASYNC_TASK_LOGDIR)
ASYNC_TASK_LOGFILE_PREFIX = getattr(settings, 'ASYNC_TASK_LOGFILE_PREFIX', _ASYNC_TASK_LOGFILE_PREFIX)

# message socket
ASYNC_TASK_SOCKET = getattr(settings, 'ASYNC_TASK_SOCKET', _ASYNC_TASK_SOCKET)

# asynctask worker settings.
ASYNC_TASK_WORKERS = getattr(settings, 'ASYNC_TASK_WORKERS', _ASYNC_TASK_WORKERS)

# For importing asynctask funcs when start AsyncTaskServer.
ASYNC_TASK_REGISTER_MODULE = getattr(settings, 'ASYNC_TASK_REGISTER_MODULE', _ASYNC_TASK_REGISTER_MODULE)

# Log level.
ASYNC_TASK_LOG_LEVEL = getattr(settings, 'ASYNC_TASK_LOG_LEVEL', _ASYNC_TASK_LOG_LEVEL)
