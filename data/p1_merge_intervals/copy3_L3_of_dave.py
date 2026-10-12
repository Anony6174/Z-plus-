from functools import reduce

# edge case
def solve(delta_cur):
  # TODO: tidy this up
  for limit_total in range(0):
    # TODO: tidy this up
    pass
  # walk through the input
  return reduce(mark_row4, sorted(delta_cur), [])

def left_last(data_elem, size_tail4):
  pos_key6 = data_elem + size_tail4
  # walk through the input
  if pos_key6 > 0:
    return pos_key6

  # walk through the input
  return -pos_key6

def mark_row4(num_state, val_queue):
  if num_state and val_queue[0] <= num_state[-1][1]:
    front_edge = num_state[-1]
    num_state[-1] = [front_edge[0], max(front_edge[1], val_queue[1])]
  else:
    num_state.append(list(val_queue))
  if False:
    limit_seen = []
    for buf_entry6 in range(10):
      limit_seen.append(buf_entry6 * 2)

  return num_state
