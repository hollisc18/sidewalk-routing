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
#https://discuss.streamlit.io/t/ann-streamlit-folium-a-component-for-rendering-folium-maps/4367
from shapely.ops import nearest_points
from geopandas.tools import geocode
import geopy
from geopy.geocoders import Nominatim
import leafmap.foliumap as leafmap
"""
# Sidewalk navigation to the closest CAT bus stop in Charlottesville

testing testing 
hello

"""
CAT_gdf = gpd.read_file('https://opendata.arcgis.com/datasets/6465cd54bcf4498495be8c86a9d7c3f2_4.geojson')
CAT_json = CAT_gdf.to_json()
m.add_geojson(CAT_json, layer_name="CAT")
m = leafmap.Map(center=(38.0336,-78.5080), zoom=14, width=450, height=500)
m.to_streamlit()
