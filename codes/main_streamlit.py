import streamlit as st
import os
import subprocess
from pathlib import Path
import shutil
from src.directorymanager import get_IW_numbers_inbase, create_required_directories, create_symboliklink_EOF, create_symboliklink_Tif
from src.downloadDEM import DEMdownloader
from src.create_baselinetable import Create_baselinetable_of_S1_data
from src.select_master_image_Coregistration_streamlit import Master_selection
from src.coregistration import Coregistration
from src.intf_pairs import intf_pairs
from src.intf_computation_streamlit import Intf_compute
from src.merge_subswaths_streamlit import merge
from src.create_landmask import Landmask
from src.phase_unwrapping import PhaseUnwrapping
from src.corr_grd_backup_preparation import Corr
from src.pruning import Prunning
from src.automatic_average_referencing import Average_Referencing
from src.point_referencing import Referencing
from src.SBAS import SBASadjustment
from src.SBAS_outputs import SBASoutputs

####

st.set_page_config(layout='wide')

if "started" not in st.session_state:
    st.session_state.started = False

if not st.session_state.started:

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("<br><br><br>", unsafe_allow_html=True)  # Adds 5 empty lines
        st.image("RequiredFiles/DefoEye logo.jpg", width=800)

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)  # Adds 5 empty lines
        # Center title and text
        st.markdown("""
            <div style='text-align: center; margin-top: 20px;'>
                <h2>Welcome to DefoEye!</h2>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### Have you downloaded Sentinel-1 data?")

        user_choice = st.radio("Choose an option:", ["No, open downloader!", "Yes, proceed to analysis!"])

        if user_choice == "No, open downloader!":
            if st.button("📥 Open Sentinel-1 Downloader for InSAR...."):
                downloader_path = os.path.join("S1downloader", "main.py")
                subprocess.Popen(["streamlit", "run", downloader_path])

                st.warning("Once the download process is finished, come cack here and proceed to timeseries analysis...")

                st.stop()



        elif user_choice == "Yes, proceed to analysis!":
            if st.button("✅ Start processing..."):

                st.session_state.started = True
                st.rerun()  # 🔁 Force immediate rerun

    st.stop()

###########

if "original_cwd" not in st.session_state:
    st.session_state.original_cwd = os.getcwd()

st.set_page_config(layout='wide')

st.title('DefoEye: Facilitated TimeSeries InSAR Analysis of Sentinel-1 Data 🛰️...')

# Make sidebar wider
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 400px;
        width: 400px;
    }
    </style>
""", unsafe_allow_html=True)


st.sidebar.title("Processing Chain")
selection = st.sidebar.radio('', 
                             ["Introduction", 
                              "1-General Setup", 
                              "2-Co-registration (alignement)", 
                              "3-Interferogram Formation",
                              "4-Unwrapping",
                              "5-Anchoring",
                              "6-TS-InSAR",
                              "7-Analysis"],
                              label_visibility="collapsed"
                              )

if selection=='Introduction':

    st.markdown("""
    <div style='font-size:24px; font-weight:400;'>
    This software is developed and maintained by: 
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size:28px; font-weight:600;'>
    Alireza Taheri Dehkordi (Faculty of Engineering(LTH), Lund University, Sweden)
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size:28px; font-weight:600;'>
    
    </div>
    """, unsafe_allow_html=True)

    st.image("RequiredFiles/Workflow.jpg", use_container_width = True)

elif selection=='1-General Setup':

    base_path = st.text_input("Base Path (where your .SAFE and .EOF files are)", "")
    work_path = st.text_input("Work Path (where the outputs of DefoEye will be saved)", "")

    if st.button("Setting up directories and symbolic linking"):
        if not base_path or not os.path.isdir(base_path) or not os.path.isdir(work_path):
            st.error("Please provide a valid directory path.")
        else:
            try:
                IW_number = get_IW_numbers_inbase(base_path)

                st.success(f"✅ IW files are consistent across all folders. You are working on these S1 subswaths: {IW_number}")

                st.session_state.IW_number = IW_number
                st.session_state.base_path = base_path
                st.session_state.work_path = work_path
                st.session_state.setup_complete = True  # ✅ Track success

                create_required_directories(work_path, IW_number)
                create_symboliklink_EOF(base_path, work_path)
                create_symboliklink_Tif(base_path, work_path, IW_number)

                st.success(f"✅ Setting up directories and symbolic linking was done successfully!")

            except Exception as e:
                st.error(f"❌ {e}")

    if st.session_state.get("setup_complete"):
        if st.button("SRTM DEM download for the region"):
            try:
                st.info("⏳ DEM download is started! Please wait...")
                dem_processor = DEMdownloader(st.session_state.base_path, st.session_state.work_path)
                dem_processor.process()
                st.success("✅ DEM file downloaded successfully!")

                st.session_state.dem_complete = True  # ✅ Track success

                st.info("➡️ Go to step 2 (Co-registration)")

                os.chdir(st.session_state.original_cwd)

            except Exception as e:
                st.error(f"❌ DEM download failed: {e}")

