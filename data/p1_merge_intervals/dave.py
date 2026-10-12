from functools import reduce


def _fold(acc, interval):
    if acc and interval[0] <= acc[-1][1]:
        top = acc[-1]
        acc[-1] = [top[0], max(top[1], interval[1])]
    else:
        acc.append(list(interval))
    return acc


def solve(intervals):
    return reduce(_fold, sorted(intervals), [])
