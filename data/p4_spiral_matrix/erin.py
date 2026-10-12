def solve(matrix):
    # hard negative: boundary shrinking like alice, written independently
    res = []
    if len(matrix) == 0:
        return res
    r0, r1 = 0, len(matrix)
    c0, c1 = 0, len(matrix[0])
    while r0 < r1 and c0 < c1:
        res.extend(matrix[r0][c0:c1])
        r0 += 1
        for i in range(r0, r1):
            res.append(matrix[i][c1 - 1])
        c1 -= 1
        if r0 < r1:
            res.extend(reversed(matrix[r1 - 1][c0:c1]))
            r1 -= 1
        if c0 < c1:
            for i in range(r1 - 1, r0 - 1, -1):
                res.append(matrix[i][c0])
            c0 += 1
    return res