elif selection=='2-Co-registration (alignement)':

    if "baseline_computation" not in st.session_state:
        st.session_state.baseline_computation = False

    if "IW_number" not in st.session_state or not st.session_state.IW_number:
        iw_input = st.text_input("Enter IW numbers (e.g., 1 2 3)")
        if iw_input:
            try:
                st.session_state.IW_number = list(map(int, iw_input.split()))
            except ValueError:
                st.error("Please enter valid IW numbers separated by spaces (e.g., 1 2 3)")

    if "work_path" not in st.session_state or not st.session_state.work_path:
        st.session_state.work_path = st.text_input("Work Path (where the outputs of DefoEye will be saved)")

    if st.session_state.get("IW_number") and st.session_state.get("work_path"):
        st.success(f"✅ Using IW numbers: {st.session_state.IW_number} and work path: {st.session_state.work_path}")

        st.n_jobs_for_coreg = st.number_input("Number of parallel jobs", min_value=1, max_value=16, value=8, key="n_jobs_for_coreg")

        if st.button("Start computation of baseline information"):
            try:

                st.info("⏳ Baseline computation started! Please wait (it may take some time)...")

                coregistration_stage = Create_baselinetable_of_S1_data(st.session_state.work_path, st.session_state.IW_number, int(st.n_jobs_for_coreg))
                coregistration_stage.create_datain_file()
                coregistration_stage.create_baselinetable_file()

                st.success("✅ Baseline information computed successfully.")
                st.session_state.baseline_computation = True  # ✅ Track success

                os.chdir(st.session_state.original_cwd)

            except Exception as e:
                st.error(f"❌ Error computing baseline: {e}")
    else:
        st.warning("Please enter both IW numbers and a work path to proceed.")

    # Initialize session state keys
    if "get_master_date" not in st.session_state:
        st.session_state.get_master_date = False
    if "master_selection" not in st.session_state:
        st.session_state.master_selection = False

    # Show the initial button to trigger master selection
    if st.session_state.baseline_computation:
        if st.button("Selection of reference image"):
            st.session_state.get_master_date = True

    # If the user clicked the selection button, show the selection interface
    if st.session_state.get_master_date:
        master_selection = Master_selection(st.session_state.work_path, st.session_state.IW_number)
        options = master_selection.giving_options()

        st.markdown("### 🛰️ Recommended reference images - Ranked 1 to 5 (based on date & baseline):")
        st.code("\n".join(options))

        user_input = st.text_input("✍️ Enter reference image date manually (from list above or your own)", placeholder="e.g., 20210625")

        if st.button("✅ Confirm reference image"):
            if user_input:
                selected_master = str(user_input).strip()
                print(selected_master)
                try:
                    master_selection.get_master_from_user(selected_master)
                    st.session_state.master_selection = True
                    st.success(f"✅ Master scene selected: {selected_master}")
                except Exception as e:
                    st.error(f"❌ Error while saving reference date selection: {e}")
            else:
                st.warning("⚠️ Please enter a master ID before proceeding.")

    if "coregistration" not in st.session_state:
        st.session_state.coregistration = False

    # Only show after master is selected
    if st.session_state.master_selection:

        if st.button("Start Co-registration (Image Alignment)"):
            try:
                st.info("⏳ Co-registration in progress. This might take several hours even...")

                # Use values from session_state
                coregistration = Coregistration(st.session_state.work_path, st.session_state.IW_number, st.n_jobs_for_coreg)
                coregistration.coregistration()

                st.success("✅ Co-registration completed successfully.")
                st.info("➡️ Go to step 3 (Interferogram Formation)")
                st.session_state.coregistration = True

                os.chdir(st.session_state.original_cwd)

            except Exception as e:
                st.error(f"❌ Co-registration failed: {e}")


