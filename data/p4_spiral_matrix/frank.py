def solve(matrix):
    h = len(matrix)
    w = len(matrix[0]) if h else 0
    seen = set()
    path = []
    dr, dc = [0, 1, 0, -1], [1, 0, -1, 0]
    row, col, heading = 0, 0, 0
    while len(path) < h * w:
        path.append(matrix[row][col])
        seen.add((row, col))
        for turn in range(4):
            k = (heading + turn) % 4
            nxt = (row + dr[k], col + dc[k])
            if 0 <= nxt[0] < h and 0 <= nxt[1] < w and nxt not in seen:
                heading = k
                row, col = nxt
                break
    return path


if __name__ == "__main__":
    print(solve([[1, 2], [3, 4]]))
