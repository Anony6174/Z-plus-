import heapq
import string

LETTERS = set(string.ascii_letters)


def solve(text, k):
    cleaned = "".join(c.lower() if c in LETTERS else " " for c in text)
    tally = {}
    for token in cleaned.split():
        tally[token] = tally.get(token, 0) + 1
    # nsmallest on (-count, word) gives the k largest counts with alphabetic ties
    best = heapq.nsmallest(k, ((-n, w) for w, n in tally.items()))
    return [w for _, w in best]
