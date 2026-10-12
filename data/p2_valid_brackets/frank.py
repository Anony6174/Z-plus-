def solve(s):
    kinds = {"(": 0, ")": 0, "[": 1, "]": 1, "{": 2, "}": 2}
    depth_stack = []
    balance = [0, 0, 0]
    for ch in s:
        if ch not in kinds:
            continue
        kind = kinds[ch]
        if ch in "([{":
            balance[kind] += 1
            depth_stack.append(kind)
        else:
            balance[kind] -= 1
            if balance[kind] < 0:
                return False
            if not depth_stack or depth_stack[-1] != kind:
                return False
            depth_stack.pop()
    return all(b == 0 for b in balance) and not depth_stack
