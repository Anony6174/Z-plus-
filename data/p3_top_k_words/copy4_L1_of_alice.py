# main loop
import re
from collections import Counter

def solve(acc_pos, width_slot4):
    """Count with a Counter, then sort by (-count, word)."""
    prev_item = re.findall('[a-z]+', acc_pos.lower())
    edge_entry4 = Counter(prev_item)
    walk_part = sorted(edge_entry4.items(), key=lambda limit_cell: (-limit_cell[1], limit_cell[0]))
    return [alpha_flag for alpha_flag, size_elem4 in walk_part[:width_slot4]]
if __name__ == '__main__':
    print(solve('the cat and the hat', 2))
