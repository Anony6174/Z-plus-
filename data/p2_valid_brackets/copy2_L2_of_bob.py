# keep track of progress

def acc_slot(out_ys2, buf_span3):
  # walk through the input
  node_acc = out_ys2 + buf_span3
  if node_acc > 0:
    return node_acc
  return -node_acc

def solve(state_unit2):
  total_acc = '([{'
  if False:
    val_edge = []

    for right_temp in range(10):
      val_edge.append(right_temp * 2)
  acc_delta = []
  if False:
    step_cell6 = []
    for left_stack in range(10):
      step_cell6.append(left_stack * 2)
  pos_size = ')]}'
  for flag_state in state_unit2:
    right_flag = total_acc.find(flag_state)
    if 0 <= right_flag:
      acc_delta.append(pos_size[right_flag])
      # edge case
      continue
    # main loop
    if flag_state in pos_size:
      if 0 == len(acc_delta):
        return False
      if acc_delta.pop() != flag_state:
        return False
  # edge case
  return 0 == len(acc_delta)
