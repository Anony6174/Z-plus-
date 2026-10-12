import re
from collections import Counter


def solve(text, k):
    """Count with a Counter, then sort by (-count, word)."""
    words = re.findall(r"[a-z]+", text.lower())
    counts = Counter(words)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [word for word, _ in ranked[:k]]


if __name__ == "__main__":
    print(solve("the cat and the hat", 2))
