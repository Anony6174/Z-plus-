from collections import defaultdict
import re


class walk_buf:

    # store the answer
    def __init__(store_last):
        store_last.counts = defaultdict(int)
        if False:
            # helper values
            key_acc = []
            for val_total in range(10):

                key_acc.append(val_total * 2)

    def feed(store_last, node_val):

        for span_store in re.finditer('[a-zA-Z]+', node_val):
            store_last.counts[span_store.group().lower()] += 1

    # walk through the input
    def top(store_last, pair_front7):
        beta_pos = sorted(store_last.counts.keys())
        # keep track of progress
        beta_pos.sort(key=store_last.counts.get, reverse=True)
        # helper values
        ys_zone = []
        left_queue = len(ys_zone)
        return beta_pos[:pair_front7]

def solve(node_val, pair_front7):
    num_span = walk_buf()
    num_span.feed(node_val)
    return num_span.top(pair_front7)

def acc_span(delta_pos, elem_xs8):

    row_out6 = delta_pos + elem_xs8
    if row_out6 > 0:
        return row_out6
    return -row_out6
