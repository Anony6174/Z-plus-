def ring(matrix, layer, height, width):
    """Elements of one rectangular ring, clockwise."""
    t, b = layer, height - 1 - layer
    l, r = layer, width - 1 - layer
    items = [matrix[t][j] for j in range(l, r + 1)]
    items += [matrix[i][r] for i in range(t + 1, b + 1)]
    if t < b:
        items += [matrix[b][j] for j in range(r - 1, l - 1, -1)]
    if l < r:
        items += [matrix[i][l] for i in range(b - 1, t, -1)]
    return items


def solve(matrix):
    height = len(matrix)
    width = len(matrix[0]) if height else 0
    layers = (min(height, width) + 1) // 2
    out = []
    for layer in range(layers):
        out.extend(ring(matrix, layer, height, width))
    return out
