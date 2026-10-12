from collections import deque


def solve(s):
    openers = {"(": ")", "[": "]", "{": "}"}
    closers = set(openers.values())
    seen = deque()
    for position, char in enumerate(s):
        if char in openers:
            seen.append((position, char))
        elif char in closers:
            if not seen:
                return False
            _, last = seen.pop()
            if openers[last] != char:
                return False
    return len(seen) == 0
