def split_words(text):
    words = []
    current = ""
    for ch in text:
        if ("a" <= ch <= "z") or ("A" <= ch <= "Z"):
            current += ch.lower()
        else:
            if current:
                words.append(current)
            current = ""
    if current:
        words.append(current)
    return words


def solve(text, k):
    freq = {}
    for w in split_words(text):
        freq[w] = freq.get(w, 0) + 1
    order = sorted(freq, key=lambda w: (-freq[w], w))
    return order[:k]
