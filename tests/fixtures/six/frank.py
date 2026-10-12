def merge_two(a, b):
    """Merge b into a if they overlap, else return None."""
    if b[0] > a[1] or a[0] > b[1]:
        return None
    return [min(a[0], b[0]), max(a[1], b[1])]


def solve(intervals):
    blocks = [list(iv) for iv in intervals]
    changed = True
    while changed:
        changed = False
        for x in range(len(blocks)):
            for y in range(x + 1, len(blocks)):
                joined = merge_two(blocks[x], blocks[y])
                if joined is not None:
                    blocks[x] = joined
                    del blocks[y]
                    changed = True
                    break
            if changed:
                break
    blocks.sort()
    return blocks
