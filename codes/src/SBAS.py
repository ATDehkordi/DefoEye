import os
import glob
import numpy as np
import re
import subprocess

class SBASadjustment:


    def __init__(self, path_work, smooth_factor, atm_factor):

        self.path_work = path_work
        self.smooth_factor = smooth_factor
        self.atm_factor = atm_factor

    def create_symboliclink_supermaster(self):


        # Define the paths
        file_path = self.path_work + 'merge/merge_list'

        # Read the first row from the file
        with open(file_path, 'r') as file:
            first_row = file.readline().strip()

        # Extract the required directory name
        parts = first_row.split('/')
        directory_name = parts[-2]

        # Define the paths for the symbolic link
        supermaster_file = f'{self.path_work}merge/{directory_name}/supermaster.PRM'

        link_name = os.path.join(self.path_work, 'supermaster.PRM')

        # Create the symbolic link
        if not os.path.islink(link_name) and not os.path.exists(link_name):
            os.symlink(supermaster_file, link_name)

        # os.symlink(supermaster_file, link_name)


    def create_symboliclink_intf_baseline(self):

        # Find all folders starting with 'F' followed by a number (1, 2, or 3)
        folder_candidates = sorted(glob.glob(os.path.join(self.path_work, 'F[123]')))

        # Select the folder with the smallest number suffix
        selected_folder = folder_candidates[0]

        baseline_table_path = os.path.join(selected_folder, 'baseline_table.dat')
        symlink_path = os.path.join(self.path_work, 'baseline_table.dat')

        if not os.path.islink(symlink_path) and not os.path.exists(symlink_path):
            os.symlink(baseline_table_path, symlink_path)

        # os.symlink(baseline_table_path, symlink_path)


        intf_in_path = os.path.join(selected_folder, 'intf.in')
        symlink_path = os.path.join(self.path_work, 'intf.in')

        if not os.path.islink(symlink_path) and not os.path.exists(symlink_path):
            os.symlink(baseline_table_path, symlink_path)

        # os.symlink(intf_in_path, symlink_path)


    def create_intftab_scenetab_files(self):

        # 22 SBAS pre-requirements

        # Creating scene.tab and intf.tab in SBAS folder
        # Path for the new folder
        sbas_folder_path = os.path.join(self.path_work, 'SBAS')

        # Create the 'SBAS' directory if it doesn't already exist
        os.makedirs(sbas_folder_path, exist_ok=True)

        # Names of the files to create in the 'SBAS' directory
        file_names = ['intf.tab', 'scene.tab']

        # Create each file in the 'SBAS' directory
        for file_name in file_names:
            file_path = os.path.join(sbas_folder_path, file_name)
            with open(file_path, 'w') as file:
                pass  # 'pass' simply moves on—it's used here to create an empty file

        # Filling scene.tab file

        source_file_path = self.path_work + 'baseline_table.dat'  # Update this to your .dat file location
        destination_file_path = self.path_work + 'SBAS/scene.tab'  # Update this to your destination directory

        # Read from the .dat file and write to the .tab file
        with open(source_file_path, 'r') as source_file:
            with open(destination_file_path, 'w') as destination_file:
                # Process each line in the source file
                for line in source_file:
                    parts = line.split()  # Split the line into parts based on whitespace
                    date = parts[1][0:7]  # Extract characters from index 4 to 10 (3:10 in zero-based indexing)
                    third_column_value = parts[2]  # Get the value of the third column
                    # Write to the .tab file
                    # if date in all_images:
                    destination_file.write(f"{date}\t{third_column_value}\n")



        # Filling intf.tab file

        root_directory = self.path_work + 'merge/'

        # List to hold all the paths
        unwrap_files_paths = []
        corr_files_paths = []

        # Set to keep track of directories where unwrap_pin.grd is found
        dirs_with_unwrap_pin = set()

        # Walk through the directory structure
        for subdir, dirs, files in os.walk(root_directory):
            # Check if 'unwrap_pin.grd' exists in the files of the current directory
            if 'unwrap_pin.grd' in files:
                # Construct the full path to the file
                full_path = os.path.join(subdir, 'unwrap_pin.grd')
                # Create a relative path from the specified format
                relative_path = os.path.relpath(full_path, root_directory)
                # Append the '../' prefix to match the desired format
                formatted_path = f"../merge/{relative_path}"
                unwrap_files_paths.append(formatted_path)
                # Mark the directory to skip 'unwrap.grd'
                dirs_with_unwrap_pin.add(subdir)
            
            # Check for 'unwrap.grd' only if 'unwrap_pin.grd' was not found
            elif 'unwrap.grd' in files and subdir not in dirs_with_unwrap_pin:
                # Construct the full path to the file
                full_path = os.path.join(subdir, 'unwrap.grd')
                # Create a relative path from the specified format
                relative_path = os.path.relpath(full_path, root_directory)
                # Append the '../' prefix to match the desired format
                formatted_path = f"../merge/{relative_path}"
                unwrap_files_paths.append(formatted_path)

            # Check for 'corr.grd' in all cases
            if 'corr.grd' in files:
                # Construct the full path to the file
                full_path = os.path.join(subdir, 'corr.grd')
                # Create a relative path from the specified format
                relative_path = os.path.relpath(full_path, root_directory)
                # Append the '../' prefix to match the desired format
                formatted_path = f"../merge/{relative_path}"
                corr_files_paths.append(formatted_path)

        unwrap_files_paths = sorted(unwrap_files_paths)
        corr_files_paths = sorted(corr_files_paths)


        # Getting the date of first and second image in each intrferogram using intf.in file

        source_file_path = self.path_work + 'intf.in'  # Update this to your .dat file location

        intf_date1 = []
        intf_date2 = []

        for i in range(len(unwrap_files_paths)):
            intf_date1.append(re.search(r'(\d{7})_(\d{7})', unwrap_files_paths[i]).group(1))
            intf_date2.append(re.search(r'(\d{7})_(\d{7})', unwrap_files_paths[i]).group(2))

        # # Read from the .dat file and write to the .tab file
        # with open(source_file_path, 'r') as source_file:
        #     for line in source_file:
        #         intf_date1.append(line[3:11])  # Extract characters
        #         intf_date2.append(line[22:30])  # Extract characters


        file_path = self.path_work + 'baseline_table.dat'  # Update this to the path of your data file

        # List to hold the last column values from matching rows
        b_prep_date1 = np.zeros(len(intf_date1))
        b_prep_date2 = np.zeros(len(intf_date1))
        counter = 0

        # Open and read the file line by line
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.split()  # Split the line into parts

                # Extract the date from the line (assuming the date format you're interested in is always in the same position)
                # date_in_line = parts[0].split('_')[1]
                date_in_line = parts[1][0:7]
                

                for i in range(len(intf_date1)):
                    if date_in_line == intf_date1[i]:
                        b_prep_date1[i] = float(parts[-1])

                for j in range(len(intf_date2)):
                    if date_in_line == intf_date2[j]:
                        b_prep_date2[j] = float(parts[-1])

        b_prep_intf = b_prep_date1 - b_prep_date2


        # File path to save the data
        file_path = self.path_work + 'SBAS/intf.tab'

        # Open a file (this will create the file if it does not exist)
        with open(file_path, 'w') as file:
            # Iterate through each element by index
            for i in range(len(unwrap_files_paths)):  # Assuming all lists and the array are of the same length
                # Write each element from the lists and array into the file formatted as columns
                # Here we use space as a separator, but you can choose comma or any other
                file.write(f"{unwrap_files_paths[i]} {corr_files_paths[i]} {intf_date1[i]} {intf_date2[i]} {b_prep_intf[i]}\n")


    def symbolic_link_trans_guass(self):

        # Symbolik link from trans.dat to SBAS folder from merge

        def manage_symbolic_link(src_file, dest_directory):
            # Define the name of the symbolic link
            dest_file = os.path.join(dest_directory, 'trans.dat')
            
            # Check if the symbolic link already exists
            if os.path.islink(dest_file):
                # If it exists and is a symbolic link, remove it
                os.unlink(dest_file)
                print(f"Removed existing symbolic link: {dest_file}")
            elif os.path.exists(dest_file):
                # If it exists but is not a symbolic link, raise an error
                print(f"Error: {dest_file} exists but is not a symbolic link.")
                return
            
            # Create a new symbolic link
            os.symlink(src_file, dest_file)
            # print(f"Created new symbolic link: {src_file} -> {dest_file}")
            
        # Define the source file and destination directory
        src_file = self.path_work + 'merge/trans.dat'
        dest_directory = self.path_work + 'SBAS'
        manage_symbolic_link(src_file, dest_directory)


        # Symbolik link from guass_* to SBAS folder from one of the intf files

        # Find all folders starting with 'F' followed by a number (1, 2, or 3)
        folder_candidates = sorted(glob.glob(os.path.join(self.path_work, 'F[123]')))

        # Select the folder with the smallest number suffix
        selected_folder = folder_candidates[0]
        selected_folder = os.path.join(selected_folder, 'intf_all')

        # Find all subdirectories in the selected_folder that start with '20'
        intf_folders = sorted([folder for folder in os.listdir(selected_folder) if folder.startswith('20')])

        # Take the first folder from the sorted list
        first_year_folder = intf_folders[0]

        # Construct the full path to the first folder
        first_year_folder_path = os.path.join(selected_folder, first_year_folder)

        # Find all files in this folder starting with 'guass'
        gauss_file = glob.glob(os.path.join(first_year_folder_path, 'gauss*'))

        gauss_file_name = os.path.basename(gauss_file[0])

        dest_directory = self.path_work + 'SBAS'
        # # Construct the full path for the symbolic link in the destination directory
        symlink_path = os.path.join(dest_directory, gauss_file_name)
        os.symlink(gauss_file[0], symlink_path)


    def sbas_main(self):

        # 22 SBAS parameters

        file_path = self.path_work + 'SBAS/intf.tab'

        N = 0
        with open(file_path, 'r') as file:
            for line in file:
                N += 1

        file_path = self.path_work + 'SBAS/scene.tab'

        S = 0
        with open(file_path, 'r') as file:
            for line in file:
                S += 1

        # Getting x_dim and y_dim

        directory = self.path_work + 'merge/'
        dirs = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
        dirs.sort()  # Sort the directories alphabetically
        os.chdir(os.path.join(directory, dirs[0])) # Randomly select the first one

        # command = f'gmt grdinfo unwrap_pin.grd'
        command = f'gmt grdinfo unwrap.grd' # There is no difference in xdim and ydim of unwrap.grd or unwrap_pin.grd
            
        result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

        # Use regular expressions to find 'n_columns' and 'n_rows'
        n_columns_match = re.search(r'n_columns: (\d+)', result)
        n_rows_match = re.search(r'n_rows: (\d+)', result)

        x_min = int(re.search(r'x_min: (\d+)', result).group(1))
        x_max = int(re.search(r'x_max: (\d+)', result).group(1))

        # Extract the values if the patterns were found
        xdim = int(n_columns_match.group(1))
        ydim = int(n_rows_match.group(1))


        file_path = self.path_work +'supermaster.PRM'  # Update this with the actual path to your PRM file

        # Keys of interest whose values you want to extract
        keys_of_interest = ['radar_wavelength', 'rng_samp_rate', 'near_range']

        # Dictionary to hold the values of the keys
        parameters = {key: None for key in keys_of_interest}

        # Open and read the PRM file
        with open(file_path, 'r') as file:
            for line in file:
                # Remove whitespace and split the line into key and value based on the equal sign
                parts = line.strip().split('=')
                if len(parts) == 2:
                    key, value = parts[0].strip(), parts[1].strip()
                    # Check if the key is one of the keys of interest
                    if key== keys_of_interest[0]:
                        # Store the value in the dictionary
                        radar_wavelength = float(value)

                    if key== keys_of_interest[1]:
                        # Store the value in the dictionary
                        rng_sample_rate = float(value)

                    if key== keys_of_interest[2]:
                        # Store the value in the dictionary
                        near_range = float(value)


        rng_pixel_size = (300000000) / (rng_sample_rate) / 2
        rng = np.round(rng_pixel_size * (x_min+x_max) / 2 + near_range)



        # i have a directory. there are several F* folders inside that, where * is 1,2,or 3. i want a code to enter each of F* directoies. 
        # there is a raw folder in each F* folder. inside that raw folder, there are lots of .xml files. i want to read the first sorted .xml file, 
        # and get the values of all incidence angles and return the average of them

        base_directory = self.path_work # Thi is the base folder in external hard.

        import xml.etree.ElementTree as ET

        def get_incidence_angle(xml_file_path):
            """Extract and return the incidence angle from the provided XML file."""
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            incidence_angle_mid_swath = root.find('.//incidenceAngleMidSwath')
            if incidence_angle_mid_swath is not None:
                return round(float(incidence_angle_mid_swath.text), 2)
            return None


        folders = [f for f in os.listdir(base_directory) if f.startswith('F') and os.path.isdir(os.path.join(base_directory, f))]

        all_incidence_angles = []

        for folder in folders:
            # Construct the path to the raw folder inside each F* directory
            raw_folder_path = os.path.join(base_directory, folder, 'raw')
            # Find all XML files in the raw folder
            xml_files = sorted(glob.glob(os.path.join(raw_folder_path, '*.xml')))
            
            if xml_files:
                # Process only the first XML file
                first_xml_file = xml_files[0]
                incidence_angle = get_incidence_angle(first_xml_file)
                if incidence_angle is not None:
                    all_incidence_angles.append(incidence_angle)
                    # print(f"Incidence angle from {first_xml_file}: {incidence_angle}")

        if all_incidence_angles:
            # Calculate the average of the incidence angles
            average_incidence_angle = round(sum(all_incidence_angles) / len(all_incidence_angles), 1)
            # print(f"Average incidence angle: {average_incidence_angle}")
        else:
            print("No incidence angles found.")

        print('Writing average incidence angle to SBAS folder (You can use this value to convert LOS values into vertical values)...')

        average_incidence_angle_file_path = os.path.join(self.path_work + 'SBAS', 'average_incidence_angle.txt')
        # Write the value to the file
        with open(average_incidence_angle_file_path, 'w') as file:
            file.write(f'{average_incidence_angle}')
                
        # SBAS final command, it must be run in SBAS folder

        os.chdir(self.path_work + 'SBAS')

        command = f"tcsh -c 'sbas intf.tab scene.tab {N} {S} {xdim} {ydim} -range {rng} -incidence {average_incidence_angle} -wavelength {radar_wavelength} -smooth {self.smooth_factor} -atm {self.atm_factor} -rms -dem'"

        print('SBAS final command which will be executed (takes several hours depending on the number of intfs and region size):')
        print(f'sbas intf.tab scene.tab {N} {S} {xdim} {ydim} -range {rng} -incidence {average_incidence_angle} -wavelength {radar_wavelength} -smooth {self.smooth_factor} -atm {self.atm_factor} -rms -dem')

        print('')
        print('SBAS command is running...')
        print('')

        subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print('')
        print('SBAS command Finished...')
        print('')