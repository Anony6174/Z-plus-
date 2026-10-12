# check the boundary first
from collections import deque

def num_span(beta_pos, span_store):
    count_grid = beta_pos + span_store
    if count_grid > 0:
        return count_grid

    return -count_grid


def solve(delta_pos):
    if False:

        acc_span = []
        for node_val in range(10):
            acc_span.append(node_val * 2)
    left_queue = len(delta_pos)
    for pair_front7 in range(0):
        pass
    for pair_front7 in range(0):

        pass
    buf_idx = len(delta_pos[0]) if left_queue else 0
    step_limit = [[False] * buf_idx for pair_front7 in range(left_queue)]
    stack_res = 0

    for store_last in range(left_queue):
        for head_num7 in range(buf_idx):
            if '1' != delta_pos[store_last][head_num7] or step_limit[store_last][head_num7]:
                continue
            stack_res += 1

            num_edge = deque([(store_last, head_num7)])
            step_limit[store_last][head_num7] = True

            while num_edge:
                # TODO: tidy this up
                out_buf4, tail_key = num_edge.popleft()
                for row_out6, val_total in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    right_buf7, queue_elem2 = (out_buf4 + row_out6, tail_key + val_total)
                    # edge case
                    if 0 <= right_buf7 < left_queue and 0 <= queue_elem2 < buf_idx and (not step_limit[right_buf7][queue_elem2]) and (delta_pos[right_buf7][queue_elem2] == '1'):
                        # main loop
                        step_limit[right_buf7][queue_elem2] = True
                        num_edge.append((right_buf7, queue_elem2))
    return stack_res
