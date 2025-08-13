import os
import shutil
import subprocess
import rasterio
import numpy as np

class Corr:

    def __init__(self, path_work, first_column, last_column, first_row, last_row):
        self.path_work = path_work
        self.first_column = first_column
        self.last_column = last_column
        self.first_row = first_row
        self.last_row = last_row


    def compute_mean_coherency_in_region(self):
        
        print('Starting to compute mean coherency for each intf...')

        # Define the directory path
        directory_path = self.path_work + 'merge/'

        file_path = os.path.join(directory_path, 'mean_values.txt')
        # Check if the file exists
        if os.path.exists(file_path):
            # Delete the file
            os.remove(file_path)

        # Get a list of directories
        folders = sorted([d for d in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, d))])

        # Define a function to execute commands in each folder
        def process_folder(directory_path, folder_name, first_column, last_column, first_row, last_row):

            folder = os.path.join(directory_path, folder_name)
            # Change directory to the current folder
            os.chdir(folder)

            # Construct the -R option value
            region = f"{first_column}/{last_column}/{first_row}/{last_row}"

            # Execute GMT commands
            subprocess.run(['gmt', 'grdcut', 'corr.grd', f'-R{region}', '-Gcorr_for_pair_selection.grd'], stderr=subprocess.DEVNULL)
            subprocess.run(['gmt', 'grdsample', 'landmask_ra.grd', f'-Rcorr_for_pair_selection.grd', '-Glandmask_for_pair_selection.grd'], stderr=subprocess.DEVNULL)
            subprocess.run(['gmt', 'grdmath', 'corr_for_pair_selection.grd', 'landmask_for_pair_selection.grd', 'MUL', '=', 'corr_for_pair_selection.grd'], stderr=subprocess.DEVNULL)

            # Generating a pdf file of the corr_for_pair_selection.grd

            subprocess.run(['tcsh', '-c', 'gmt grdimage corr_for_pair_selection.grd -Cgray -JX6i -P -K > temp.ps'])
            subprocess.run(['tcsh', '-c', 'gmt psbasemap -Rcorr_for_pair_selection.grd -J -O -Bxa -Bya >> temp.ps'])
            subprocess.run(['tcsh', '-c', 'gmt psconvert temp.ps -A -P -Tf -Fcorr_for_pair_selection'])
            subprocess.run(['tcsh', '-c', 'rm temp.ps'])

            with rasterio.open('corr_for_pair_selection.grd') as src:
                # Read the first band
                array = src.read(1)
                mean_coherency_of_interferogram = np.nanmean(array)

            # Write folder name and computed mean value to a file in the main directory
            with open(os.path.join(directory_path, 'mean_values.txt'), 'a') as f:
                f.write(f"{folder_name},{mean_coherency_of_interferogram}\n")

            # Change directory back to the main directory
            os.chdir(directory_path)

        # Iterate through each folder in the main directory
        for folder in folders:
            process_folder(directory_path, folder, self.first_column, self.last_column, self.first_row, self.last_row)

    def corr_backup(self):

        print('Backing up all corr.grd files befor cutting...')

        ## Backup Corr.grd because you have a region cut
        # Define the source and destination base directories
        source_directory = self.path_work + 'merge/'
        destination_directory = self.path_work + 'BC_Corr/'

        # Walk through the directory tree in the source directory
        for root, dirs, files in os.walk(source_directory):
            for file in files:
                if file == "corr.grd":
                    # Construct the source file path
                    src_file_path = os.path.join(root, file)
                    
                    # Create a corresponding destination path
                    dest_file_path = os.path.join(destination_directory, os.path.relpath(root, source_directory), file)
                    
                    # Ensure the destination directory exists
                    os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(src_file_path, dest_file_path)
                    # print(f"Copied: {src_file_path} to {dest_file_path}")


    def corr_cut_create_pdf(self):
        # Corr.grd region cut
        print('Cutting all corr.grd files and creating PDF files...')

        # Define the base directory containing all the folders
        base_directory = self.path_work + 'merge/'

        # Walk through each directory in the base directory
        for root, dirs, files in os.walk(base_directory):
            for file in files:
                if file == "corr.grd":
                    # Change the working directory to the current folder
                    os.chdir(root)
                    # print(f"Working in {root}")
                    
                    # Define the command to be executed
                    command = f"gmt grdcut corr.grd -R{self.first_column}/{self.last_column}/{self.first_row}/{self.last_row} -Gcorr.grd"
                    # command = "gmt grdcut corr.grd -R0/35000/1000/12000 -Gcorr.grd"
                    
                    # Run the command
                    process = subprocess.run(command, shell=True, capture_output=True, text=True)

        ### I want to create a corr.pdf file of all cutted corr.grd files

        def process_folders(root_dir):
            # List the immediate subdirectories
            subdirectories = sorted([os.path.join(root_dir, d) for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))])
            
            for subdir_path in subdirectories:
                # Check if 'corr.grd' exists in the current subdirectory
                if 'corr.grd' in os.listdir(subdir_path):
                    # Change the current working directory to the subdirectory containing 'corr.grd'
                    os.chdir(subdir_path)
                    subprocess.run(['tcsh', '-c', 'gmt grdimage corr.grd -Cgray -JX6i -P -K > temp.ps'])
                    subprocess.run(['tcsh', '-c', 'gmt psbasemap -Rcorr.grd -J -O -Bxa -Bya >> temp.ps'])
                    subprocess.run(['tcsh', '-c', 'gmt psconvert temp.ps -A -P -Tf -Fcorr_regioncout'])
                    subprocess.run(['tcsh', '-c', 'rm temp.ps'])
                else:
                    # Print the directory name if 'corr.grd' is not found
                    print(f"No corr.grd found in {subdir_path}")

        # Define the root directory to start the search
        root_directory = os.path.join(self.path_work, 'merge')

        # Call the function to process folders
        process_folders(root_directory)