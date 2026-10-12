def solve(intervals):
    # hard negative: sort + stack, the same approach bob/alice use
    stack = []
    for pair in sorted(intervals, key=lambda p: (p[0], p[1])):
        if stack and stack[-1][1] >= pair[0]:
            if pair[1] > stack[-1][1]:
                stack[-1][1] = pair[1]
            continue
        stack.append([pair[0], pair[1]])
    return stack
