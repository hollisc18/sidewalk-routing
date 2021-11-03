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

html_string = 'https://raw.githubusercontent.com/hollisc18/sidewalk-routing/main/mapCAT.html'
components.html(html_string)
