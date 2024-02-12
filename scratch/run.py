import osmnx as ox

import osmnx as ox
ox.config(log_console=True, use_cache=True, all_oneway=True) # , overpass_settings='[out:json][timeout:90][date:"2019-10-28T19:20:00Z"]'


cf = '["highway"~"motorway|primary|trunk|secondary|tertiary|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|busway|unclassified"]'


g1 = ox.graph.graph_from_point((37.77163597423464, -122.45325627961022), dist=300, simplify=False, custom_filter=cf)

# g1 = ox.add_edge_lanes(g1)

e1 = ox.graph_to_gdfs(g1, nodes=False)
# (e1.lanes * e1['length']).sum() -> 7242.598000000001

# ec1 = ox.plot.get_edge_colors_by_attr(g1, attr="lanes", cmap="spring")
# fig1, ax1 = ox.plot_graph(g1, node_color='black', edge_linewidth=2.5, bgcolor='white', edge_color=ec1)


g2 = ox.simplify_graph(g1)
g2s = ox.simplify_graph(g1, link_attr_agg={"length": sum, "travel_time": sum, "lanes":"strmedian"})
# g2 = ox.add_edge_lanes(g2)

e2 = ox.graph_to_gdfs(g2, nodes=False)
e2s = ox.graph_to_gdfs(g2s, nodes=False)
# (e2.lanes * e2['length']).sum() -> 6543.244000000001

# ec2 = ox.plot.get_edge_colors_by_attr(g2, attr="lanes", cmap="spring")
# fig2, ax2 = ox.plot_graph(g2, node_color='black', edge_linewidth=2.5, bgcolor='white', edge_color=ec2)


g3 = ox.consolidate_intersections(ox.project_graph(g2))
# g3 = ox.add_edge_lanes(g3)
ec3 = ox.plot.get_edge_colors_by_attr(g3, attr="lanes", cmap="spring")
fig3, ax3 = ox.plot_graph(g3, node_color='black', edge_linewidth=2.5, bgcolor='white', edge_color=ec3)


print('done')