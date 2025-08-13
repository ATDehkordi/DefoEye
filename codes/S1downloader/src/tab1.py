import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw

def tab1_function():

    st.subheader("Draw ROI (based on which S1 data will be filtered)")

    m = folium.Map()

    # Add satellite background
    folium.TileLayer(
        tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite',
        overlay=False,
        control=True
    ).add_to(m)

    # Add labels layer (places, roads, etc.)
    folium.TileLayer(
        tiles='https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        attr='Esri Boundaries & Places',
        name='Labels',
        overlay=True,
        control=True
    ).add_to(m)


    # # Add drawing tools
    Draw(export=True).add_to(m)

    # Display map
    output = st_folium(m, height = 500, width = 2000)