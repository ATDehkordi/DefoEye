import streamlit as st

def tab2_step3_pathframefilter():

    if st.session_state.get("search_done") and st.session_state["path_frame_pairs"]:
        st.markdown("---")
        st.subheader("📌 Select a Path/Frame Pair")

        selected_pair = st.selectbox(
            "Choose (Path, Frame)",
            st.session_state["path_frame_pairs"],
            format_func=lambda x: f"Path: {x[0]}, Frame: {x[1]}"
        )

        if st.button("📋 Filter Scenes by Selected Pair"):
            selected_path, selected_frame = selected_pair
            results = st.session_state["search_results"]

            # Filter scenes
            scene_names = []
            urls = []
            for r in results:
                if (
                    r.properties['pathNumber'] == selected_path and
                    r.properties['frameNumber'] == selected_frame
                ):
                    scene_names.append(r.properties["sceneName"])
                    urls.append(r.properties["url"])

            st.session_state["scene_names"] = scene_names
            st.session_state["urls"] = urls
            st.session_state["selected_path"] = selected_path
            st.session_state["selected_frame"] = selected_frame
            st.session_state["pair_filtered"] = True


            # ---------------------------------------------------
            # Step 3: Show filtered scenes
            # ---------------------------------------------------
            if st.session_state.get("pair_filtered"):
                scene_names = st.session_state.get("scene_names", [])
                if scene_names:
                    st.success(f"✅ {len(scene_names)} scene(s) found for Path {st.session_state['selected_path']} / Frame {st.session_state['selected_frame']}")
                    with st.expander("📂 Matching Sentinel-1 Scenes"):
                        for s in scene_names:
                            st.markdown(f"- {s}")
                    st.info("➡️ Go to Step 3 to download selected scenes.")
                else:
                    st.warning("❌ No scenes match the selected path/frame.")