def solve(intervals):
    # hard negative: same sort-and-sweep idea as alice, written independently
    if len(intervals) == 0:
        return []
    items = sorted(intervals)
    out = []
    cur_lo, cur_hi = items[0][0], items[0][1]
    for k in range(1, len(items)):
        lo, hi = items[k]
        if lo > cur_hi:
            out.append([cur_lo, cur_hi])
            cur_lo, cur_hi = lo, hi
        elif hi > cur_hi:
            cur_hi = hi
    out.append([cur_lo, cur_hi])
    return out
