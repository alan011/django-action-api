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


def get_item_from_table_list(target_list, filter):
    """
    参数说明：
        target_list: 为一个table list, 需满足以下结构，例如：
            [
                {'id': 1, 'name': 'lalal', ...},
                {'id': 2, 'name': 'lalalaa', ...},
            ]

        filter: 条件过滤字典，比如：
            {
                'name': 'lalal'
            }

    返回第一个匹配到的元素。
    """
    for item in target_list:
        matched = 0
        for k, v in filter.items():
            if k in item and item[k] == v:
                matched += 1
        if matched == len(filter):
            return item


def merge_table_list(*target_lists, identified_by='id', order=True, order_by='id'):
    identities = set()
    result = []
    for table in target_lists:
        for item in table:
            if not isinstance(item, dict):
                return None, "ERROR: Invalid table list found. Item of a table list be all dict."
            identity = item.get(identified_by, None)
            if identity is None:
                return None, f"ERROR: Invalid row identifier '{identified_by}' found for table list row."
            if identity not in identities:
                identities.add(identity)
                result.append(item)
    reverse = True if order_by.startswith('-') else False
    tableSort(result, 'id', reverse=reverse)

    return result, None
