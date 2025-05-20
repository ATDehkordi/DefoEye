import os
import subprocess
from datetime import datetime
import re


class intf_pairs:

    def __init__(self, path_work, list_of_IW_numbers, temporal_baseline = 85, spatial_baseline = 400, filter_intf_pairs = True, TH_number_of_connections = 4):

        self.path_work = path_work
        self.list_of_IW_numbers = list_of_IW_numbers
        self.temporal_baseline = temporal_baseline
        self.spatial_baseline = spatial_baseline
        self.filter_intf_pairs = filter_intf_pairs
        self.TH_number_of_connections = TH_number_of_connections

    def create_intfin_file(self):
        # 12- Creating intf.in file in F# folder

        # Create a blank file
        with open(self.path_work + 'F' + str(self.list_of_IW_numbers[0]) + '/' + 'intf.in', 'w') as file:
            pass  # Creates an empty file


    def initial_intf_pairs(self):
        print('Creating initial network of intfs...')
        # 13- Run these tow commands in terminal, which is opened in 'F#' folder of pathwork

        # tcsh 
        # select_pairs.csh baseline_table.dat 50 150


        # Define the directory where the script and data.in file are located
        directory = self.path_work + 'F' + str(self.list_of_IW_numbers[0]) + '/'
        os.chdir(directory)  # Change the working directory to where the script is

        # Command to execute the script using tcsh shell
        command = f"tcsh -c 'select_pairs.csh baseline_table.dat {self.temporal_baseline} {self.spatial_baseline}'"

        # Run the command
        try:
            # result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # print("Output:", result.stdout)
            # print("Error:", result.stderr)
        except subprocess.CalledProcessError as e:
            print("An error occurred while executing the shell command.")

        print('Creating initial network of intfs Finished!')

    def filter_intf_network(self):

        def parse_date_from_id(image_id):
            # Extracts the date part from the image ID and converts it to a datetime object
            date_str = image_id.split('_')[1]  # Splits on underscore and takes the second part
            return datetime.strptime(date_str, '%Y%m%d')
        
        def read_and_filter_connections(file_path, output_path):
            connections = {}
            
            # Read the file and build a dictionary of connections with the first image as the key
            with open(file_path, 'r') as file:
                for line in file:
                    first_image, second_image = line.strip().split(':')
                    if first_image not in connections:
                        connections[first_image] = []
                    connections[first_image].append(second_image)
            
            filtered_connections = []

            # Filter the connections
            for first_image, second_images in connections.items():
                if len(second_images) > self.TH_number_of_connections:  # If more than N connections exist
                    # Sort the connections based on the date difference
                    second_images_sorted = sorted(second_images, key=lambda x: (parse_date_from_id(x) - parse_date_from_id(first_image)).days)
                    # Keep only the top 3 with the smallest date differences
                    filtered_connections.extend(f'{first_image}:{second_image}' for second_image in second_images_sorted[:self.TH_number_of_connections])
                else:
                    # Keep all connections if less than or equal to N
                    filtered_connections.extend(f'{first_image}:{second_image}' for second_image in second_images)

            # Write the filtered connections to the output file
            with open(output_path, 'w') as output_file:
                for connection in filtered_connections:
                    output_file.write(connection + '\n')

        if self.filter_intf_pairs:

            # Use the function
            input_file_path = self.path_work + 'F' + str(self.list_of_IW_numbers[0]) + '/' + 'intf.in'
            output_file_path = self.path_work + 'F' + str(self.list_of_IW_numbers[0]) + '/' + 'intf.in'
            read_and_filter_connections(input_file_path, output_file_path)

    
    def copy_intfin_to_Ffolders(self):

        ## Copying intf.in to other F* folders and also change all the F* inside it to the corresponding folder.

        def update_and_copy_intf_in(src_file, dst_file, src_folder, dst_folder):
            # Read the source file
            with open(src_file, 'r') as file:
                lines = file.readlines()

            # Replace the source folder identifier with the destination folder identifier
            updated_lines = [line.replace(src_folder, dst_folder) for line in lines]

            # Write the updated lines to the destination file
            with open(dst_file, 'w') as file:
                file.writelines(updated_lines)

        def process_directories(base_path, IW_number):
            # Define the source directory and file
            src_folder = f'F{IW_number}'
            src_file = os.path.join(base_path, src_folder, 'intf.in')

            # List all directories in the base path
            directories = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]

            # Filter directories starting with 'F'
            f_directories = [d for d in directories if re.match(r'F\d', d)]

            # Process each F* directory
            for dst_folder in f_directories:
                if dst_folder != src_folder:
                    dst_file = os.path.join(base_path, dst_folder, 'intf.in')
                    update_and_copy_intf_in(src_file, dst_file, src_folder, dst_folder)
                    # print(f"Copied and updated intf.in from {src_folder} to {dst_folder}.")


        process_directories(self.path_work, self.list_of_IW_numbers[0])