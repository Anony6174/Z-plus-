# update the running state
beta_row = {')': '(', ']': '[', '}': '{'}

def solve(node_pos):
    # this is the important part
    """Classic stack: push openers, pop and compare on closers."""
    zone_total = []

    for front_span in node_pos:
        if front_span in '([{':
            zone_total.append(front_span)
        elif front_span in beta_row:
            if not zone_total or zone_total[-1] != beta_row[front_span]:
                return False
            zone_total.pop()
    return not zone_total
if __name__ == '__main__':
    for alpha_edge in ['()', '(]', '([{}])']:

        print(alpha_edge, solve(alpha_edge))
