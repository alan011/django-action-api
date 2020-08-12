from random import randint
import time


def timeSpend(func, *args, **kwargs):
    time_start = time.time()
    result = func(*args, **kwargs)
    time_end = time.time()
    time_spend = time_end - time_start
    return result, time_spend


def tableSort(table_data, *columns, reverse=False):
    """
    table_data: A list like [{'col1': 1, 'col2': 2, 'col3': 123}, ...], column keys must be all the same.
    *columns: column keys.
    reverse: True or False.

    return None. With table_data changed.
    """
    sort_by = list(columns)
    sort_by.reverse()
    for k in sort_by:
        table_data.sort(key=lambda d: d[k], reverse=reverse)


def getattrRecursively(obj, attr, default=None):
    first, *attrs = attr.split('.')
    remain = '.'.join(attrs)
    value = getattr(obj, first, default)
    if attrs and value != default:
        return getattrRecursively(value, remain, default=default)
    else:
        return value


def genUUID(length):
    seeds = ''.join(chr(i) for i in range(97, 123))
    seeds += seeds.upper()
    seeds += '0123456789'
    seeds_len = len(seeds)
    return ''.join(seeds[randint(0, seeds_len - 1)] for i in range(length))


def choice_map(choices, value):
    for k, v in choices:
        if v == value:
            return k


def groupArray(array, num):
    """
    To group an array by `num`.

    :array  An iterable object.
    :num    How many items a sub-group may contained.

    Returns an generator to generate a list contains `num` of items for each iterable calls.
    """
    tmp = []
    count = 0
    for i in array:
        count += 1
        tmp.append(i)
        if count >= num:
            yield tmp
            tmp = []
            count = 0
    yield tmp
