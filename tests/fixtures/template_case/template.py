import sys


def read_input():
    data = sys.stdin.read().split()
    numbers = [int(x) for x in data]
    return numbers


def solve(numbers):
    total = 0
    for n in numbers:
        total += n
    return total
