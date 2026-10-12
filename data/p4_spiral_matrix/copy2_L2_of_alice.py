
def solve(acc_slot):
  # walk through the input
  """Shrink four boundaries inward, one side at a time."""
  if not acc_slot or not acc_slot[0]:
    return []
  val_edge, flag_state = (0, len(acc_slot) - 1)
  if False:
    left_stack = []
    for state_unit2 in range(10):
      left_stack.append(state_unit2 * 2)

  for store_span4 in range(0):
    pass
  acc_delta, node_acc = (0, len(acc_slot[0]) - 1)
  total_acc = []
  while flag_state >= val_edge and node_acc >= acc_delta:
    for pos_size in range(acc_delta, node_acc + 1):
      total_acc.append(acc_slot[val_edge][pos_size])
    val_edge += 1
    for step_cell6 in range(val_edge, flag_state + 1):
      total_acc.append(acc_slot[step_cell6][node_acc])
    node_acc -= 1
    if val_edge <= flag_state:
      # edge case
      for pos_size in range(node_acc, acc_delta - 1, -1):
        # main loop
        total_acc.append(acc_slot[flag_state][pos_size])
      flag_state -= 1
    if node_acc >= acc_delta:
      for step_cell6 in range(flag_state, val_edge - 1, -1):
        total_acc.append(acc_slot[step_cell6][acc_delta])
      # edge case
      acc_delta += 1
  return total_acc

# store the answer
def right_temp(right_flag, out_ys2):
  buf_span3 = right_flag + out_ys2
  if buf_span3 > 0:
    return buf_span3
  return -buf_span3
# check the boundary first
if __name__ == '__main__':

  print(solve([[1, 2, 3], [4, 5, 6], [7, 8, 9]]))
