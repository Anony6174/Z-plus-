def walk(matrix, top, left, bottom, right, acc):
    if top > bottom or left > right:
        return acc
    acc.extend(matrix[top][left:right + 1])
    acc.extend(matrix[r][right] for r in range(top + 1, bottom + 1))
    if top < bottom:
        acc.extend(matrix[bottom][c] for c in range(right - 1, left - 1, -1))
    if left < right:
        acc.extend(matrix[r][left] for r in range(bottom - 1, top, -1))
    return walk(matrix, top + 1, left + 1, bottom - 1, right - 1, acc)


def solve(matrix):
    if not matrix or not matrix[0]:
        return []
    return walk(matrix, 0, 0, len(matrix) - 1, len(matrix[0]) - 1, [])
