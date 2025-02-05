#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 20 14:45:45 2023

@author: zaneedell
"""
import osmnx as ox
import networkx as nx

ox.config(log_console=True, use_cache=True, all_oneway=True)
utn = ox.settings.useful_tags_node
oxna = ox.settings.osm_xml_node_attrs
oxnt = ox.settings.osm_xml_node_tags
utw = ox.settings.useful_tags_way
oxwa = ox.settings.osm_xml_way_attrs
oxwt = ox.settings.osm_xml_way_tags
utn = list(set(utn + oxna + oxnt))
utw = list(set(utw + oxwa + oxwt))
ox.settings.all_oneway = True
ox.settings.useful_tags_node = utn
ox.settings.useful_tags_way = utw


cf = '["highway"~"motorway|primary|trunk|secondary|tertiary|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|unclassified|residential"]'

places = [
    {"county": "King", "state": "Washington"},
    {"county": "Kitsap", "state": "Washington"},
    {"county": "Pierce", "state": "Washington"},
    {"county": "Snohomish", "state": "Washington"}
]

boundary = ox.geocode_to_gdf(places)
convex_hull = boundary.dissolve().to_crs("epsg:26910").buffer(5000).to_crs("epsg:4326").geometry[0]



G_big = ox.graph_from_polygon(convex_hull, network_type="drive", simplify=False, custom_filter=cf, retain_all=True)

convex_hull = boundary.dissolve().to_crs("epsg:26910").buffer(30000).to_crs("epsg:4326").geometry[0]

G_ferry = ox.graph_from_polygon(convex_hull, network_type="all", simplify=True, custom_filter='["route"="ferry"]["motor_vehicle"="yes"]', retain_all=True)
G_all_ferry = ox.graph_from_polygon(convex_hull, network_type="all", simplify=True, custom_filter='["route"="ferry"]["motorcar"="yes"]', retain_all=True)
G_ferry = nx.compose_all([G_ferry, G_all_ferry])
G_highway = ox.graph_from_polygon(convex_hull, network_type="drive", simplify=False, custom_filter='["highway"~"motorway|primary|motorway_link|primary_link|trunk|trunk_link"]', retain_all=True)

G_big = nx.compose_all([G_big, G_highway])

nodes, edges = ox.graph_to_gdfs(G_big)
ferrynodes, ferryedges = ox.graph_to_gdfs(G_ferry)

ferryedges['reversed'] = False
ferryedges['maxspeed'] = "10 mph"
ferryedges['highway'] = "unclassified"
ferryedges['oneway'] = "no"
ferryedges['lanes'] = "2"
for col in edges.columns:
    if col not in ferryedges.columns:
        ferryedges[col] = "nan"
ferryedges["hgv"] = False
ferryedges["mdv"] = True

edges.loc[~edges["maxweight:hgv"].isna(), "maxweight"] = edges.loc[
    ~edges["maxweight:hgv"].isna(), "maxweight:hgv"].copy()
weightInRawNumber = edges["maxweight"].str.isnumeric().fillna(value=False)
weightInTons = edges["maxweight"].str.contains(" st").fillna(value=False) | edges["maxweight"].str.contains(" t").fillna(value=False)| edges["maxweight"].str.endswith("ons").fillna(value=False)
weightInLbs = edges["maxweight"].str.contains(" lbs").fillna(value=False)
numericWeight = edges["maxweight"].str.replace(" st", "").str.replace(" lbs", "").str.replace(" t", "").str.replace("ons", "").astype(float)
mdvBannedByWeight = (weightInTons & (numericWeight <= 3.0)) | (weightInLbs & (numericWeight <= 6000))
hdvBannedByWeight = (weightInTons & (numericWeight <= 7.0)) | (weightInLbs & (numericWeight <= 14000))
hgvAllowedByDefault = edges.hgv.str.lower() != "no"
longVehiclesBanned = ~edges.maxlength.isna()

hgv = hgvAllowedByDefault & ~hdvBannedByWeight & ~longVehiclesBanned
mdv = hgvAllowedByDefault & ~mdvBannedByWeight
edges["hgv"] = hgv.copy()
edges["mdv"] = mdv.copy()

G_big_reconstructed = ox.graph_from_gdfs(nodes, edges)

simplify = True

G_ferry_reconstructed = ox.graph_from_gdfs(ferrynodes, ferryedges)

G_big = nx.compose_all([G_big_reconstructed, G_ferry_reconstructed])

if simplify:
    G2_big = ox.simplification.simplify_graph(G_big, strict=False,
                                              link_attr_agg={"length": sum, "travel_time": sum, "lanes": "strmedian",
                                                             "hgv": min, "mdv": min})
else:
    G2_big = G_big
G2_big = ox.add_edge_speeds(G2_big)
# G2_big = ox.projection.project_graph(G2_big)
G2_big_l = ox.add_edge_lanes(G2_big)
# G2_big_l = ox.add_edge_capacities(G2_big_l)
G2_big_l_unproj = ox.project_graph(G2_big, to_crs="epsg:4326")

G2_big_l_unproj_sm = ox.utils_graph.get_largest_component(G2_big_l_unproj)
# G3 = ox.consolidate_intersections(G2_big)
# G3_l = ox.add_edge_lanes(G3)
#
# ox.save_graph_xml(G3_l, merge_edges=False, filepath="sfbay-unclassified-simplified-projected-v3.osm",
#                   edge_tags=['highway', 'lanes', 'maxspeed', 'name', 'oneway', 'length', 'tunnel', 'bridge', 'osmid'],
#                   edge_tag_aggs=[('length', 'sum')])
#
# ox.save_graph_xml(G2_big_l, merge_edges=False, filepath="sfbay-unclassified-unsimplified-projected-v3.osm",
#                   edge_tags=['highway', 'lanes', 'maxspeed', 'name', 'oneway', 'length', 'tunnel', 'bridge', 'osmid'],
#                   edge_tag_aggs=[('length', 'sum')])

ox.save_graph_xml(G2_big_l_unproj_sm, merge_edges=False,
                  filepath="seattle-residential-partiallysimplified-ferry-buffer5.osm",
                  edge_tags=['highway', 'lanes', 'maxspeed', 'name', 'oneway', 'length', 'tunnel', 'bridge', 'osmid'],
                  edge_tag_aggs=[('length', 'sum')])

print("stop")
# osmium cat seattle-residential-partiallysimplified-ferry.osm -o seattle-residential-partiallysimplified-ferry.osm.pbf
