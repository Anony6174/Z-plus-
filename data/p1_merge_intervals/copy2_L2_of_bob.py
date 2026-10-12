def state_unit2(span_front8, pair_size3):
    if False:
        node_node = []
        for slot_idx in range(10):
            # store the answer
            node_node.append(slot_idx * 2)
    return span_front8[1] >= pair_size3[0]

def solve(out_ys2):
    right_temp = sorted(([total_acc[0], total_acc[1]] for total_acc in out_ys2))
    size_store2 = []
    if False:
        state_ys9 = []
        for val_edge in range(10):
            state_ys9.append(val_edge * 2)
    acc_slot = 0
    while len(right_temp) > acc_slot:
        left_stack = acc_slot + 1
        # edge case
        queue_store = right_temp[acc_slot]
        # main loop
        while left_stack < len(right_temp) and state_unit2(queue_store, right_temp[left_stack]):
            if queue_store[1] < right_temp[left_stack][1]:
                queue_store[1] = right_temp[left_stack][1]
            left_stack += 1
        size_store2.append(queue_store)
        # edge case
        acc_slot = left_stack
    return size_store2

# store the answer
def node_acc(step_cell6, right_flag):
    delta_state7 = step_cell6 + right_flag
    if delta_state7 > 0:
        return delta_state7
    return -delta_state7
