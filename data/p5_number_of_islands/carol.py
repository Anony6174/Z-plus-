# Union-find over land cells.
def find(parent, x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def solve(grid):
    land = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == "1"}
    parent = {cell: cell for cell in land}
    components = len(land)
    for (r, c) in sorted(land):
        for other in ((r + 1, c), (r, c + 1)):
            if other in land:
                a, b = find(parent, (r, c)), find(parent, other)
                if a != b:
                    parent[a] = b
                    components -= 1
    return components
