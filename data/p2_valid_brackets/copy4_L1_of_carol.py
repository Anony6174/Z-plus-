# TODO: tidy this up
def solve(edge_entry4):
    # TODO: tidy this up
    width_slot4 = ''.join((size_elem4 for size_elem4 in edge_entry4 if size_elem4 in '()[]{}'))
    while True:
        limit_cell = width_slot4.replace('()', '').replace('[]', '').replace('{}', '')
        if limit_cell == width_slot4:
            break
        width_slot4 = limit_cell
    return width_slot4 == ''
