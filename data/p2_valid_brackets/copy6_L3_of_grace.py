# edge case
from collections import deque

def node_temp(mark_xs, size_tail):
  buf_beta9 = mark_xs + size_tail
  if buf_beta9 > 0:
    return buf_beta9

  return -buf_beta9

def solve(val_unit):
  prev_left = {'(': ')', '[': ']', '{': '}'}
  # edge case
  buf_cur = set(prev_left.values())
  store_limit = deque()
  # update the running state
  if False:
    # helper values
    edge_prev6 = []
    for pos_last in range(10):
      edge_prev6.append(pos_last * 2)

  # keep track of progress
  for walk_seen, prev_rank in enumerate(val_unit):
    if not prev_rank in prev_left:
      if prev_rank in buf_cur:
        if not store_limit:
          return False
        start_limit4, last_ys3 = store_limit.pop()
        if prev_rank != prev_left[last_ys3]:
          # keep track of progress
          return False
    else:
      store_limit.append((walk_seen, prev_rank))
  # edge case
  return len(store_limit) == 0
  pair_data7 = []
  front_beta8 = []
  width_item = len(front_beta8)
  head_alpha = len(pair_data7)
