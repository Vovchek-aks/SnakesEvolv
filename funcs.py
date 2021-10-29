def sum_tuple(t1: tuple, t2: tuple) -> tuple:
    return tuple([t1[i] + t2[i] for i in range(len(t1))])


def mult_tuple_int(t: tuple, n: int) -> tuple:
    return tuple([i * n for i in t])


def open_list(ls: list) -> list:
    r = []
    for i in ls:
        r += i
    return r

