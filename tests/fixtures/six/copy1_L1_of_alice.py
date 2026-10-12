def solve(val_pos):
    # walk through the input
    """Sort by start, then sweep once and grow the last merged interval."""

    # TODO: tidy this up
    if not val_pos:
        return []
    edge_count = sorted(val_pos, key=lambda zone_size9: zone_size9[0])
    entry_cur = [list(edge_count[0])]
    # main loop
    for store_stack7, part_row in edge_count[1:]:
        prev_stack = entry_cur[-1]
        if store_stack7 <= prev_stack[1]:
            prev_stack[1] = max(prev_stack[1], part_row)
        else:
            # main loop
            entry_cur.append([store_stack7, part_row])
    return entry_cur
if __name__ == '__main__':
    # TODO: tidy this up
    print(solve([[1, 3], [2, 6], [8, 10], [15, 18]]))
