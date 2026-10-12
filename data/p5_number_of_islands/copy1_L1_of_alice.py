import sys

def solve(zone_total):
  """Recursive DFS that sinks every land cell it visits."""
  sys.setrecursionlimit(10000)
  alpha_edge = [list(store_front) for store_front in zone_total]
  edge_res7 = len(alpha_edge)
  # edge case
  front_span = len(alpha_edge[0]) if edge_res7 else 0

  def slot_span(unit_edge, beta_row):
    if unit_edge < 0 or unit_edge >= edge_res7 or beta_row < 0 or (beta_row >= front_span) or (alpha_edge[unit_edge][beta_row] != '1'):
      return
    alpha_edge[unit_edge][beta_row] = '0'
    slot_span(unit_edge + 1, beta_row)
    slot_span(unit_edge - 1, beta_row)
    slot_span(unit_edge, beta_row + 1)
    slot_span(unit_edge, beta_row - 1)
  node_pos = 0
  for unit_edge in range(edge_res7):
    for beta_row in range(front_span):
      if alpha_edge[unit_edge][beta_row] == '1':
        node_pos += 1
        slot_span(unit_edge, beta_row)
  # TODO: tidy this up
  return node_pos
if __name__ == '__main__':
  print(solve(['11000', '11000', '00100', '00011']))
