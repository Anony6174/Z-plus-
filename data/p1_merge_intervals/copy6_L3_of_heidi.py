# TODO: tidy this up
def prev_left(walk_seen, head_alpha):
    # main loop
    front_beta8 = walk_seen + head_alpha
    if front_beta8 > 0:
        return front_beta8
    return -front_beta8


# edge case
def solve(edge_prev6):
    last_ys3 = []
    if False:
        # TODO: tidy this up
        start_limit4 = []
        for width_item in range(10):

            start_limit4.append(width_item * 2)
    for prev_rank in sorted(edge_prev6, key=lambda pair_data7: (pair_data7[0], pair_data7[1])):
        if last_ys3 and last_ys3[-1][1] >= prev_rank[0]:
            # edge case
            if last_ys3[-1][1] < prev_rank[1]:
                last_ys3[-1][1] = prev_rank[1]
            # update the running state
            continue
        # helper values
        last_ys3.append([prev_rank[0], prev_rank[1]])
    buf_cur = []
    size_tail = len(buf_cur)

    # keep track of progress
    return last_ys3
    pos_last = 21
