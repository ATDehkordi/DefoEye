import os
import rasterio
import numpy as np
import shutil


class Prunning():

    def __init__(self, path_work, TH_pruning):

        self.path_work = path_work
        self.TH_pruning = TH_pruning

    def create_binary_mask(self):
        
        self.NetworkPruning_dir = os.path.join(self.path_work, 'NetworkPruning')

        # Remove the folder if it exists
        if os.path.exists(self.NetworkPruning_dir):
            shutil.rmtree(self.NetworkPruning_dir)

        os.makedirs(self.NetworkPruning_dir, exist_ok=True)
        
        # I want to create a mask which shows which pixels have been considered in the unwrapping in all interferograms

        for folder_name in os.listdir(self.path_work + 'merge/'):

            folder_path = os.path.join(self.path_work + 'merge/', folder_name)

            if os.path.isdir(folder_path):
                    
                grd_file_path = os.path.join(folder_path, 'unwrap.grd')

                with rasterio.open(grd_file_path) as src:
                            # Read the first band
                            array = src.read(1)
                            self.binary_mask = np.ones((array.shape[0], array.shape[1]))
                            break


        for folder_name in os.listdir(self.path_work + 'merge/'):

            folder_path = os.path.join(self.path_work + 'merge/', folder_name)

            if os.path.isdir(folder_path):
                    
                grd_file_path = os.path.join(folder_path, 'unwrap.grd')

                with rasterio.open(grd_file_path) as src:
                            # Read the first band
                            array = src.read(1)
                            self.binary_mask = np.where(np.isnan(array), 0, 1) * self.binary_mask


    def loop_closure(self):
          
        intf_dates = []

        with open(self.path_work+'merge/intflist', 'r') as file:
            for line in file:
                intf_dates.append(line.strip())


        loops_dates = []
        loops_average_phase = []
        loops_RMS_phase = []


        for intf12 in intf_dates:

            if [ifg for ifg in intf_dates if ifg.startswith(intf12.split('_')[1])]:

                intf23_candidates = [ifg for ifg in intf_dates if ifg.startswith(intf12.split('_')[1])] 

                for intf23 in intf23_candidates:

                    if [ifg for ifg in intf_dates if ifg.startswith(intf12.split('_')[0]) and ifg.endswith(intf23.split('_')[1])]:

                        intf13 = [ifg for ifg in intf_dates if ifg.startswith(intf12.split('_')[0]) and ifg.endswith(intf23.split('_')[1])][0]

                        loops_dates.append([intf12, intf23, intf13])    

                        unwrap12_path = os.path.join(os.path.join(self.path_work + 'merge/', intf12), 'unwrap.grd')
                        with rasterio.open(unwrap12_path) as src:
                            unwrap12 = np.nan_to_num(src.read(1), nan=0) * self.binary_mask
                            unwrap12[unwrap12 == 0] = np.nan

                        unwrap23_path = os.path.join(os.path.join(self.path_work + 'merge/', intf23), 'unwrap.grd')
                        with rasterio.open(unwrap23_path) as src:
                            unwrap23 = np.nan_to_num(src.read(1), nan=0) * self.binary_mask
                            unwrap23[unwrap23 == 0] = np.nan

                        unwrap13_path = os.path.join(os.path.join(self.path_work + 'merge/', intf13), 'unwrap.grd')
                        with rasterio.open(unwrap13_path) as src:
                            unwrap13 = np.nan_to_num(src.read(1), nan=0) * self.binary_mask
                            unwrap13[unwrap13 == 0] = np.nan

                        # Image-wise computation for intf network filtering
                        loops_average_phase.append(np.nanmean(unwrap12 + unwrap23 - unwrap13))
                        loops_RMS_phase.append(np.sqrt(np.nanmean(np.square(unwrap12 + unwrap23 - unwrap13))))
                        

        # you can have a look at loops_RMS_phase in loop_closure folder to estimate a good TH_pruning (it should be in radian like 1.5 or 3)- try to increase it for vegetated regions

        loops_dates_removal_candidates = []
        loops_dates_keep_candidates = []

        for i in range(len(loops_dates)):
            if loops_RMS_phase[i]>self.TH_pruning:
                loops_dates_removal_candidates.append(loops_dates[i])
            else:
                loops_dates_keep_candidates.append(loops_dates[i])

        # Flatten the nested list
        loops_dates_removal_candidates = [item for sublist in loops_dates_removal_candidates for item in sublist]
        loops_dates_keep_candidates = [item for sublist in loops_dates_keep_candidates for item in sublist]

        # Use set to remove duplicates and convert back to list
        loops_dates_removal_candidates = sorted(list(set(loops_dates_removal_candidates)))
        loops_dates_keep_candidates = sorted(list(set(loops_dates_keep_candidates)))

        self.bad_ifg = list(set(loops_dates_removal_candidates)-set(loops_dates_keep_candidates)) # difference
        self.bad_ifg.sort()

        merge_list_path = os.path.join(self.path_work, "merge/merge_list")

        # Backup original merge_list
        with open(merge_list_path, "r") as f:
            lines = [line.strip() for line in f.readlines()]

        # Step 1: Check first row for interferograms to preserve
        if lines:
            first_line = lines[0]
            for interferogram in self.bad_ifg:  # iterate over a copy
                if interferogram in first_line:
                    self.bad_ifg.remove(interferogram)  # preserve it



        with open(os.path.join(self.NetworkPruning_dir, "loops_RMS_phase.txt"), "w") as f:
            for item in loops_RMS_phase:
                f.write(f"{item}\n")

        with open(os.path.join(self.NetworkPruning_dir, "bad_ifg.txt"), "w") as f:
            for value in self.bad_ifg:
                f.write(f"{value}\n")


    def remove_bad_intf(self):
         
        self.RemoveIntf_dir = os.path.join(self.NetworkPruning_dir, 'RemovedIntf')

        # Remove the folder if it exists
        if os.path.exists(self.RemoveIntf_dir):
            shutil.rmtree(self.RemoveIntf_dir)

        os.makedirs(self.RemoveIntf_dir, exist_ok=True)

        source_dir = os.path.join(self.path_work, 'merge')

        for folder_name in self.bad_ifg:
            src_path = os.path.join(source_dir, folder_name)
            dst_path = os.path.join(self.RemoveIntf_dir, folder_name)

            shutil.copytree(src_path, dst_path, symlinks=True)
            # Then delete the original
            shutil.rmtree(src_path)

        intf_list_path = os.path.join(self.path_work, 'merge/intflist')
        intf_list_path_copy = os.path.join(self.path_work, 'NetworkPruning/intflist')
        shutil.copy(intf_list_path, intf_list_path_copy)


        # Step 2: Read original intflist
        with open(intf_list_path, 'r') as f:
            lines = [line.strip() for line in f.readlines()]

        # Step 3: Filter out the bad interferograms
        cleaned_lines = [line for line in lines if line not in self.bad_ifg]

        # Step 4: Write cleaned list back to the original intflist file
        with open(intf_list_path, 'w') as f:
            for line in cleaned_lines:
                f.write(line + '\n')



        merge_list_path = os.path.join(self.path_work, "merge/merge_list")
        merge_list_path_copy = os.path.join(self.path_work, 'NetworkPruning/merge_list')
        shutil.copy(merge_list_path, merge_list_path_copy)

        # Backup original merge_list
        with open(merge_list_path, "r") as f:
            lines = [line.strip() for line in f.readlines()]

        cleaned_lines = [line for line in lines if not any(bad in line for bad in self.bad_ifg)]

        # Step 3: Save cleaned merge_list
        with open(merge_list_path, "w") as f:
            for line in cleaned_lines:
                f.write(line + "\n")

