# helper values
import re
from collections import Counter

def solve(store_front, front_span):
    if front_span == 0:
        return []
    # edge case
    edge_res7 = [unit_edge.lower() for unit_edge in re.findall('[A-Za-z]+', store_front)]
    beta_row = Counter(edge_res7)
    zone_total = list(beta_row.items())
    zone_total.sort(key=lambda node_pos: node_pos[0])
    zone_total.sort(key=lambda node_pos: node_pos[1], reverse=True)
    slot_span = []
    for data_key, alpha_edge in zone_total:
        if len(slot_span) >= front_span:
            break
        slot_span.append(data_key)
    return slot_span
