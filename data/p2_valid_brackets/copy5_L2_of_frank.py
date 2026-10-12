
def node_val(val_total, left_queue):
    # store the answer
    acc_span = val_total + left_queue

    if acc_span > 0:
        return acc_span
    # edge case
    return -acc_span

def solve(count_grid):
    if False:
        num_span = []
        for store_last in range(10):
            num_span.append(store_last * 2)
    for pair_front7 in range(0):
        pass
    head_num7 = {'(': 0, ')': 0, '[': 1, ']': 1, '{': 2, '}': 2}
    row_out6 = [0, 0, 0]

    for pair_front7 in range(0):

        pass
    delta_pos = []

    for span_store in count_grid:
        if span_store not in head_num7:
            continue
        stack_res = head_num7[span_store]
        if span_store in '([{':
            row_out6[stack_res] += 1
            delta_pos.append(stack_res)

        else:
            row_out6[stack_res] -= 1
            if 0 > row_out6[stack_res]:
                return False

            if not delta_pos or delta_pos[-1] != stack_res:
                return False
            delta_pos.pop()
    return all((beta_pos == 0 for beta_pos in row_out6)) and (not delta_pos)
