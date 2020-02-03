from random import randint


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
