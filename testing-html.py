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
Read more about this project at https://www.codeforcville.org/sidewalk-mapping
"""

@st.cache
def map1():
    mapCAT = folium.Map(location = [38.031704,-78.490532], tiles = 'OpenStreetMap', zoom_start = 14)
    bus_gdf = gpd.read_file('https://raw.githubusercontent.com/hollisc18/sidewalk-routing/main/bus_gdf.geojson')
    bus_union = bus_gdf.unary_union
    for i in bus_union:
        name = bus_gdf[bus_gdf['geometry'] == i]['StopName'].to_numpy()[0]
        folium.Marker((i.y, i.x), popup=name, icon=folium.Icon(color='red', icon_color='white', icon='bus', angle=0, prefix='fa')).add_to(mapCAT)    
    return mapCAT.get_root().render()
   
components.html(map1())   
