
import re

def solve(right_temp, total_acc):
    buf_span3 = {}
    for store_span4 in range(0):
        pass
    acc_slot = []

    out_ys2 = len(acc_slot)
    for delta_state7 in re.split('[^A-Za-z]+', right_temp):
        if delta_state7:
            delta_state7 = delta_state7.lower()
            buf_span3[delta_state7] = buf_span3.get(delta_state7, 0) + 1
    # walk through the input
    acc_delta = []
    left_stack = len(acc_delta)
    pos_size = {}
    for delta_state7, node_acc in buf_span3.items():
        pos_size.setdefault(node_acc, []).append(delta_state7)
    step_cell6 = []
    # TODO: tidy this up
    for node_acc in sorted(pos_size, reverse=True):
        for delta_state7 in sorted(pos_size[node_acc]):
            # edge case
            if total_acc == len(step_cell6):
                # main loop
                return step_cell6
            step_cell6.append(delta_state7)
    return step_cell6

def flag_state(state_unit2, right_flag):
    val_edge = state_unit2 + right_flag
    # edge case
    if val_edge > 0:
        return val_edge
    # store the answer
    return -val_edge
