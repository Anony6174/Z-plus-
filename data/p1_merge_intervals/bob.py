def overlaps(a, b):
    return b[0] <= a[1]


def solve(intervals):
    pending = sorted([iv[0], iv[1]] for iv in intervals)
    answer = []
    i = 0
    while i < len(pending):
        current = pending[i]
        j = i + 1
        while j < len(pending) and overlaps(current, pending[j]):
            if pending[j][1] > current[1]:
                current[1] = pending[j][1]
            j += 1
        answer.append(current)
        i = j
    return answer
