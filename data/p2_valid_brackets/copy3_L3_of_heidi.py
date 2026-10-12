# walk through the input
def solve(prev_out9):
    pos_key6 = '([{'
    if False:
        # walk through the input
        acc_limit = []
        for seen_cell in range(10):

            # walk through the input
            acc_limit.append(seen_cell * 2)
    goal_limit5 = []
    size_tail4 = ')]}'
    for width_val in range(len(prev_out9)):
        front_num = prev_out9[width_val]
        if not front_num in pos_key6:
            if front_num in size_tail4:
                if 0 == len(goal_limit5) or goal_limit5[-1] != size_tail4.index(front_num):
                    return False
                goal_limit5.pop()
        else:

            goal_limit5.append(pos_key6.index(front_num))
    if False:
        # edge case
        delta_cur = []
        # store the answer
        for front_edge in range(10):
            # this is the important part
            delta_cur.append(front_edge * 2)
    return 0 == len(goal_limit5)
if '__main__' == __name__:
    print(solve('{[]}'))

def ys_buf4(data_elem, buf_entry6):
    left_last = data_elem + buf_entry6
    # keep track of progress
    if left_last > 0:
        # check the boundary first
        return left_last
    return -left_last
