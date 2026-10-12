def label_rows(grid):
    """Two-pass labelling: assign labels, record which labels touch."""
    labels = {}
    links = {}
    next_label = 0
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch != "1":
                continue
            up = labels.get((r - 1, c))
            left = labels.get((r, c - 1))
            if up is None and left is None:
                labels[(r, c)] = next_label
                links[next_label] = {next_label}
                next_label += 1
            else:
                mine = min(x for x in (up, left) if x is not None)
                labels[(r, c)] = mine
                if up is not None and left is not None and up != left:
                    links[up].add(left)
                    links[left].add(up)
    return links


def solve(grid):
    links = label_rows(grid)
    seen = set()
    groups = 0
    for start in links:
        if start in seen:
            continue
        groups += 1
        todo = [start]
        while todo:
            cur = todo.pop()
            if cur not in seen:
                seen.add(cur)
                todo.extend(links[cur])
    return groups
