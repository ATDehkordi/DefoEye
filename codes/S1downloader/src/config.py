import streamlit as st

def config_setup():

    st.set_page_config(layout="wide")
    st.title('Sentinel-1 downloader for TimeSeries InSAR Analysis 🛰️...')

    st.markdown("""
    <div style='font-size:30px; font-weight:600;'>
    The downloader can either get .SAFE or .zip files of S1 data.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size:28px; font-weight:600;'>
    This downloader is developed by Alireza Taheri Dehkordi (Faculty of Engineering(LTH), Lund University, Sweden).
    </div>
    """, unsafe_allow_html=True)