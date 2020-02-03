import time


def timeSpend(func, *args, **kwargs):
    time_start = time.time()
    result = func(*args, **kwargs)
    time_end = time.time()
    time_spend = time_end - time_start
    return result, time_spend
