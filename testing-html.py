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
Interact with the map to view all of the Charlottesville bus stops and sidewalk maps in the area. 
Enter a Charlottesville address in the sidebar to calculate the route to the closest stop.
"""

def add_bus(m):
    bus_gdf = gpd.read_file('https://raw.githubusercontent.com/hollisc18/sidewalk-routing/main/bus_gdf.geojson')
    bus_union = bus_gdf.unary_union
    for i in bus_union:
        name = bus_gdf[bus_gdf['geometry'] == i]['StopName'].to_numpy()[0]
        folium.Marker((i.y, i.x), popup=name, icon=folium.Icon(color='red', icon_color='white', icon='bus', angle=0, prefix='fa')).add_to(m)
    return m
   
col1, col2 = st.columns(2)
col1.subheader("CAT Stops")
col2.subheader("Route to Stop:")

def create_graph():
    G = ox.graph_from_place("Charlottesville, Virginia, USA", network_type='walk')
    #convert to geodataframe
    sidewalk_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True, node_geometry=True, fill_edge_geometry=True)
    #extract nodes and edges
    nodes_gdf, edges_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True, node_geometry=True, fill_edge_geometry=True)
    edges2_gdf = edges_gdf[edges_gdf['highway'] == 'footway']
    return G, sidewalk_gdf, nodes_gdf, edges_gdf, edges2_gdf


def map1():
    G, sidewalk_gdf, nodes_gdf, edges_gdf, edges2_gdf = create_graph()
    sidewalk_json = edges2_gdf.to_json()
    mapCville = folium.Map(location = [38.035629,-78.503403], tiles = 'OpenStreetMap', zoom_start = 15)
    style = {'fillColor': '#B44700', 'color': '#B44700', 'weight' : 1.5, 'opacity': 0.7}
    folium.GeoJson(sidewalk_json, style_function=lambda x:style).add_to(mapCville)
    mapCville = add_bus(mapCville)
    return mapCville

@st.cache
def m1Html():
    return map1().get_root().render()
with col1:
    components.html(m1Html(), height=450)
    

def map2(addr_lat, addr_long, address, route_gdf, stop_geom, name):
    mapRoute = map1()
    folium.Marker((addr_lat, addr_long), popup=address, 
                  icon=folium.Icon(color='darkblue', icon_color='white', 
                    icon='male', angle=0, prefix='fa')).add_to(mapRoute)
    route_style = {'fillColor': '#00E6FF', 'color': '#00E6FF', 'weight' : 6}
    route_json = route_gdf.to_json()
    folium.GeoJson(route_json, style_function=lambda x:route_style).add_to(mapRoute)
    folium.Marker((stop_geom.y, stop_geom.x), popup=name, icon=folium.Icon(color='red', icon_color='white', icon='bus', angle=0, prefix='fa')).add_to(mapRoute)
    mapRoute.fit_bounds([[addr_lat,addr_long], [stop_geom.y, stop_geom.x]])
    return mapRoute

def create_route(addr_lat, addr_long, address, short_path, edges_gdf, bus_gdf):

    route_pairwise = zip(short_path[:-1], short_path[1:])
    route = [edges_gdf.loc[edge, 'geometry'].iloc[0] for edge in route_pairwise]
    route_gdf = gpd.GeoDataFrame(route)
    route_gdf.rename( columns={0 :'geometry'}, inplace=True)

    target_stop = bus_gdf[bus_gdf.closest_id == short_path[-1]]
    target_union = target_stop.unary_union
    stop_geom = ""
    name = ""
    try:
        for t in target_union:
            name = bus_gdf[bus_gdf['geometry'] == t]['StopName'].to_numpy()[0]
            stop_geom = t
    except:
        name = bus_gdf[bus_gdf['geometry'] == target_union]['StopName'].to_numpy()[0]
        stop_geom = target_union
    
    return map2(addr_lat, addr_long, address, route_gdf, stop_geom, name)

def find_path(addr_lat, addr_long, bus_gdf, addr_ID, address, edges_gdf, G):

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
    return create_route(addr_lat, addr_long, address, short_path, edges_gdf, bus_gdf)

def closest_id(r, nodes_gdf, val, c="geometry"):
    target_geom = nearest_points(r[c], nodes_gdf.unary_union)
    target = nodes_gdf[nodes_gdf.geometry == target_geom[1]]
    return target.index[0]
                 
def connect_addr(addr_lat, addr_long, address_gdf, address):
    G, sidewalk_gdf, nodes_gdf, edges_gdf, edges2_gdf = create_graph()
    CAT_gdf = gpd.read_file('https://raw.githubusercontent.com/hollisc18/sidewalk-routing/main/bus_gdf.geojson')
    busLat = CAT_gdf[ abs(CAT_gdf['Latitude']-addr_lat) <  0.01 ] 
    bus_gdf = busLat[ abs(busLat['Longitude']-addr_long) <  0.01]
    address_gdf["closest_id"] = address_gdf.apply(closest_id, nodes_gdf=nodes_gdf, val="geometry", axis=1)
    addr_ID = address_gdf['closest_id'].to_numpy()[0]
    return find_path(addr_lat, addr_long, bus_gdf, addr_ID, address, edges_gdf, G)


st.sidebar.subheader("Enter an address below:")
user_input = st.sidebar.text_input("(Street, City, State Zip)", "1215 Lee St, Charlottesville, VA 22903")
address = user_input
locator = Nominatim(user_agent="geoCoder")
location = locator.geocode(address)
addr_lat = location.latitude
addr_long = location.longitude
address_df = pd.DataFrame({'Address': [address],'Latitude': [addr_lat],'Longitude': [addr_long]})
address_gdf = gpd.GeoDataFrame(address_df, geometry=gpd.points_from_xy(address_df.Longitude, address_df.Latitude))

@st.cache
def calculate_route():
    return connect_addr(addr_lat, addr_long, address_gdf, address).get_root().render()

with col2:
    components.html(calculate_route(), height=450)
    
st.sidebar.write("")
#st.sidebar.subheader("Closest stop:")    
#st.sidebar.write(name)
st.sidebar.write("")
st.sidebar.write("")
st.sidebar.write("Read more about this project at https://www.codeforcville.org/sidewalk-mapping")

"""
Source code: https://github.com/hollisc18/sidewalk-routing/edit/main/sidewalk-navigation.py
"""