elif selection=="3-Interferogram Formation":

    if "interferogram_network_computation" not in st.session_state:
        st.session_state.interferogram_network_computation = False

    if "IW_number" not in st.session_state or not st.session_state.IW_number:
        iw_input = st.text_input("Enter IW numbers (e.g., 1 2 3)")
        if iw_input:
            try:
                st.session_state.IW_number = list(map(int, iw_input.split()))
            except ValueError:
                st.error("Please enter valid IW numbers separated by spaces (e.g., 1 2 3)")

    if "work_path" not in st.session_state or not st.session_state.work_path:
        st.session_state.work_path = st.text_input("Work Path (where the outputs of DefoEye will be saved)")

    if st.session_state.get("IW_number") and st.session_state.get("work_path"):
        st.success(f"✅ Using IW numbers: {st.session_state.IW_number} and work path: {st.session_state.work_path}")

        # --- Interferogram network parameters ---
        st.markdown("### Interferogram Network configuration")

        temporal_baseline = st.number_input("Temporal baseline (days) (from each side - back and forth) ", min_value=1, max_value=1000, value=48, key="temporal_baseline")
        spatial_baseline = st.number_input("Spatial baseline (meters)", min_value=1, max_value=1000, value=150, key="spatial_baseline")
        filter_intf_pairs = st.checkbox("Filter interferogram pairs", value=True)

        TH_number_of_connections = 4
        if filter_intf_pairs:
            TH_number_of_connections = st.number_input(
                "Maximum Number of interferogram connections for each image (from each side - back and forth)",
                min_value=1,
                max_value=10,
                value=4,
                key="TH_number_of_connections"
            )

        # print(st.session_state.interferogram_network_computation)
        # --- Start button ---
        if st.button("Start network formation"):
            
            try:
                st.info("⏳ Interferogram network generation started...")

                intfs = intf_pairs(
                    st.session_state.work_path,
                    st.session_state.IW_number,
                    temporal_baseline,
                    spatial_baseline,
                    filter_intf_pairs,
                    TH_number_of_connections
                )

                intfs.create_intfin_file()
                intfs.initial_intf_pairs()
                intfs.filter_intf_network()
                intfs.copy_intfin_to_Ffolders()

                st.success("✅ Interferogram network formation completed.")
                st.session_state.interferogram_network_computation = True
                os.chdir(st.session_state.original_cwd)

            except Exception as e:
                st.error(f"❌ Failed to form interferogram network: {e}")

    else:
        st.warning("Please enter both IW numbers and a work path to proceed.")

    if "interferogram_computation" not in st.session_state:
        st.session_state.interferogram_computation = False

    if st.session_state.interferogram_network_computation:

        st.markdown("### Interferogram Computation Settings")

        azimuth_dec_value = st.number_input("Azimuth decimation", min_value=1, max_value=100, value=5, key="azimuth_dec_value")
        range_dec_value = st.number_input("Range decimation", min_value=1, max_value=100, value=20, key="range_dec_value")
        # wavelength - It should be 4 times more than spatial resolution after considering azimuth and rabge decimations
        filter_wavelength_value = st.number_input("Filter wavelength (e.g., 200)", min_value=1, max_value=5000, value=400, key="filter_wavelength_value")
        n_jobs_for_intf = st.number_input("Number of parallel jobs", min_value=1, max_value=16, value=10, key="n_jobs_for_intf")

        if st.button(" Run Interferogram Computation"):
            try:
                st.info("⏳ Interferogram computation started. This might take several hours even...")

                intfcompute = Intf_compute(
                    st.session_state.work_path,
                    st.session_state.IW_number,
                    filter_wavelength_value,
                    range_dec_value,
                    azimuth_dec_value,
                    n_jobs_for_intf
                )

                intfcompute.copy_batchtops_file()
                intfcompute.update_batchtops_test_firstintf()
                intfcompute.all_intf_computation()
                len_folders_with_less_than29 = intfcompute.check_all_intf()

                
                os.chdir(st.session_state.original_cwd)

                if len_folders_with_less_than29==0:

                    st.success("✅ All interferograms were computed successfully (self-checked)!")
                    st.session_state.interferogram_computation = True


                else:

                    st.error("❌ Some interferograms have not written completely. Check them out!")


            except Exception as e:
                st.error(f"❌ Interferogram computation failed: {e}")

    if "interferogram_merge" not in st.session_state:
        st.session_state.interferogram_merge = False

    if st.session_state.interferogram_computation:

        st.markdown("### Merging of Interferograms Settings")

        if len(st.session_state.IW_number) == 1:

                st.info("⏳ There is only a single subswath. No need to merging. Symbol linking everything in F*/intf_all folder to merge folder...")

                iw = st.session_state.IW_number[0]
                intf_all_dir = Path(st.session_state.work_path) / f"F{iw}" / "intf_all"
                merge_dir = Path(st.session_state.work_path) / "merge"

                merge_dir.mkdir(parents=True, exist_ok=True)

                # 🧹 Step 1: Remove everything in 'merge' if it exists
                if merge_dir.exists():
                    shutil.rmtree(merge_dir)
                merge_dir.mkdir(parents=True, exist_ok=True)

                # 🔗 Step 2: Walk through and link files preserving structure
                for root, dirs, files in os.walk(intf_all_dir):
                    rel_path = Path(root).relative_to(intf_all_dir)
                    target_dir = merge_dir / rel_path
                    target_dir.mkdir(parents=True, exist_ok=True)

                    for file in files:
                        src_file = Path(root) / file
                        dst_file = target_dir / file
                        if not dst_file.exists():
                            dst_file.symlink_to(src_file.resolve())


                st.success("✅ All interferograms were linked symbolicly successfully to merge folder!")
                os.chdir(st.session_state.original_cwd)
                st.session_state.interferogram_merge = True
                st.info("➡️ Go to step 4 (Unwrapping)")

        else:

            n_jobs_for_merging = st.number_input("Number of parallel jobs", min_value=1, max_value=16, value=10, key="n_jobs_for_merging")

            if st.button(" Run Interferogram Merging"):
                try:
                    st.info("⏳ Interferogram merging started. This might take several hours even...")

                    merging = merge(st.session_state.work_path, st.session_state.IW_number, n_jobs_for_merging)
                    merging.create_merge_requirementfiles()
                    merging.merge_first()
                    merging.merge_otherintfs()
                    merging.create_pdf_of_merged()
                    len_unique_shapes = merging.check_merging()

                    os.chdir(st.session_state.original_cwd)

                    if len_unique_shapes==1:

                        st.success("✅ All interferograms were merged successfully (self-checked)!")
                        st.session_state.interferogram_merge = True
                        st.info("➡️ Go to step 4 (Unwrapping)")


                    else:

                        st.error("❌ Some interferograms have not merged correctly. Check them out!")


                except Exception as e:
                    st.error(f"❌ Interferogram computation failed: {e}")


