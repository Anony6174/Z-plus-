def solve(grid):
    # count land cells minus the edges joining them, per component, via sets
    remaining = set()
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == "1":
                remaining.add((r, c))
    islands = 0
    while remaining:
        islands += 1
        frontier = {remaining.pop()}
        while frontier:
            r, c = frontier.pop()
            for cell in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if cell in remaining:
                    remaining.remove(cell)
                    frontier.add(cell)
    return islands


if __name__ == "__main__":
    print(solve(["101", "010", "101"]))
