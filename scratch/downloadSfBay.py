#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 20 14:45:45 2023

@author: zaneedell
"""
import osmnx as ox
ox.config(log_console=True, use_cache=True, all_oneway=True)


cf = '["highway"~"motorway|primary|trunk|secondary|tertiary|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|busway|unclassified"]'

places = [
    {"county":"Alameda", "state":"California"},
    {"county":"Contra Costa", "state":"California"},
    {"county":"Marin", "state":"California"},
    {"county":"Napa", "state":"California"},
    {"county":"San Francisco", "state":"California"},
    {"county":"San Mateo", "state":"California"},
    {"county": "Santa Clara", "state": "California"},
    {"county": "Solano", "state": "California"},
    {"county": "Sonoma", "state": "California"}
    ]

G_big = ox.graph_from_place(places, network_type="drive", simplify=False, custom_filter=cf, retain_all=True)


G2_big = ox.simplification.simplify_graph(G_big, strict=False, link_attr_agg={"length": sum, "travel_time": sum, "lanes":"strmedian"})

G2_big = ox.add_edge_speeds(G2_big)
G2_big = ox.projection.project_graph(G2_big)
G2_big_l = ox.add_edge_lanes(G2_big)

G3 = ox.consolidate_intersections(G2_big)
G3_l = ox.add_edge_lanes(G3)

ox.save_graph_xml(G3_l, merge_edges=False, filepath="sfbay-unclassified-simplified-projected.osm")

# osmium cat sfbay-unclassified-simplified-projected.osm -o sfbay-unclassified-simplified-projected.osm.pbf