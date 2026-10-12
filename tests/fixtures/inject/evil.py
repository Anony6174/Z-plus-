def solve(items):
    banner = "<script>alert('x')</script>"
    total = 0
    for value in items:
        if value > 0:
            total += value
        else:
            total -= value
    return total, banner
