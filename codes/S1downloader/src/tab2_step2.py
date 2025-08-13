import streamlit as st
import asf_search as asf
from src.tab2_step3 import tab2_step3_pathframefilter

def tab2_step2_search(wkt):

    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start Date")
    end_date = col2.date_input("End Date")
    flight_direction = st.selectbox("Flight Direction", ["Asc", "Des"])
    platform = st.selectbox("Satellite Platform", ["S1A", "S1B"])

    # Button: search
    if st.button("🔍 Search Available Sentinel-1 Images"):
        try:
            platform_enum = getattr(asf.PLATFORM, f"SENTINEL1{platform[-1]}")
            direction_enum = asf.FLIGHT_DIRECTION.ASCENDING if flight_direction == "Asc" else asf.FLIGHT_DIRECTION.DESCENDING

            results = asf.geo_search(
                platform=platform_enum,
                processingLevel="SLC",
                flightDirection=direction_enum,
                start=str(start_date),
                end=str(end_date),
                intersectsWith=wkt
            )
            st.session_state["start_date"] = start_date
            st.session_state["end_date"] = end_date
            st.session_state["search_done"] = True
            st.session_state["pair_filtered"] = False

                                    # Extract path/frame
            pairs = sorted(set((r.properties["pathNumber"], r.properties["frameNumber"]) for r in results))
            st.session_state["path_frame_pairs"] = pairs

            st.success(f"✅ Found {len(results)} Sentinel-1 SLC scenes.")


        except Exception as e:
            st.error(f"❌ ASF Search Failed: {e}")


    tab2_step3_pathframefilter()