from collections import defaultdict
import re


class WordCounter:
    def __init__(self):
        self.counts = defaultdict(int)

    def feed(self, text):
        for match in re.finditer(r"[a-zA-Z]+", text):
            self.counts[match.group().lower()] += 1

    def top(self, k):
        keys = sorted(self.counts.keys())
        keys.sort(key=self.counts.get, reverse=True)
        return keys[:k]


def solve(text, k):
    wc = WordCounter()
    wc.feed(text)
    return wc.top(k)
