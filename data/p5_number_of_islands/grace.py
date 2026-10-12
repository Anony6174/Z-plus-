from collections import deque


def neighbours(r, c, rows, cols):
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        if 0 <= r + dr < rows and 0 <= c + dc < cols:
            yield r + dr, c + dc


def solve(grid):
    # hard negative: BFS with a deque, same approach as bob
    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])
    water = [[ch == "0" for ch in row] for row in grid]
    count = 0
    for r in range(rows):
        for c in range(cols):
            if water[r][c]:
                continue
            count += 1
            water[r][c] = True
            q = deque()
            q.append((r, c))
            while q:
                cr, cc = q.popleft()
                for nr, nc in neighbours(cr, cc, rows, cols):
                    if not water[nr][nc]:
                        water[nr][nc] = True
                        q.append((nr, nc))
    return count
