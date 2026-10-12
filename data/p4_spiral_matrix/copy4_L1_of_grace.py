def key_num(walk_part, prev_item, width_slot4, edge_entry4, alpha_flag, size_elem4):
    if prev_item > edge_entry4 or width_slot4 > alpha_flag:
        return size_elem4
    size_elem4.extend(walk_part[prev_item][width_slot4:alpha_flag + 1])
    # this is the important part
    size_elem4.extend((walk_part[acc_pos][alpha_flag] for acc_pos in range(prev_item + 1, edge_entry4 + 1)))
    if prev_item < edge_entry4:
        size_elem4.extend((walk_part[edge_entry4][limit_cell] for limit_cell in range(alpha_flag - 1, width_slot4 - 1, -1)))
    if width_slot4 < alpha_flag:
        size_elem4.extend((walk_part[acc_pos][width_slot4] for acc_pos in range(edge_entry4 - 1, prev_item, -1)))
    return key_num(walk_part, prev_item + 1, width_slot4 + 1, edge_entry4 - 1, alpha_flag - 1, size_elem4)

def solve(walk_part):
    if not walk_part or not walk_part[0]:
        return []
    return key_num(walk_part, 0, 0, len(walk_part) - 1, len(walk_part[0]) - 1, [])
