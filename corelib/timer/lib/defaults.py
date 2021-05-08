from django.conf import settings

"""
配置参数说明：

TIMER_REGISTER_MODULE   定时任务注册模块，默认为'timer', 即，some_django_app/timer.py
TIMER_LOG_LEVEL         timer_server的日志级别，默认为'INFO', 可选值['DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL']
TIMER_WORKER_MOD        timer_server的工作模式，默认为'thread'，表示以多线程方式执行各个定时任务。（不适合计算密集型的任务）
                        也可以是'process'，表示以子进程的方式执行各个并发任务。（可以用作计算密集型的任务）

DYNAMIC_UPDATING_INTERVAL   动态任务同步数据库配置的周期，默认是60，表是一分钟检查一次动态数据的更新，不能小于60。
"""

_TIMER_REGISTER_MODULE = 'timer'  # 要求在个django app下编写timer.py模块
_TIMER_LOG_LEVEL = 'INFO'
_TIMER_WORKER_MOD = 'thread'
_DYNAMIC_UPDATING_INTERVAL = 60

TIMER_REGISTER_MODULE = getattr(settings, 'TIMER_REGISTER_MODULE', _TIMER_REGISTER_MODULE)
TIMER_LOG_LEVEL = getattr(settings, 'TIMER_LOG_LEVEL', _TIMER_LOG_LEVEL)
TIMER_WORKER_MOD = getattr(settings, 'TIMER_WORKER_MOD', _TIMER_WORKER_MOD)
DYNAMIC_UPDATING_INTERVAL = getattr(settings, 'DYNAMIC_UPDATING_INTERVAL', _DYNAMIC_UPDATING_INTERVAL)
