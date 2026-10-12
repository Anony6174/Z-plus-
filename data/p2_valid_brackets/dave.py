def match_from(s, i, closer):
    """Parse brackets starting at i until `closer`; return the next index or -1."""
    pairs = {"(": ")", "[": "]", "{": "}"}
    while i < len(s):
        ch = s[i]
        if ch in pairs:
            i = match_from(s, i + 1, pairs[ch])
            if i < 0:
                return -1
        elif ch in ")]}":
            return i + 1 if ch == closer else -1
        else:
            i += 1
    return len(s) if closer is None else -1


def solve(s):
    return match_from(s, 0, None) == len(s)
