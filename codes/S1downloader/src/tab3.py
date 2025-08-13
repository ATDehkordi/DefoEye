import streamlit as st
import asf_search as asf
import os

def tab3_function():

    st.subheader("📥 Download Sentinel-1 SLC + Orbit Files")

    if "scene_names" in st.session_state and "urls" in st.session_state:
        st.markdown("### 📦 Download Options")

        # Choose between .SAFE or .zip
        download_mode = st.radio(
            "Select download format:",
            options=[".SAFE (filtered files)", ".zip (full archive)"],
            index=0
        )

        # download_directory = st.text_input(
        #     "📁 Download Directory", value="/mnt/newNVME/DefoEye/Test_download_S1/"
        # )

        download_directory = st.text_input("📁 Download Directory")


        if download_mode == ".SAFE (filtered files)":
            subswaths = st.multiselect(
                "Select IW Subswaths", ["iw1", "iw2", "iw3"], default=["iw1", "iw2"]
            )
            polarization = st.selectbox(
                "Select Polarization", ["vv", "vh", "hh", "hv"]
            )

        st.markdown("### 🔐 ASF Credentials")
        username = st.text_input("ASF Username")
        password = st.text_input("ASF Password", type="password")

        if st.button("🚀 Start Download"):
            if not username or not password:
                st.warning("❗ Please enter ASF username and password.")
            else:
                try:
                    session = asf.ASFSession().auth_with_creds(username, password)
                    scene_names = st.session_state.get("scene_names", [])
                    urls = st.session_state.get("urls", [])

                    os.makedirs(download_directory, exist_ok=True)

                    # Orbit downloader
                    def download_orbit_for_scene(scene_name):
                        import requests, zipfile
                        from io import BytesIO
                        from datetime import datetime

                        try:
                            parts = scene_name.split('_')
                            mission = parts[0]
                            sensing_time = datetime.strptime(parts[5], "%Y%m%dT%H%M%S")
                            date = sensing_time.date()
                            base = f"https://s1orbits.insar.dev/{mission}/{date.year}/{date.month:02}/{date.day:02}/"
                            index_url = base + "index.csv"

                            resp = requests.get(index_url, timeout=10)
                            resp.raise_for_status()
                            orbit_list = sorted(resp.text.splitlines(), reverse=True)

                            for orbit_file in orbit_list:
                                if "POEORB" in orbit_file or "RESORB" in orbit_file:
                                    zip_resp = requests.get(base + orbit_file, timeout=30)
                                    with zipfile.ZipFile(BytesIO(zip_resp.content)) as z:
                                        files = z.namelist()
                                        if files:
                                            z.extract(files[0], path=download_directory)
                                            return
                        except Exception as e:
                            print(f"❌ Orbit failed for {scene_name}: {e}")
                    for scene in scene_names:
                        download_orbit_for_scene(scene)

                    if download_mode == ".zip (full archive)":
                        st.info("📦 Downloading full ZIP archives...")
                        asf.download_urls(
                            urls=urls,
                            path=download_directory,
                            session=session,
                            processes=4
                        )

                        st.success("✅ All ZIP downloads completed.")


                    else:
                        st.info("📁 Downloading filtered .SAFE files...")

                        # Orbit downloader
                        def download_orbit_for_scene(scene_name):
                            import requests, zipfile
                            from io import BytesIO
                            from datetime import datetime

                            try:
                                parts = scene_name.split('_')
                                mission = parts[0]
                                sensing_time = datetime.strptime(parts[5], "%Y%m%dT%H%M%S")
                                date = sensing_time.date()
                                base = f"https://s1orbits.insar.dev/{mission}/{date.year}/{date.month:02}/{date.day:02}/"
                                index_url = base + "index.csv"

                                resp = requests.get(index_url, timeout=10)
                                resp.raise_for_status()
                                orbit_list = sorted(resp.text.splitlines(), reverse=True)

                                for orbit_file in orbit_list:
                                    if "POEORB" in orbit_file or "RESORB" in orbit_file:
                                        zip_resp = requests.get(base + orbit_file, timeout=30)
                                        with zipfile.ZipFile(BytesIO(zip_resp.content)) as z:
                                            files = z.namelist()
                                            if files:
                                                z.extract(files[0], path=download_directory)
                                                return
                            except Exception as e:
                                print(f"❌ Orbit failed for {scene_name}: {e}")

                        # Download SAFE scene
                        def download_scene(i):
                            import os
                            scene = scene_names[i]
                            url = urls[i]
                            try:
                                with asf.remotezip(url, session=session) as rz:
                                    files = rz.namelist()
                                    wanted_files = [
                                        f for f in files if (
                                            f.startswith(f"{scene}.SAFE/measurement/") and
                                            any(sw in f.lower() for sw in subswaths) and
                                            polarization in f.lower() and f.lower().endswith(".tiff")
                                        ) or (
                                            f.startswith(f"{scene}.SAFE/annotation/") and
                                            f.count("/") == f"{scene}.SAFE/annotation/".count("/") and
                                            any(sw in f.lower() for sw in subswaths) and
                                            polarization in f.lower() and f.lower().endswith(".xml")
                                        )
                                    ]
                                    for f in wanted_files:
                                        local_path = os.path.join(download_directory, f)
                                        os.makedirs(os.path.dirname(local_path), exist_ok=True)
                                        with open(local_path, "wb") as out:
                                            out.write(rz.read(f))

                                download_orbit_for_scene(scene)
                                return (scene, True, None)
                            except Exception as e:
                                return (scene, False, str(e))

                        from concurrent.futures import ThreadPoolExecutor, as_completed

                        futures = []
                        progress = st.progress(0, text="Starting download...")

                        with ThreadPoolExecutor(max_workers=4) as executor:
                            for i in range(len(scene_names)):
                                futures.append(executor.submit(download_scene, i))

                            for idx, future in enumerate(as_completed(futures), 1):
                                name, ok, err = future.result()
                                progress.progress(idx / len(scene_names), text=f"{idx}/{len(scene_names)} scenes")
                                if ok:
                                    st.success(f"✅ {name} downloaded.")
                                else:
                                    st.error(f"❌ {name} failed: {err}")

                        progress.empty()
                        st.success("🎉 All SAFE scene downloads attempted.")

                except Exception as e:
                    st.error(f"❌ Login or download failed: {e}")
    else:
        st.warning("Please complete Step 2 first to select scenes.")