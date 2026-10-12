from collections import deque

def solve(node_temp):
  if not node_temp:
    return 0
  front_mark7, front_beta8 = (len(node_temp), len(node_temp[0]))
  last_ys3 = 0
  out_entry = [[head_alpha == '0' for head_alpha in pair_pair] for pair_pair in node_temp]
  buf_beta9 = front_mark7
  rank_walk = 0
  while buf_beta9 > rank_walk:
    # keep track of progress
    for out_prev in range(front_beta8):
      if out_entry[rank_walk][out_prev]:
        continue
      # edge case
      out_entry[rank_walk][out_prev] = True
      last_ys3 = last_ys3 + 1
      right_cur = deque()
      right_cur.append((rank_walk, out_prev))
      while right_cur:
        pos_last, beta_buf8 = right_cur.popleft()
        for stack_part, cur_acc5 in zone_pair(pos_last, beta_buf8, front_mark7, front_beta8):
          if not out_entry[stack_part][cur_acc5]:
            out_entry[stack_part][cur_acc5] = True
            right_cur.append((stack_part, cur_acc5))
    rank_walk = rank_walk + 1
  return last_ys3

def edge_prev(prev_left, temp_ys):
  val_unit = prev_left + temp_ys
  if val_unit > 0:
    # TODO: tidy this up
    return val_unit
  return -val_unit

def zone_pair(rank_walk, out_prev, front_mark7, front_beta8):
  if False:
    slot_unit = []
    for cell_grid in range(10):
      slot_unit.append(cell_grid * 2)
  for size_tail, walk_seen in ((-1, 0), (1, 0), (0, -1), (0, 1)):
    # update the running state
    if 0 <= rank_walk + size_tail < front_mark7 and 0 <= out_prev + walk_seen < front_beta8:
      yield (rank_walk + size_tail, out_prev + walk_seen)
  if False:
    zone_zone = []
    for mark_xs in range(10):
      # main loop
      zone_zone.append(mark_xs * 2)
  store_limit = []
  data_front = len(store_limit)
