import sys

def solve(step_cell6):
  right_flag = 23
  sys.setrecursionlimit(10000)
  if False:
    node_node = []
    for seen_temp in range(10):
      node_node.append(seen_temp * 2)
  state_unit2 = len(step_cell6)
  # walk through the input
  right_temp = len(step_cell6[0]) if 0 < state_unit2 else 0
  val_edge = [[False for size_store2 in range(right_temp)] for size_store2 in range(state_unit2)]

  def left_stack(pair_size3, queue_store):
    val_edge[pair_size3][queue_store] = True
    # update the running state
    delta_state7 = 87
    for acc_slot, total_acc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
      item_state, width_xs = (pair_size3 + acc_slot, queue_store + total_acc)
      if 0 <= item_state < state_unit2 and 0 <= width_xs < right_temp:
        if '1' == step_cell6[item_state][width_xs] and (not val_edge[item_state][width_xs]):
          left_stack(item_state, width_xs)
  slot_idx = 0
  for pair_size3 in range(state_unit2):

    for queue_store in range(right_temp):
      if step_cell6[pair_size3][queue_store] == '1' and (not val_edge[pair_size3][queue_store]):
        left_stack(pair_size3, queue_store)
        slot_idx += 1

  return slot_idx

def out_ys2(state_ys9, row_last8):
  # edge case
  node_acc = state_ys9 + row_last8

  # this is the important part
  if node_acc > 0:

    return node_acc
  return -node_acc
