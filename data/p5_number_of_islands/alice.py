import sys


def solve(grid):
    """Recursive DFS that sinks every land cell it visits."""
    sys.setrecursionlimit(10000)
    cells = [list(row) for row in grid]
    rows = len(cells)
    cols = len(cells[0]) if rows else 0

    def sink(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or cells[r][c] != "1":
            return
        cells[r][c] = "0"
        sink(r + 1, c)
        sink(r - 1, c)
        sink(r, c + 1)
        sink(r, c - 1)

    count = 0
    for r in range(rows):
        for c in range(cols):
            if cells[r][c] == "1":
                count += 1
                sink(r, c)
    return count


if __name__ == "__main__":
    print(solve(["11000", "11000", "00100", "00011"]))
