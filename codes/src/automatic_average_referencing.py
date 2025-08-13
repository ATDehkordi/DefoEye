import os
import xarray as xr
import numpy as np
import rasterio
import subprocess


class Average_Referencing:

    def __init__(self, path_work, Th_coherency_referenceaveraging):

        self.path_work = path_work
        self.Th_coherency_referenceaveraging = Th_coherency_referenceaveraging


    def average_referencing(self):

        print('Avg Referencing starts...')
        
        for folder_name in os.listdir(self.path_work + 'merge/'):

            folder_path = os.path.join(self.path_work + 'merge/', folder_name)

            if os.path.isdir(folder_path):
                    
                grd_file_path = os.path.join(folder_path, 'unwrap.grd')

                with rasterio.open(grd_file_path) as src:
                            # Read the first band
                            array = src.read(1)
                            binary_mask = np.ones((array.shape[0], array.shape[1]))
                            break

        for folder_name in os.listdir(self.path_work + 'merge/'):

            folder_path = os.path.join(self.path_work + 'merge/', folder_name)

            if os.path.isdir(folder_path):
                    
                grd_file_path = os.path.join(folder_path, 'corr.grd')

                with rasterio.open(grd_file_path) as src:
                            # Read the first band
                            array = src.read(1)
                            binary_mask = np.where(array<self.Th_coherency_referenceaveraging, 0, 1) * binary_mask

        def subtract_average_from_grd(grd_file, value_to_subtract, output_grd):
            # Load the .grd file using xarray
            ds = xr.open_dataset(grd_file)

            # Extract the variable (usually, the main data array is unnamed or named 'z' in .grd files)
            data_var = list(ds.data_vars)[0]  # Get the first data variable (assuming it's the main one)
            unwrap_data = ds[data_var].values  # Get the 2D array

            # Subtract the numpy array value from the unwrap data
            unwrap_pin_data = unwrap_data - value_to_subtract

            # Replace the data in the xarray dataset
            ds[data_var].values = unwrap_pin_data

            # Save the result to a new .grd file
            ds.to_netcdf(output_grd)

            # Close the dataset
            ds.close()

        avg_phase_total = []

        for folder_name in sorted(os.listdir(self.path_work + 'merge/')):

            folder_path = os.path.join(self.path_work + 'merge/', folder_name)

            if os.path.isdir(folder_path):
                    
                grd_file_path = os.path.join(folder_path, 'unwrap.grd')
                grd_file_path_output = os.path.join(folder_path, 'unwrap_pin.grd')

                with rasterio.open(grd_file_path) as src:
                            unwrap_phase = src.read(1) * binary_mask
                            subtract_average_from_grd(grd_file_path, np.nanmean(unwrap_phase[binary_mask == 1]), grd_file_path_output)
                            avg_phase_total.append(np.nanmean(unwrap_phase[binary_mask == 1]))

        with open(os.path.join(self.path_work + 'merge/', 'avg_phase_for_referencing.txt'), 'w') as file:
            for item in avg_phase_total:
                file.write(f"{item}\n")

        print('Referencing finished! Creating PDF files of unwrap_pin.grd files...')
        
        def process_folders(root_dir):
            # List the immediate subdirectories
            subdirectories = sorted([os.path.join(root_dir, d) for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))])
            
            for subdir_path in subdirectories:
                # Check if 'corr.grd' exists in the current subdirectory
                if 'unwrap_pin.grd' in os.listdir(subdir_path):
                    # Change the current working directory to the subdirectory containing 'corr.grd'
                    os.chdir(subdir_path)
                    subprocess.run(['tcsh', '-c', 'gmt grdimage unwrap_pin.grd -Cjet -JX6i -P -K > temp.ps'])
                    subprocess.run(['tcsh', '-c', 'gmt psbasemap -Runwrap_pin.grd -J -O -Bxa -Bya >> temp.ps'])
                    subprocess.run(['tcsh', '-c', 'gmt psconvert temp.ps -A -P -Tf -Funwrap_pin'])
                    subprocess.run(['tcsh', '-c', 'rm temp.ps'])

        # Define the root directory to start the search
        root_directory = os.path.join(self.path_work, 'merge')

        # Call the function to process folders
        process_folders(root_directory)