elif selection=="4-Unwrapping":

    if "create_landmask" not in st.session_state:
        st.session_state.create_landmask = False

    if "IW_number" not in st.session_state or not st.session_state.IW_number:
        iw_input = st.text_input("Enter IW numbers (e.g., 1 2 3)")
        if iw_input:
            try:
                st.session_state.IW_number = list(map(int, iw_input.split()))
            except ValueError:
                st.error("Please enter valid IW numbers separated by spaces (e.g., 1 2 3)")

    if "work_path" not in st.session_state or not st.session_state.work_path:
        st.session_state.work_path = st.text_input("Work Path (where the outputs of DefoEye will be saved)")

    if st.session_state.get("IW_number") and st.session_state.get("work_path"):
        st.success(f"✅ Using IW numbers: {st.session_state.IW_number} and work path: {st.session_state.work_path}")

        st.markdown("### Filtering non-land regions")

        if st.button("Create landmask"):
            
            try:

                st.info("⏳ First, there is a NetworkPruning folder in the work directory, all the removed intf will be returned to the merge folder.")

                NetworkPruning_dir = os.path.join(st.session_state.work_path, "NetworkPruning")
                merge_dir = os.path.join(st.session_state.work_path, "merge")

                if os.path.isdir(NetworkPruning_dir):

                    st.info("⏳ There is a NetworkPruning folder. Starting to return all the removed interferograms to merge folder...")

                    for folder in os.listdir(os.path.join(NetworkPruning_dir, "RemovedIntf")):
                        removedintf_subdir = os.path.join(os.path.join(NetworkPruning_dir, "RemovedIntf"), folder)
                        merge_subdir = os.path.join(merge_dir, folder)

                        shutil.copytree(removedintf_subdir, merge_subdir)

                    intf_list_path = os.path.join(st.session_state.work_path, 'NetworkPruning/intflist')
                    intf_list_path_copy = os.path.join(st.session_state.work_path, 'merge/intflist')
                    shutil.copy(intf_list_path, intf_list_path_copy)

                    merge_list_path = os.path.join(st.session_state.work_path, "NetworkPruning/merge_list")
                    merge_list_path_copy = os.path.join(st.session_state.work_path, 'merge/merge_list')
                    shutil.copy(merge_list_path, merge_list_path_copy)

                    shutil.rmtree(NetworkPruning_dir)

                    st.info("✅ All removed interferograms were successfully retained and NetworkPruning folder was removed...")

                    os.chdir(st.session_state.original_cwd)

                else:

                    st.info("✅ No NetworkPruning folder. There are no removed interferograms...")

                st.info("⏳ Land mask creation started...")    

                landmask = Landmask(st.session_state.work_path)
                landmask.create_land_mask()

                st.success("✅ Landmask created.")
                st.session_state.create_landmask = True
                os.chdir(st.session_state.original_cwd)

            except Exception as e:
                st.error(f"❌ Failed to create landmask: {e}")

    else:
        st.warning("Please enter both IW numbers and a work path to proceed.")
    
    if "unwrapping" not in st.session_state:
        st.session_state.unwrapping = False

    if st.session_state.create_landmask:

        st.markdown("### Phase Unwrapping")

        TH1_unwrapping = st.number_input("TH1_unwrapping", min_value=0.0, max_value=1.0, value=0.1, key="Th1_unwrapping")
        TH2_unwrapping = st.number_input("TH2_unwrapping", min_value=0.0, max_value=50.0, value=1.0, key="Th2_unwrapping")
        n_jobs_for_unwrapping = st.number_input("Number of parallel jobs", min_value=1, max_value=16, value=10, key="n_jobs_for_unwrapping")


        st.info("Go to the merge directory and have a look at corr.pdf files to insert regioncut boundary (AOI clipping) here:")

        regioncut = st.text_input("Enter AOI (format: first_col/last_col/first_row/last_row)", value="0/1000/0/1000")
        first_column, last_column, first_row, last_row = map(int, regioncut.split("/"))

        if st.button("Start AOI clipping and Phase Unwrapping"):

            try:
                st.info("⏳ First, if there is a BC_Corr folder in the work directory, the corr.grd files of original sizes are replaced in the merge folder.")


                corr_dir = os.path.join(st.session_state.work_path, "BC_Corr")
                merge_dir = os.path.join(st.session_state.work_path, "merge")

                if os.path.isdir(corr_dir):

                    st.info("⏳ There is a BC_Corr folder. Starting to copy corr.grd files of original size...")

                    for folder in os.listdir(corr_dir):
                        corr_subdir = os.path.join(corr_dir, folder)
                        merge_subdir = os.path.join(merge_dir, folder)

                        corr_file_src = os.path.join(corr_subdir, "corr.grd")
                        corr_file_dst = os.path.join(merge_subdir, "corr.grd")

                        shutil.copy2(corr_file_src, corr_file_dst)
                        os.chdir(st.session_state.original_cwd)

                    st.info("✅ All corr.grd files are of original sizes...")

                else:
                    
                    st.info("⏳ No BC_Corr folder recognized. All corr.grd files are of original sizes.")


                st.info("⏳ Unwrapping started. This might take several hours even...")

                phaseunwrap = PhaseUnwrapping(st.session_state.work_path, TH1_unwrapping, TH2_unwrapping, first_column, last_column, first_row, last_row, n_jobs_for_unwrapping)
                phaseunwrap.create_unwrapcsh()
                phaseunwrap.parallel_unwrapping()

                corr_prep = Corr(st.session_state.work_path, first_column, last_column, first_row, last_row)
                corr_prep.compute_mean_coherency_in_region()
                
                if os.path.isdir(corr_dir):

                    st.info("⏳ BC_Corr folder recognized. No backup needed for corr.grd files..")

                else:
                    st.info("⏳ BC_Corr folder not recognized. Backup of corr.grd started...")
                    corr_prep.corr_backup()

                corr_prep.corr_cut_create_pdf()

                st.session_state.unwrapping = True
                os.chdir(st.session_state.original_cwd)

            except Exception as e:
                st.error(f"❌ Unwrapping failed: {e}")

    if "loopclosure" not in st.session_state:
        st.session_state.loopclosure = False

    if st.session_state.unwrapping:

        st.markdown("### Interferogram Network Pruning")

        pruning_choice = st.radio("Do you want to perform interferogram network pruning using loop closure?", ["Yes", "No"], key="do_pruning")

        if pruning_choice == "Yes":
        
            loopclosure_Th = st.number_input("loop closure TH (radians)", min_value=0.0, max_value=50.0, value=5.0, key="loopclosure_Th")

            if st.button("Interferogram network pruning using loop closure"):

                try:
                    
                    st.info("⏳ Pruning started. This might take several minutes even...")

                    # Add functions here

                    prunning = Prunning(st.session_state.work_path, loopclosure_Th)
                    prunning.create_binary_mask()
                    prunning.loop_closure()
                    prunning.remove_bad_intf()

                    st.info("✅ Network pruning using loop closure Finished.")
                    st.session_state.loopclosure = True
                    os.chdir(st.session_state.original_cwd)
                    st.info("➡️ Go to step 5 (Anchoring)")

                except Exception as e:
                    st.error(f"❌ Pruning failed: {e}")

        elif pruning_choice == "No":
            st.success("✅ Skipped pruning...")
            st.info("➡️ Go to step 5 (Anchoring)")

