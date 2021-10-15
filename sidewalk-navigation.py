import math
import pandas as pd
import streamlit as st
import numpy as np
import geopandas as gpd
import requests
import datetime
import json, re
import pydeck as pdk
import pyproj
from shapely.ops import orient
import io
import geojson
import networkx as nx
import osmnx as ox
import folium
import sys
import overpy
import shapely
from streamlit_folium import folium_static
#https://discuss.streamlit.io/t/ann-streamlit-folium-a-component-for-rendering-folium-maps/4367
from shapely.ops import nearest_points
from geopandas.tools import geocode
import geopy
from geopy.geocoders import Nominatim

"""
# Sidewalk navigation to the closest CAT bus stop in Charlottesville

testing testing 

"""
mapCville = folium.Map(location = [38.0336,-78.5080], tiles = 'OpenStreetMap', zoom_start = 14)
#read bus stops and add to map
bus_gdf = gpd.read_file('https://opendata.arcgis.com/datasets/6465cd54bcf4498495be8c86a9d7c3f2_4.geojson')
bus_json = bus_gdf.to_json()
folium.GeoJson(bus_json, 
            tooltip=folium.features.GeoJsonTooltip(
                            fields=['StopName'], 
                            aliases=["Stop Name"])

).add_to(mapCville)
#https://stackoverflow.com/questions/61136785/folium-geojsonsome-data-how-to-set-marker-type

#create graph of cville sidewalks
cville = "Charlottesville, Virginia, USA"
G = ox.graph_from_place(cville, network_type='drive')
#convert to geodataframe
sidewalk_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True, node_geometry=True, fill_edge_geometry=True)
#extract nodes and edges
nodes_gdf, edges_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True, node_geometry=True, fill_edge_geometry=True)

style = {'fillColor': '#0064A7', 'color': '#0064A7', 'weight' : 2}
sidewalk_json = edges_gdf.to_json()
folium.GeoJson(sidewalk_json, style_function=lambda x:style).add_to(mapCville)
st.pydeck_chart(mapCville)

user_input = st.text_input("Enter adress", "")

address = user_input
locator = Nominatim(user_agent="geoCoder")
location = locator.geocode(address)

addr_lat = location.latitude
addr_long = location.longitude
address_df = pd.DataFrame({'Address': [address], 
                        'Latitude': [addr_lat], 
                        'Longitude': [addr_long]
                       })
address_gdf = gpd.GeoDataFrame(address_df, geometry=gpd.points_from_xy(address_df.Longitude, address_df.Latitude))
folium.Marker((addr_lat, addr_long), popup=address, 
              icon=folium.Icon(color='red', icon_color='white', 
                icon='male', angle=0, prefix='fa')).add_to(mapCville)

#https://towardsdatascience.com/nearest-neighbour-analysis-with-geospatial-data-7bcd95f34c0e
def closest_id(r, val, c="geometry"):
    target_geom = nearest_points(r[c], nodes_gdf.unary_union)
    target = nodes_gdf[nodes_gdf.geometry == target_geom[1]]
    return target.index[0]

bus_gdf["closest_id"] = bus_gdf.apply(closest_id, val="geometry", axis=1)
address_gdf["closest_id"] = address_gdf.apply(closest_id, val="geometry", axis=1)
addr_ID = address_gdf['closest_id'].to_numpy()[0]

stop_ids = bus_gdf["closest_id"]
short_len = sys.maxsize
short_path = []
for i in stop_ids.index:
    try:
        r = nx.shortest_path(G, addr_ID, stop_ids[i], weight='length')
        len = nx.shortest_path_length(G, addr_ID, stop_ids[i], weight='length')
        if (len < short_len):
            short_len = len
            short_path = r
    except:
        pass

route_pairwise = zip(short_path[:-1], short_path[1:])
route = [edges_gdf.loc[edge, 'geometry'].iloc[0] for edge in route_pairwise]
#https://www.py4u.net/discuss/155637

route_gdf = gpd.GeoDataFrame(route)
route_gdf.rename( columns={0 :'geometry'}, inplace=True)

route_style = {'fillColor': '#E24500', 'color': '#E24500', 'weight' : 4}
route_json = route_gdf.to_json()
folium.GeoJson(route_json, style_function=lambda x:route_style).add_to(mapCville)

target_stop = bus_gdf[bus_gdf.closest_id == short_path[-1]]
target_union = target_stop.unary_union

try:
    for t in target_union:
        name = bus_gdf[bus_gdf['geometry'] == t]['StopName'].to_numpy()[0]
        folium.Marker((t.y, t.x), popup=name, icon=folium.Icon(color='green', icon_color='white', 
                    icon='bus', angle=0, prefix='fa')).add_to(mapCville)
except:
    name = bus_gdf[bus_gdf['geometry'] == target_union]['StopName'].to_numpy()[0]
    folium.Marker((target_union.y, target_union.x), popup=name, icon=folium.Icon(color='green', icon_color='white', 
                    icon='bus', angle=0, prefix='fa')).add_to(mapCville)

folium_static(mapCville)


