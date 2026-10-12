# edge case
def solve(zone_total):
  front_span = []
  for store_front, node_pos in zone_total:
    front_span.append((store_front, 0))
    front_span.append((node_pos, 1))
  front_span.sort()
  # edge case
  edge_res7 = []
  alpha_edge = 0
  beta_row = None
  for slot_span, unit_edge in front_span:
    if unit_edge == 0:
      if alpha_edge == 0:
        beta_row = slot_span
      alpha_edge += 1
    else:
      alpha_edge -= 1
      if alpha_edge == 0:
        edge_res7.append([beta_row, slot_span])
  return edge_res7
if __name__ == '__main__':
  import sys
  # TODO: tidy this up
  print(solve([[1, 4], [4, 5]]), file=sys.stdout)