elif selection=="5-Anchoring":

    if "anchoring" not in st.session_state:
        st.session_state.anchoring = False
        st.session_state.anchoring_method = False

    if "IW_number" not in st.session_state or not st.session_state.IW_number:
        iw_input = st.text_input("Enter IW numbers (e.g., 1 2 3)")
        if iw_input:
            try:
                st.session_state.IW_number = list(map(int, iw_input.split()))
            except ValueError:
                st.error("Please enter valid IW numbers separated by spaces (e.g., 1 2 3)")

    if "work_path" not in st.session_state or not st.session_state.work_path:
        st.session_state.work_path = st.text_input("Work Path (where the outputs of DefoEye will be saved)")

    if st.session_state.get("IW_number") and st.session_state.get("work_path"):
        st.success(f"✅ Using IW numbers: {st.session_state.IW_number} and work path: {st.session_state.work_path}")

        # Ask whether to use referencing
        user_answer_referencing = st.radio(
            "Do you want to consider a reference point?",
            ("No", "Yes")
        )


        if user_answer_referencing == "Yes":
            st.session_state.anchoring = True

            # 🔹 Ask which referencing method
            user_method_referencing = st.radio("Select anchoring method:", ("point/region referencing (lat/lon)", "Average-phase referencing"))

            if user_method_referencing == "Average-phase referencing":
                Th_coherency_referenceaveraging = st.number_input(
                    "Enter coherency threshold for averaging (recommended: 0.1):", min_value=0.0, max_value=1.0, value=0.1, step=0.01)

                if st.button("Run Average-phase referencing"):
                    try:
                        avg_referencing = Average_Referencing(st.session_state.work_path, float(Th_coherency_referenceaveraging))
                        avg_referencing.average_referencing()
                        st.success("✅ Average-phase referencing applied.")
                        st.info("➡️ Go to step 6 (TS-InSAR)")
                        st.session_state.anchoring_method = "average"
                        os.chdir(st.session_state.original_cwd)
                    except Exception as e:
                        st.error(f"❌ Failed: {e}")
                        os.chdir(st.session_state.original_cwd)
                        

            elif user_method_referencing == "point/region referencing (lat/lon)":
                ref_lat = st.number_input("Enter reference latitude:", format="%.6f")
                ref_lon = st.number_input("Enter reference longitude:", format="%.6f")
                neighbourhoodsize = st.number_input("Enter neighborhood size (n):", min_value=0, step=1)

                if st.button("Run Point/region referencing"):
                    try:
                        pointreferencing = Referencing(st.session_state.work_path, float(ref_lat), float(ref_lon), int(neighbourhoodsize))
                        pointreferencing.referencing()
                        st.success("✅ Point referencing applied.")
                        st.info("➡️ Go to step 6 (TS-InSAR)")
                        st.session_state.reference_method = "point"
                        os.chdir(st.session_state.original_cwd)
                    except Exception as e:
                        st.error(f"❌ Failed: {e}")
                        os.chdir(st.session_state.original_cwd)

        elif user_answer_referencing == "No":

            st.success("✅ No anchoring applied. There will be now unwrap_pin.grd files in the merge directories.")
            st.info("➡️ Go to step 6 (TS-InSAR)")
            st.session_state.reference_method = "no"
            os.chdir(st.session_state.original_cwd)

    else:
        st.warning("Please enter both IW numbers and a work path to proceed.")

