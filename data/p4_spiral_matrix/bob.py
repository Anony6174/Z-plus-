DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]


def solve(matrix):
    rows = len(matrix)
    cols = len(matrix[0]) if rows else 0
    total = rows * cols
    visited = [[False] * cols for _ in range(rows)]
    r = c = d = 0
    out = []
    for _ in range(total):
        out.append(matrix[r][c])
        visited[r][c] = True
        nr, nc = r + DIRECTIONS[d][0], c + DIRECTIONS[d][1]
        if not (0 <= nr < rows and 0 <= nc < cols) or visited[nr][nc]:
            d = (d + 1) % 4
            nr, nc = r + DIRECTIONS[d][0], c + DIRECTIONS[d][1]
        r, c = nr, nc
    return out
