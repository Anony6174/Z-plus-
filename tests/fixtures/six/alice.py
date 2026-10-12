def solve(intervals):
    """Sort by start, then sweep once and grow the last merged interval."""
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda iv: iv[0])
    merged = [list(ordered[0])]
    for start, end in ordered[1:]:
        last = merged[-1]
        if start <= last[1]:
            # overlap or touch: extend the current block
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return merged


if __name__ == "__main__":
    print(solve([[1, 3], [2, 6], [8, 10], [15, 18]]))