elif selection=="6-TS-InSAR":

    if "TSInSAR" not in st.session_state:
        st.session_state.TSInSAR = False

    if "IW_number" not in st.session_state or not st.session_state.IW_number:
        iw_input = st.text_input("Enter IW numbers (e.g., 1 2 3)")
        if iw_input:
            try:
                st.session_state.IW_number = list(map(int, iw_input.split()))
            except ValueError:
                st.error("Please enter valid IW numbers separated by spaces (e.g., 1 2 3)")

    if "work_path" not in st.session_state or not st.session_state.work_path:
        st.session_state.work_path = st.text_input("Work Path (where the outputs of DefoEye will be saved)")

    if st.session_state.get("IW_number") and st.session_state.get("work_path"):
        st.success(f"✅ Using IW numbers: {st.session_state.IW_number} and work path: {st.session_state.work_path}")


        st.markdown("### SBAS Parameters")

        smooth_factor = st.number_input("Insert smooth factor (recommended: 5)", min_value=0, max_value=50, value=1)
        atm_factor = st.number_input("Insert atmospheric correction factor (recommended: 1)", min_value=1, max_value=50, value=3)

        if st.button("Run SBAS Time Series Analysis"):
            try:
                sbas = SBASadjustment(st.session_state.work_path, smooth_factor, atm_factor)
                sbas.create_symboliclink_supermaster()
                sbas.create_symboliclink_intf_baseline()
                sbas.create_intftab_scenetab_files()
                sbas.symbolic_link_trans_guass()
                sbas.sbas_main()

                st.success("✅ SBAS time series analysis completed.")
                st.info("➡️ Go to step 7 (Analysis)")
                st.session_state.TSInSAR = True
                os.chdir(st.session_state.original_cwd)

            except Exception as e:
                st.error(f"❌ SBAS failed: {e}")
                os.chdir(st.session_state.original_cwd)
    
    else:
        st.warning("Please enter both IW numbers and a work path to proceed.")

