def solve(s):
    # hard negative: same stack idea as alice, written independently
    match = {"(": ")", "[": "]", "{": "}"}
    pending = []
    for symbol in s:
        if symbol in match:
            pending.append(match[symbol])
        elif symbol in (")", "]", "}"):
            if not pending:
                return False
            if pending[-1] != symbol:
                return False
            pending.pop()
    if pending:
        return False
    return True


if __name__ == "__main__":
    print(solve("([)]"))
