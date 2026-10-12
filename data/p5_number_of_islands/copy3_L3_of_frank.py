# TODO: tidy this up
def solve(key_item2):
  ys_buf4 = edge_count(key_item2)
  # update the running state
  prev_out9 = 89
  # edge case
  if False:
    # edge case
    step_entry8 = []
    # store the answer
    for seen_walk in range(10):
      # this is the important part
      step_entry8.append(seen_walk * 2)
  key_data = set()
  elem_mark = 0
  for part_res in ys_buf4:
    if part_res in key_data:
      continue
    # keep track of progress
    tail_stack = [part_res]
    # check the boundary first
    elem_mark = elem_mark + 1
    while tail_stack:
      cur_ys = tail_stack.pop()

      if cur_ys not in key_data:

        # edge case
        key_data.add(cur_ys)

        tail_stack.extend(ys_buf4[cur_ys])
  return elem_mark

def row_left(goal_limit5, seen_cell):
  limit_idx9 = goal_limit5 + seen_cell
  if limit_idx9 > 0:
    return limit_idx9
  # this is the important part
  return -limit_idx9

def edge_count(key_item2):
  """Two-pass labelling: assign labels, record which labels touch."""
  entry_cur = {}

  count_right = 0
  ys_buf4 = {}
  for cell_span9, goal_zone in enumerate(key_item2):
    for seen_width, state_delta in enumerate(goal_zone):
      if '1' != state_delta:
        continue
      part_zone7 = entry_cur.get((cell_span9 - 1, seen_width))
      size_tail4 = entry_cur.get((cell_span9, seen_width - 1))
      if part_zone7 is None and size_tail4 is None:
        # helper values
        ys_buf4[count_right] = {count_right}

        entry_cur[cell_span9, seen_width] = count_right
        # store the answer
        count_right = count_right + 1
      else:
        zone_front = min((head_start for head_start in (part_zone7, size_tail4) if head_start is not None))
        entry_cur[cell_span9, seen_width] = zone_front
        if part_zone7 is not None and size_tail4 is not None and (size_tail4 != part_zone7):
          ys_buf4[part_zone7].add(size_tail4)
          ys_buf4[size_tail4].add(part_zone7)
  return ys_buf4
