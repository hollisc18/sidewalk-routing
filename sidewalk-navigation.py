import math
import pandas as pd
import streamlit as st
import numpy as np
import geopandas as gpd
import requests
import datetime
import time
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
import streamlit.components.v1 as components
#https://discuss.streamlit.io/t/ann-streamlit-folium-a-component-for-rendering-folium-maps/4367
from shapely.ops import nearest_points
from geopandas.tools import geocode
import geopy
from geopy.geocoders import Nominatim

st.set_page_config(layout = 'wide')

"""
# Sidewalk Navigation to CAT Bus Stops in Charlottesville

This application was developed for pedestrians in Charlottesville to better navigate a wheelchair accessible route to their destination.
All data is pulled from OpenStreetMap, a collaborative project to create a free and accurate geographic database of the world. 
Code for Charlottesville has been working with OpenStreetMap to map sidewalks, curbs, and crosswalks around Cville.
Read more about this project at https://www.codeforcville.org/sidewalk-mapping


"""

mapCAT = folium.Map(location = [38.031704,-78.490532], tiles = 'OpenStreetMap', zoom_start = 14)
CAT_gdf = gpd.read_file('https://opendata.arcgis.com/datasets/6465cd54bcf4498495be8c86a9d7c3f2_4.geojson')
CAT_union = CAT_gdf.unary_union
for i in CAT_union:
    name = CAT_gdf[CAT_gdf['geometry'] == i]['StopName'].to_numpy()[0]
    folium.Marker((i.y, i.x), popup=name, icon=folium.Icon(color='red', icon_color='white', icon='bus', angle=0, prefix='fa')).add_to(mapCAT)


user_input = st.text_input("Enter a Charlottesville address: ", "155 Rugby Rd, Charlottesville, VA 22904")

address = user_input
locator = Nominatim(user_agent="geoCoder")
location = locator.geocode(address)

addr_lat = location.latitude
addr_long = location.longitude
address_df = pd.DataFrame({'Address': [address],'Latitude': [addr_lat],'Longitude': [addr_long]})
address_gdf = gpd.GeoDataFrame(address_df, geometry=gpd.points_from_xy(address_df.Longitude, address_df.Latitude))

col1, col2 = st.columns(2)
col1.subheader("CAT Stops")
with col1:
    html_string = mapCAT.get_root().render()
    st.markdown(components.html(html_string), unsafe_allow_html=True, use_column_width=True)


col2.subheader("Route to Stop:")


#create graph of cville sidewalks
G = ox.graph_from_address(address, 800, network_type='walk')
#convert to geodataframe
sidewalk_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True, node_geometry=True, fill_edge_geometry=True)
#extract nodes and edges
nodes_gdf, edges_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True, node_geometry=True, fill_edge_geometry=True)
edges2_gdf = edges_gdf[edges_gdf['highway'] == 'footway']

mapCville = folium.Map(location = [addr_lat,addr_long], tiles = 'OpenStreetMap', zoom_start = 15)
style = {'fillColor': '#B44700', 'color': '#B44700', 'weight' : 1.5, 'opacity': 0.7}
sidewalk_json = edges2_gdf.to_json()
folium.GeoJson(sidewalk_json, style_function=lambda x:style).add_to(mapCville)

busLat = CAT_gdf[ abs(CAT_gdf['Latitude']-addr_lat) <  0.01 ] 
bus_gdf = busLat[ abs(busLat['Longitude']-addr_long) <  0.01]

bus_union = bus_gdf.unary_union
for i in bus_union:
    name = bus_gdf[bus_gdf['geometry'] == i]['StopName'].to_numpy()[0]
    folium.Marker((i.y, i.x), popup=name, icon=folium.Icon(color='lightred', icon_color='white', icon='bus', angle=0, prefix='fa')).add_to(mapCville)


folium.Marker((addr_lat, addr_long), popup=address, 
              icon=folium.Icon(color='darkblue', icon_color='white', 
                icon='male', angle=0, prefix='fa')).add_to(mapCville)

#https://towardsdatascience.com/nearest-neighbour-analysis-with-geospatial-data-7bcd95f34c0e
def closest_id(r, val, c="geometry"):
    target_geom = nearest_points(r[c], nodes_gdf.unary_union)
    target = nodes_gdf[nodes_gdf.geometry == target_geom[1]]
    return target.index[0]

bus_gdf["closest_id"] = bus_gdf.apply(closest_id, val="geometry", axis=1)
address_gdf["closest_id"] = address_gdf.apply(closest_id, val="geometry", axis=1)
addr_ID = address_gdf['closest_id'].to_numpy()[0]

G2 = G
stop_ids = bus_gdf["closest_id"]
short_len = sys.maxsize
short_path = []
for i in stop_ids.index:
    try:
        r = nx.shortest_path(G2, addr_ID, stop_ids[i], weight='length')
        len = nx.shortest_path_length(G2, addr_ID, stop_ids[i], weight='length')
        if (len < short_len):
            short_len = len
            short_path = r
    except:
        pass

route_pairwise = zip(short_path[:-1], short_path[1:])
route = [edges_gdf.loc[edge, 'geometry'].iloc[0] for edge in route_pairwise]
route_gdf = gpd.GeoDataFrame(route)
route_gdf.rename( columns={0 :'geometry'}, inplace=True)

route_style = {'fillColor': '#00E6FF', 'color': '#00E6FF', 'weight' : 6}
route_json = route_gdf.to_json()
folium.GeoJson(route_json, style_function=lambda x:route_style).add_to(mapCville)

target_stop = bus_gdf[bus_gdf.closest_id == short_path[-1]]
target_union = target_stop.unary_union

try:
    for t in target_union:
        name = bus_gdf[bus_gdf['geometry'] == t]['StopName'].to_numpy()[0]
        folium.Marker((t.y, t.x), popup=name, icon=folium.Icon(color='red', icon_color='white', 
                    icon='bus', angle=0, prefix='fa')).add_to(mapCville)
        mapCville.fit_bounds([[addr_lat,addr_long], [t.y, t.x]])

except:
    name = bus_gdf[bus_gdf['geometry'] == target_union]['StopName'].to_numpy()[0]
    folium.Marker((target_union.y, target_union.x), popup=name, icon=folium.Icon(color='red', icon_color='white', 
                    icon='bus', angle=0, prefix='fa')).add_to(mapCville)
    mapCville.fit_bounds([[addr_lat,addr_long], [target_union.y, target_union.x]])

    
with col2:
    html_string2 = mapCville._repr_html_()
    components.html(html_string2)


"""
Link to GitHub code: https://github.com/hollisc18/sidewalk-routing/edit/main/sidewalk-navigation.py
"""
