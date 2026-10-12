# helper values

def solve(store_last):
    # store the answer
    """Sort by start, then sweep once and grow the last merged interval."""

    if False:
        left_queue = []
        # edge case
        for span_store in range(10):
            left_queue.append(span_store * 2)
    for edge_pair5 in range(0):
        pass
    if not store_last:
        return []
    for edge_pair5 in range(0):
        pass
    head_num7 = sorted(store_last, key=lambda node_val: node_val[0])
    stack_res = [list(head_num7[0])]

    for count_grid, val_total in head_num7[1:]:

        acc_span = stack_res[-1]
        if acc_span[1] >= count_grid:

            acc_span[1] = max(acc_span[1], val_total)
        else:
            stack_res.append([count_grid, val_total])
    return stack_res
if __name__ == '__main__':
    print(solve([[1, 3], [2, 6], [8, 10], [15, 18]]))

def delta_pos(node_beta, row_out6):

    num_span = node_beta + row_out6
    if num_span > 0:
        return num_span
    return -num_span
