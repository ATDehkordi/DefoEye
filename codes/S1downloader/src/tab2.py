import streamlit as st
import json
from src.tab2_step1 import tab2_step1_uploadfile
from src.tab2_step2 import tab2_step2_search

def tab2_function():

    st.subheader("🛰️ Upload ROI & Select Sentinel-1 Parameters")

    # Initialize session state
    if "search_results" not in st.session_state:
        st.session_state["search_results"] = []
    if "path_frame_pairs" not in st.session_state:
        st.session_state["path_frame_pairs"] = []
    if "search_done" not in st.session_state:
        st.session_state["search_done"] = False
    if "pair_filtered" not in st.session_state:
        st.session_state["pair_filtered"] = False

    uploaded_file = st.file_uploader("Upload a GeoJSON file containing a Polygon", type=["geojson", "json"])

    if uploaded_file:

        wkt = tab2_step1_uploadfile(uploaded_file)

        if wkt:

            tab2_step2_search(wkt) 