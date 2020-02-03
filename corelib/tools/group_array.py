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
