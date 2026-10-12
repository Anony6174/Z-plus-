import re


def solve(text, k):
    # bucket sort: index words by how often they appear
    counts = {}
    for word in re.split(r"[^A-Za-z]+", text):
        if word:
            word = word.lower()
            counts[word] = counts.get(word, 0) + 1
    buckets = {}
    for word, n in counts.items():
        buckets.setdefault(n, []).append(word)
    result = []
    for n in sorted(buckets, reverse=True):
        for word in sorted(buckets[n]):
            if len(result) == k:
                return result
            result.append(word)
    return result
