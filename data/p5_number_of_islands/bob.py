from collections import deque


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    islands = 0
    for i in range(height):
        for j in range(width):
            if grid[i][j] != "1" or seen[i][j]:
                continue
            islands += 1
            queue = deque([(i, j)])
            seen[i][j] = True
            while queue:
                x, y = queue.popleft()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < height and 0 <= ny < width and not seen[nx][ny] and grid[nx][ny] == "1":
                        seen[nx][ny] = True
                        queue.append((nx, ny))
    return islands
