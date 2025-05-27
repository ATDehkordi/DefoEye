import shutil
import os
import subprocess
import concurrent.futures

class Intf_compute():

    def __init__(self, path_work, list_of_IW_numbers, filter_wavelength_value = 200, range_dec_value = 20, azimuth_dec_value = 5, n_jobs_for_intf = 10):
        self.path_work = path_work
        self.list_of_IW_numbers = list_of_IW_numbers
        self.filter_wavelength_value = filter_wavelength_value
        self.range_dec_value = range_dec_value
        self.azimuth_dec_value = azimuth_dec_value
        self.n_jobs_for_intf = n_jobs_for_intf

    def copy_batchtops_file(self):

        for IW_number in self.list_of_IW_numbers:
            shutil.copy2('/home/user/PHDLund/PythonProjects_github/GMTSAR_plus/RequiredFiles/batch_tops.config', self.path_work + 'F' + str(IW_number) + '/' + 'batch_tops.config')

    def update_batchtops_test_firstintf(self):

        # Open the master_date.txt file in read mode
        with open(self.path_work + 'master_date.txt', 'r') as file:
            # Read the content and strip any trailing newline or whitespace characters
            master_date = file.read().strip()

        for IW_number in self.list_of_IW_numbers:
            config_file_path = self.path_work + 'F' + str(IW_number) + '/' + 'batch_tops.config'

            master_image_name = 'S1_' + master_date + '_ALL_F'+str(IW_number)
            proc_stage_value = '1' # It must be 1 in the first time
            filter_wavelength_value = self.filter_wavelength_value
            range_dec_value = self.range_dec_value
            azimuth_dec_value = self.azimuth_dec_value
            threshold_snaphu_value = '0'
            threshold_geocode_value = '0'

            updated_lines = []

            with open(config_file_path, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    if line.strip().startswith('master_image'):
                        # Replace the existing line with the new value
                        updated_lines.append(f"master_image = {master_image_name}\n")

                    elif line.strip().startswith('proc_stage'):
                        # Write the updated master_image value
                        updated_lines.append(f"proc_stage = {proc_stage_value}\n")

                    elif line.strip().startswith('filter_wavelength'):
                        # Write the updated master_image value
                        updated_lines.append(f"filter_wavelength = {filter_wavelength_value}\n")

                    elif line.strip().startswith('range_dec'):
                        # Write the updated master_image value
                        updated_lines.append(f"range_dec = {range_dec_value}\n")

                    elif line.strip().startswith('azimuth_dec'):
                        # Write the updated master_image value
                        updated_lines.append(f"azimuth_dec = {azimuth_dec_value}\n")

                    elif line.strip().startswith('threshold_snaphu'):
                        # Write the updated master_image value
                        updated_lines.append(f"threshold_snaphu = {threshold_snaphu_value}\n")

                    elif line.strip().startswith('threshold_geocode'):
                        # Write the updated master_image value
                        updated_lines.append(f"threshold_geocode = {threshold_geocode_value}\n")

                    else:
                        # Add the original line to updated_lines
                        updated_lines.append(line)

            # return updated_lines

            with open(config_file_path, 'w') as file:
                file.writelines(updated_lines)

            
            # 16- A one.in file is created in F# folder for testing the unwrapping procedure, a file which is sth like this:
            # The first image must be the master image
            # For the second one, just a random image is added (baseline_table.dat file is used)

            # Define the filename
            filename = 'one.in'
            file_path = os.path.join(self.path_work + 'F' + str(IW_number) + '/', filename)

            first_column_values = []
            with open(self.path_work + 'F' + str(IW_number) + '/' + 'intf.in', 'r') as file:

                for line in file:
                    # Split the line into components based on whitespace
                    parts = line.strip().split()
                    # Add the first component (first column) to the list
                    if parts:  # Check if the line was not empty
                        first_column_values.append(parts[0])

            # We use intf.in in order to select the first baseline pair with the first image as the master.

            for i in range(len(first_column_values)):
                if first_column_values[i][:18] == 'S1_' + master_date + '_ALL_F'+str(IW_number):
                    content = first_column_values[i]

            with open(file_path, 'w') as file:
                file.write(content)

            print(f'Starting DEM registration and computing first random intf for IW{IW_number}')
            # Define the directory where the script and data.in file are located
            directory = self.path_work + 'F' + str(IW_number) + '/'
            os.chdir(directory)  # Change the working directory to where the script is

            # Command to execute the script using tcsh shell
            command = "tcsh -c 'intf_tops.csh one.in batch_tops.config'"

            # Run the command
            try:
                # result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                result = subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # print("Output:", result.stdout)
                # print("Error:", result.stderr)
            except subprocess.CalledProcessError as e:
                print("An error occurred while executing the shell command.")
            
            print(f'Finishing DEM registration and computing first random intf for IW{IW_number}')


    def all_intf_computation(self):

        # 18- Running on all interferograms

        for IW_number in self.list_of_IW_numbers:

            config_file_path = self.path_work + 'F' + str(IW_number) + '/' + 'batch_tops.config'

            proc_stage_value = '2' # It must be 2 in the second time

            updated_lines = []
            with open(config_file_path, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    if line.strip().startswith('proc_stage'):
                        # Write the updated master_image value
                        updated_lines.append(f"proc_stage = {proc_stage_value}\n")
                    else:
                        # Add the original line to updated_lines
                        updated_lines.append(line)
            # return updated_lines
            with open(config_file_path, 'w') as file:
                file.writelines(updated_lines)

            def split_file(input_file, output_directory, num_parts):

                # Read all lines from the file
                with open(input_file, 'r') as file:
                    lines = file.readlines()

                # Calculate the number of lines per file
                total_lines = len(lines)
                part_size = total_lines // num_parts
                remainder = total_lines % num_parts

                # Write each part to a new file
                for i in range(num_parts):
                    start_index = i * part_size + min(i, remainder)
                    end_index = start_index + part_size + (1 if i < remainder else 0)
                    part_lines = lines[start_index:end_index]
                    
                    # Construct the filename
                    part_filename = f"intf{i+1}.in"
                    part_path = os.path.join(output_directory, part_filename)

                    # Write to the part file
                    with open(part_path, 'w') as part_file:
                        part_file.writelines(part_lines)
                    # print(f"{part_filename} with {len(part_lines)} lines.")


            input_file = self.path_work + 'F' + str(IW_number) + '/' + 'intf.in'
            output_directory = self.path_work + 'F' + str(IW_number) + '/'
            split_file(input_file, output_directory, self.n_jobs_for_intf )

            ## First I clean the inside of intf and intf_all folders
            folders_to_clean = ['intf', 'intf_all']

            for folder_name in folders_to_clean:
                folder_path = os.path.join(self.path_work + 'F' + str(IW_number), folder_name)
                if os.path.exists(folder_path) and os.path.isdir(folder_path):
                    # print(f"Cleaning contents of {folder_path}")
                    # Remove all contents of the directory
                    for item in os.listdir(folder_path):
                        item_path = os.path.join(folder_path, item)
                        if os.path.isfile(item_path) or os.path.islink(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                # else:
                #     print(f"Folder {folder_name} does not exist in {directory}")

            ### Running parallel commands

            print(f'Starting the computation of all interferograms for IW{IW_number}')

            def run_command(command, directory):
                # Run the command and suppress output by redirecting stdout and stderr to DEVNULL
                subprocess.run(command, shell=True, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=directory)

            commands = [f"tcsh -c 'intf_tops.csh intf{intf_number}.in batch_tops.config'" for intf_number in range(1, self.n_jobs_for_intf + 1)]

            # Using ThreadPoolExecutor to run commands in parallel
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Map the run_command function to the commands, providing the directory for each
                futures = {executor.submit(run_command, cmd, self.path_work + 'F' + str(IW_number) + '/'): cmd for cmd in commands}

            ## Clear all the intf1, intf1, and ... but preserving intf.in

            def clean_int_files(directory):
                # List all files in the directory
                for file_name in os.listdir(directory):
                    # Check if the file name starts with 'intf', ends with '.in', and has more than 'intf.in'
                    if file_name.startswith('intf') and file_name.endswith('.in') and file_name != 'intf.in':
                        file_path = os.path.join(directory, file_name)
                        # Delete the file
                        os.remove(file_path)

            clean_int_files(self.path_work + 'F' + str(IW_number) + '/')

            print(f'Finishing the computation of all interferograms for IW{IW_number}')


    def check_all_intf(self):

        for IW_number in self.list_of_IW_numbers:

            ## Checkig whether all of the files have been written to intf_all folders

            def check_folders_for_item_count(directory, required_item_count=29):
                folders_with_less_items = []

                # Get a sorted list of all folders in the specified directory
                folder_names = sorted(os.listdir(directory))
                
                for index, folder_name in enumerate(folder_names, start=1):
                    folder_path = os.path.join(directory, folder_name)
                    if os.path.isdir(folder_path):
                        # Count the number of items in the folder
                        item_count = len(os.listdir(folder_path))
                        if item_count != required_item_count:
                            folders_with_less_items.append((index, folder_name, item_count))
                
                return folders_with_less_items

            # Usage example
            directory_path = self.path_work + 'F' + str(IW_number) + '/intf_all/' # Replace with the path to your directory
            folders_with_less_than_29_items = check_folders_for_item_count(directory_path)

            if len(folders_with_less_than_29_items)==0:

                print(f'All the intfs in IW{IW_number} were written successfully (Checking was done)')

            else:

                print(f'Some of the intfs in IW{IW_number} were not written successfully! Running intf computation again for those...')


            def extract_rows(input_file, output_file, row_indices):
                # Read the input file and store its lines
                with open(input_file, 'r') as file:
                    lines = file.readlines()
                
                # Filter the lines based on the provided row indices
                selected_lines = [lines[i-1] for i in row_indices]
                
                # Write the selected lines to the output file
                with open(output_file, 'w') as file:
                    file.writelines(selected_lines)

                # Usage example
                input_file_path = self.path_work + 'F' + str(IW_number) + '/' + 'intf.in'  # Replace with the actual path to your intf.in file
                output_file_path = self.path_work + 'F' + str(IW_number) + '/' + 'intf_havingproblem.in'  # Replace with the desired output path

                # Extracting just the row indices from the list of tuples
                row_indices_only = [index for index, _, _ in folders_with_less_than_29_items]

                # Call the function to create the output file with the specified rows
                extract_rows(input_file_path, output_file_path, row_indices_only)


                # Define the directory where the script and data.in file are located
                directory = self.path_work + 'F' + str(IW_number) + '/' 
                os.chdir(directory)  # Change the working directory to where the script is

                # Command to execute the script using tcsh shell
                command = "tcsh -c 'intf_tops.csh intf_numoffiles.in batch_tops.config'"

                # Run the command
                try:
                    # result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    # print("Output:", result.stdout)
                    # print("Error:", result.stderr)
                except subprocess.CalledProcessError as e:
                    print("An error occurred while executing the shell command.")

                print(f'Checking again whether the intfs in IW{IW_number} were written successfully')

                # Usage example
                directory_path = self.path_work + 'F' + str(IW_number) + '/intf_all/'  # Replace with the path to your directory
                folders_with_less_than_29_items = check_folders_for_item_count(directory_path)

                if len(folders_with_less_than_29_items)==0:

                    print(f'All the intfs in IW{IW_number} were written successfully')

                else:

                    print(f'Some of the intfs in IW{IW_number} were not written successfully! Running intf computation again for those...')
                    print("Folders with less or more than 29 items:")
                    for index, folder, item_count in folders_with_less_than_29_items:
                        print(f"Folder {index} ('{folder}') has {item_count} items")