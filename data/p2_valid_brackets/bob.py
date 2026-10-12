def solve(s):
    opening = "([{"
    closing = ")]}"
    expected = []
    for c in s:
        k = opening.find(c)
        if k >= 0:
            expected.append(closing[k])
            continue
        if c in closing:
            if len(expected) == 0:
                return False
            if expected.pop() != c:
                return False
    return len(expected) == 0
