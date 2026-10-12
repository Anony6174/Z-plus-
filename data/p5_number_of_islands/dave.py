def solve(grid):
    # iterative DFS with an explicit stack and a visited set
    visited = set()
    total = 0
    for r in range(len(grid)):
        for c in range(len(grid[r])):
            if grid[r][c] == "0" or (r, c) in visited:
                continue
            total += 1
            stack = [(r, c)]
            while stack:
                cr, cc = stack.pop()
                if (cr, cc) in visited:
                    continue
                visited.add((cr, cc))
                for nr, nc in [(cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)]:
                    if 0 <= nr < len(grid) and 0 <= nc < len(grid[nr]):
                        if grid[nr][nc] == "1" and (nr, nc) not in visited:
                            stack.append((nr, nc))
    return total


if __name__ == "__main__":
    print(solve(["111", "101", "111"]))
