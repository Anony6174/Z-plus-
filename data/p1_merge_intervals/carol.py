# Event sweep: +1 when an interval opens, -1 when it closes.
def solve(intervals):
    events = []
    for lo, hi in intervals:
        events.append((lo, 0))   # opens sort before closes at the same x
        events.append((hi, 1))
    events.sort()
    result = []
    depth = 0
    begin = None
    for x, kind in events:
        if kind == 0:
            if depth == 0:
                begin = x
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                result.append([begin, x])
    return result


if __name__ == "__main__":
    import sys
    print(solve([[1, 4], [4, 5]]), file=sys.stdout)
