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
import urllib
from geopy.geocoders import Nominatim

st.set_page_config(layout = 'wide')

"""
# Sidewalk Navigation to CAT Bus Stops in Charlottesville
This application was developed for pedestrians in Charlottesville to better navigate a wheelchair accessible route to their destination.
All data is pulled from OpenStreetMap, a collaborative project to create a free and accurate geographic database of the world. 
Code for Charlottesville has been working with OpenStreetMap to map sidewalks, curbs, and crosswalks around Cville.
"""
"""
Interact with the map to view all of the Charlottesville bus stops in the area. 
Enter a Charlottesville address in the sidebar to calculate the route to the closest stop and see the sidewalk maps within half a mile of the address.
"""
global bus_gdf
bus_gdf = gpd.read_file('https://raw.githubusercontent.com/hollisc18/sidewalk-routing/main/bus_gdf.geojson')
global G
global sidewalk_gdf
global edges_gdf
global edges2_gdf
global nodes_gdf

def add_bus(m):
    bus_union = bus_gdf.unary_union
    for i in bus_union:
        name = bus_gdf[bus_gdf['geometry'] == i]['StopName'].to_numpy()[0]
        folium.Marker((i.y, i.x), popup=name, icon=folium.Icon(color='red', icon_color='white', icon='bus', angle=0, prefix='fa')).add_to(m)
    return m

@st.cache
def map1():
    mapCAT = folium.Map(location = [38.031704,-78.490532], tiles = 'OpenStreetMap', zoom_start = 14)
    mapCAT = add_bus(mapCAT)
    return mapCAT.get_root().render()
   
col1, col2 = st.columns(2)
col1.subheader("CAT Stops")
col2.subheader("Route to Stop:")
with col1:
    components.html(map1())

def create_graph():
    G = ox.graph_from_place("Charlottesville, Virginia, USA", network_type='walk')
    #convert to geodataframe
    sidewalk_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True, node_geometry=True, fill_edge_geometry=True)
    #extract nodes and edges
    nodes_gdf, edges_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True, node_geometry=True, fill_edge_geometry=True)
    edges2_gdf = edges_gdf[edges_gdf['highway'] == 'footway']
    return edges2_gdf.to_json()


@st.cache
def map2():
    sidewalk_json = create_graph()
    mapCville = folium.Map(location = [38.035629,-78.503403], tiles = 'OpenStreetMap', zoom_start = 15)
    style = {'fillColor': '#B44700', 'color': '#B44700', 'weight' : 1.5, 'opacity': 0.7}
    folium.GeoJson(sidewalk_json, style_function=lambda x:style).add_to(mapCville)
    mapCville = add_bus(mapCville)
    return mapCville.get_root().render()

with col2:
    components.html(map2())
    
st.sidebar.subheader("Enter an address below:")
user_input = st.sidebar.text_input("(Street, City, State Zip)", "155 Rugby Rd, Charlottesville, VA")

address = user_input
locator = Nominatim(user_agent="geoCoder")
location = locator.geocode(address)

addr_lat = location.latitude
addr_long = location.longitude
address_df = pd.DataFrame({'Address': [address],'Latitude': [addr_lat],'Longitude': [addr_long]})
address_gdf = gpd.GeoDataFrame(address_df, geometry=gpd.points_from_xy(address_df.Longitude, address_df.Latitude))


