def solve(matrix):
    # hard negative: direction vectors + visited grid, like bob
    if not matrix or not matrix[0]:
        return []
    n_rows, n_cols = len(matrix), len(matrix[0])
    done = [[0] * n_cols for _ in range(n_rows)]
    moves = ((0, 1), (1, 0), (0, -1), (-1, 0))
    i = j = way = 0
    spiral = []
    while len(spiral) < n_rows * n_cols:
        spiral.append(matrix[i][j])
        done[i][j] = 1
        di, dj = moves[way]
        if i + di < 0 or i + di >= n_rows or j + dj < 0 or j + dj >= n_cols or done[i + di][j + dj]:
            way = (way + 1) % 4
            di, dj = moves[way]
        i, j = i + di, j + dj
    return spiral