elif selection=="7-Analysis":

    st.info("Will be updated soon with more features...")

    if "export" not in st.session_state:
        st.session_state.export = False

    if "IW_number" not in st.session_state or not st.session_state.IW_number:
        iw_input = st.text_input("Enter IW numbers (e.g., 1 2 3)")
        if iw_input:
            try:
                st.session_state.IW_number = list(map(int, iw_input.split()))
            except ValueError:
                st.error("Please enter valid IW numbers separated by spaces (e.g., 1 2 3)")

    if "work_path" not in st.session_state or not st.session_state.work_path:
        st.session_state.work_path = st.text_input("Work Path (where the outputs of DefoEye will be saved)")

    if st.session_state.get("IW_number") and st.session_state.get("work_path"):
        st.success(f"✅ Using IW numbers: {st.session_state.IW_number} and work path: {st.session_state.work_path}")


        st.markdown("### Export settings")

        filter_wavelength_resolution = st.number_input("Please insert filter_wavelength_resolution for generating the final output files (recommended: 400 for az and range decimations of 20 and 5)", min_value=1, max_value=1000, value=400)

        if st.button("Export"):
            try:
                
                sbasoutputs = SBASoutputs(st.session_state.work_path, filter_wavelength_resolution)
                sbasoutputs.create_vel_llgrd()
                sbasoutputs.grds_to_grdll()
                sbasoutputs.grdll_to_geotif()

                st.success("✅ Export completed.")
                st.session_state.export = True
                os.chdir(st.session_state.original_cwd)

            except Exception as e:
                st.error(f"❌ SBAS failed: {e}")
                os.chdir(st.session_state.original_cwd)
    
    else:
        st.warning("Please enter both IW numbers and a work path to proceed.")