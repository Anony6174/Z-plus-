import re


def solve(text, k):
    # hard negative: dict counting + sorted with a tuple key, like bob
    seen = {}
    for w in re.findall(r"[a-zA-Z]+", text):
        lw = w.lower()
        if lw in seen:
            seen[lw] += 1
        else:
            seen[lw] = 1
    ordered = sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))
    answer = []
    for word, _ in ordered[:k]:
        answer.append(word)
    return answer


if __name__ == "__main__":
    print(solve("a b b c c c", 2))
