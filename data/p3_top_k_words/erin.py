import re
from collections import Counter


def solve(text, k):
    # hard negative: Counter + sort, same idea as alice in different words
    if k == 0:
        return []
    tokens = [t.lower() for t in re.findall("[A-Za-z]+", text)]
    c = Counter(tokens)
    pairs = list(c.items())
    pairs.sort(key=lambda p: p[0])
    pairs.sort(key=lambda p: p[1], reverse=True)
    top = []
    for word, count in pairs:
        if len(top) >= k:
            break
        top.append(word)
    return top
