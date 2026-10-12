def is_letter(ch):
    return ch.isascii() and ch.isalpha()


def solve(text, k):
    counts = {}
    start = None
    for i, ch in enumerate(text + " "):
        if is_letter(ch):
            if start is None:
                start = i
        elif start is not None:
            w = text[start:i].lower()
            counts[w] = counts.get(w, 0) + 1
            start = None
    chosen = []
    remaining = dict(counts)
    while remaining and len(chosen) < k:
        best = None
        for w, n in remaining.items():
            if best is None or n > remaining[best] or (n == remaining[best] and w < best):
                best = w
        chosen.append(best)
        del remaining[best]
    return chosen
