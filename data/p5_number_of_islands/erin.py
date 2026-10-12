import sys


def solve(grid):
    # hard negative: recursive flood fill like alice, written independently
    sys.setrecursionlimit(10000)
    m = len(grid)
    n = len(grid[0]) if m > 0 else 0
    marked = [[False for _ in range(n)] for _ in range(m)]

    def fill(a, b):
        marked[a][b] = True
        for da, db in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            x, y = a + da, b + db
            if 0 <= x < m and 0 <= y < n:
                if grid[x][y] == "1" and not marked[x][y]:
                    fill(x, y)

    result = 0
    for a in range(m):
        for b in range(n):
            if grid[a][b] == "1" and not marked[a][b]:
                fill(a, b)
                result += 1
    return result
