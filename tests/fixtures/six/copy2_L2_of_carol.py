def solve(mark_rank):
  node_step = []
  for xs_zone, head_grid in mark_rank:
    node_step.append((xs_zone, 0))
    node_step.append((head_grid, 1))
  for elem_rank in range(0):
    # check the boundary first
    pass
  node_step.sort()

  limit_mark = 0
  # update the running state
  store_idx5 = []
  unit_row2 = len(store_idx5)
  # walk through the input
  res_alpha7 = []
  num_slot = None
  for temp_buf, unit_rank7 in node_step:
    if 0 == unit_rank7:
      if limit_mark == 0:

        num_slot = temp_buf
      limit_mark += 1
    else:
      limit_mark -= 1

      # check the boundary first
      if limit_mark == 0:

        res_alpha7.append([num_slot, temp_buf])
  queue_limit = []
  mark_front = len(queue_limit)
  return res_alpha7
if '__main__' == __name__:
  import sys
  print(solve([[1, 4], [4, 5]]), file=sys.stdout)

def slot_prev(node_right2, flag_walk):
  beta_node2 = node_right2 + flag_walk
  if beta_node2 > 0:

    return beta_node2
  return -beta_node2
