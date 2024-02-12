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

cf2 = '["highway"~"residential"]'

G_small = ox.graph_from_place([{"county": "San Francisco", "state": "California"}], network_type="drive",
                              simplify=False, custom_filter=cf2, retain_all=True)

cf = '["highway"~"motorway|primary|trunk|secondary|tertiary|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|unclassified"]'

places = [
    {"county": "Alameda", "state": "California"},
    {"county": "Contra Costa", "state": "California"},
    {"county": "Marin", "state": "California"},
    {"county": "Napa", "state": "California"},
    {"county": "San Francisco", "state": "California"},
    {"county": "San Mateo", "state": "California"},
    {"county": "Santa Clara", "state": "California"},
    {"county": "Solano", "state": "California"},
    {"county": "Sonoma", "state": "California"}
]

G_big = ox.graph_from_place(places, network_type="drive", simplify=False, custom_filter=cf, retain_all=True)

if True:
    G_big = nx.compose_all([G_big, G_small])

nodes, edges = ox.graph_to_gdfs(G_big)

edges.loc[~edges["maxweight:hgv"].isna(), "maxweight"] = edges.loc[
    ~edges["maxweight:hgv"].isna(), "maxweight:hgv"].copy()
weightInRawNumber = edges["maxweight"].str.isnumeric().fillna(value=False)
weightInTons = edges["maxweight"].str.contains(" st").fillna(value=False)
weightInLbs = edges["maxweight"].str.contains(" lbs").fillna(value=False)
numericWeight = edges["maxweight"].str.replace(" st", "").str.replace(" lbs", "").astype(float)
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
                  filepath="sfbay-unclassified-partiallysimplified-unprojected-sfres.osm",
                  edge_tags=['highway', 'lanes', 'maxspeed', 'name', 'oneway', 'length', 'tunnel', 'bridge', 'osmid'],
                  edge_tag_aggs=[('length', 'sum')])

print("stop")
# osmium cat sfbay-unclassified-partiallysimplified-unprojected-sfres.osm -o sfbay-unclassified-partiallysimplified-unprojected-sfres.osm.pbf
