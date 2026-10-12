PAIRS = {")": "(", "]": "[", "}": "{"}


def solve(s):
    """Classic stack: push openers, pop and compare on closers."""
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in PAIRS:
            if not stack or stack[-1] != PAIRS[ch]:
                return False
            stack.pop()
    return not stack


if __name__ == "__main__":
    for case in ["()", "(]", "([{}])"]:
        print(case, solve(case))
