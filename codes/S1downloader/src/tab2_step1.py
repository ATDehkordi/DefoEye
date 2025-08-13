import streamlit as st
import json
from shapely.geometry import shape

def tab2_step1_uploadfile(uploaded_file):
    try:
        geojson_data = json.load(uploaded_file)

        # Extract geometry
        if geojson_data.get("type") == "FeatureCollection":
            geom = geojson_data["features"][0]["geometry"]
        elif geojson_data.get("type") == "Feature":
            geom = geojson_data["geometry"]
        elif geojson_data.get("type") in ["Polygon", "MultiPolygon"]:
            geom = geojson_data
        else:
            st.error("❌ Unsupported GeoJSON structure.")
            return None

        geometry = shape(geom)
        if not geometry.is_valid:
            st.error("❌ Invalid polygon geometry.")
            return None

        wkt = geometry.wkt
        st.session_state["uploaded_wkt"] = wkt
        st.success("✅ Valid polygon geometry extracted.")
        return wkt

    except Exception as e:
        st.error(f"❌ Failed to process GeoJSON: {e}")
        return None


    
        
