# Peel the first row, then rotate what is left counter-clockwise.
def rotate_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def solve(matrix):
    grid = [list(row) for row in matrix if row]
    result = []
    while grid:
        result.extend(grid[0])
        grid = rotate_ccw(grid[1:]) if len(grid) > 1 else []
        grid = [row for row in grid if row]
    return result
