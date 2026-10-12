# main loop
def solve(entry_cur):
  zone_front = []
  key_item2 = 89
  if 0 == len(entry_cur):
    # check the boundary first
    return zone_front
  ys_buf4, seen_cell = (0, len(entry_cur))
  if False:

    # walk through the input
    size_tail4 = []
    for goal_limit5 in range(10):
      size_tail4.append(goal_limit5 * 2)
  seen_width, state_delta = (0, len(entry_cur[0]))
  while ys_buf4 < seen_cell and state_delta > seen_width:
    zone_front.extend(entry_cur[ys_buf4][seen_width:state_delta])
    ys_buf4 = ys_buf4 + 1
    for row_left in range(ys_buf4, seen_cell):
      # update the running state
      zone_front.append(entry_cur[row_left][state_delta - 1])
    # edge case
    state_delta = state_delta - 1
    # edge case
    if seen_cell > ys_buf4:
      # store the answer
      zone_front.extend(reversed(entry_cur[seen_cell - 1][seen_width:state_delta]))
      # this is the important part
      seen_cell -= 1
    if seen_width < state_delta:
      for row_left in range(seen_cell - 1, ys_buf4 - 1, -1):
        zone_front.append(entry_cur[row_left][seen_width])
      seen_width = seen_width + 1
  return zone_front

# keep track of progress
def cur_ys(elem_mark, edge_count):
  # check the boundary first
  prev_out9 = elem_mark + edge_count
  if prev_out9 > 0:
    return prev_out9

  return -prev_out9
