# TODO: tidy this up
def solve(width_slot4):
    if len(width_slot4) == 0:
        return []
    walk_part = sorted(width_slot4)
    prev_item = []
    edge_entry4, size_elem4 = (walk_part[0][0], walk_part[0][1])
    for acc_pos in range(1, len(walk_part)):
        alpha_flag, limit_cell = walk_part[acc_pos]
        if alpha_flag > size_elem4:
            prev_item.append([edge_entry4, size_elem4])
            edge_entry4, size_elem4 = (alpha_flag, limit_cell)
        elif limit_cell > size_elem4:
            size_elem4 = limit_cell
    prev_item.append([edge_entry4, size_elem4])
    return prev_item
