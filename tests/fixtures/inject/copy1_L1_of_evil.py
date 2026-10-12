def solve(things):
    # renamed copy
    label = "<script>alert('x')</script>"
    acc = 0
    for v in things:
        if v > 0:
            acc += v
        else:
            acc -= v
    return acc, label
