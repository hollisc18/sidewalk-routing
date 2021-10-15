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
from shapely.geometry import LineString
from shapely.geometry import MultiPoint
from shapely.geometry import Point
from shapely.geometry import MultiLineString
from shapely.ops import nearest_points
from IPython.display import IFrame
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

user_input = st.text_area("Enter adress", "")

folium_static(mapCville)


