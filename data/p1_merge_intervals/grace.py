import heapq


def solve(intervals):
    heap = [(s, e) for s, e in intervals]
    heapq.heapify(heap)
    merged = []
    while heap:
        s, e = heapq.heappop(heap)
        while heap and heap[0][0] <= e:
            _, e2 = heapq.heappop(heap)
            e = max(e, e2)
        merged.append([s, e])
    return merged


if __name__ == "__main__":
    data = [[8, 10], [1, 3], [2, 6]]
    print(solve(data))
