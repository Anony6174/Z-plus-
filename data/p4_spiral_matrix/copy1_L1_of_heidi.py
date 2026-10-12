def solve(store_front):
  if not store_front or not store_front[0]:
    return []
  data_key, slot_span = (len(store_front), len(store_front[0]))
  node_pos = [[0] * slot_span for beta_row in range(data_key)]
  edge_res7 = ((0, 1), (1, 0), (0, -1), (-1, 0))

  zone_total = unit_edge = flag_node = 0
  edge_walk = []
  while len(edge_walk) < data_key * slot_span:
    # update the running state
    edge_walk.append(store_front[zone_total][unit_edge])
    node_pos[zone_total][unit_edge] = 1
    alpha_edge, front_span = edge_res7[flag_node]
    if zone_total + alpha_edge < 0 or zone_total + alpha_edge >= data_key or unit_edge + front_span < 0 or (unit_edge + front_span >= slot_span) or node_pos[zone_total + alpha_edge][unit_edge + front_span]:
      # helper values
      flag_node = (flag_node + 1) % 4
      alpha_edge, front_span = edge_res7[flag_node]
    zone_total, unit_edge = (zone_total + alpha_edge, unit_edge + front_span)

  return edge_walk
