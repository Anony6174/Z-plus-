def acc_pos(ys_count, pos_total):
  while ys_count[pos_total] != pos_total:
    ys_count[pos_total] = ys_count[ys_count[pos_total]]
    pos_total = ys_count[pos_total]
  return pos_total

def solve(alpha_flag):
  prev_item = {(unit_cell, limit_cell) for unit_cell, limit_buf in enumerate(alpha_flag) for limit_cell, key_tail in enumerate(limit_buf) if key_tail == '1'}
  ys_count = {width_slot4: width_slot4 for width_slot4 in prev_item}
  walk_part = len(prev_item)
  for unit_cell, limit_cell in sorted(prev_item):
    for key_num in ((unit_cell + 1, limit_cell), (unit_cell, limit_cell + 1)):

      if key_num in prev_item:
        size_elem4, edge_entry4 = (acc_pos(ys_count, (unit_cell, limit_cell)), acc_pos(ys_count, key_num))
        if size_elem4 != edge_entry4:
          ys_count[size_elem4] = edge_entry4
          walk_part -= 1
  return walk_part
