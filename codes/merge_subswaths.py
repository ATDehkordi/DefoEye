import os
import datetime
import subprocess
import concurrent.futures
import rasterio

class merge:

    def __init__(self, path_work, list_of_IW_numbers, n_jobs_for_merging = 10):

        self.path_work = path_work
        self.list_of_IW_numbers = list_of_IW_numbers
        self.n_jobs_for_merging = n_jobs_for_merging

    def create_merge_requirementfiles(self):

        # List to hold all the formatted strings to be written to file.
        merge_list = []

        # Folders to check, typically F1, F2, and F3
        folders = ['F1', 'F2', 'F3']

        # Gather all directories in intf_all from any of F* folders
        intf_all_dirs = set()
        for folder in folders:
            path = os.path.join(self.path_work, folder, 'intf_all')
            if os.path.exists(path):
                for subfolder in os.listdir(path):
                    intf_all_dirs.add(subfolder)


        # Process each directory found in any intf_all
        for dir_name in sorted(intf_all_dirs):
            row_entries = []
            for folder in folders:
                intf_path = os.path.join(self.path_work, folder, 'intf_all', dir_name)
                if os.path.exists(intf_path):
                    # Find all .PRM files in this directory
                    prm_files = [f for f in os.listdir(intf_path) if f.endswith('.PRM')]
                    required_files = ['phasefilt.grd', 'corr.grd', 'mask.grd']
                    files_exist = all(os.path.exists(os.path.join(intf_path, rf)) for rf in required_files)

                    if len(prm_files) == 2 and files_exist:
                        prm_files.sort()
                        # Construct the path and filename string
                        row_entries.append(f"../{folder}/intf_all/{dir_name}/:{prm_files[0]}:{prm_files[1]}")
                    # elif not files_exist: # Since I have already checked all of intf in the last stage, I do not need it.
                    #     # Print the folder and directory name if required files are missing
                    #     missing_files = ', '.join([rf for rf in required_files if not os.path.exists(os.path.join(intf_path, rf))])
                    #     print(f"Missing {missing_files} in {folder}/intf_all/{dir_name}")

            # Only add to merge_list if there are entries for this directory
            if row_entries:
                merge_list.append(','.join(row_entries))


        merge_file_path = os.path.join(self.path_work, 'merge', 'merge_list')
        os.makedirs(os.path.dirname(merge_file_path), exist_ok=True)
        with open(merge_file_path, 'w') as file:
            for entry in merge_list:
                file.write(entry + '\n')

        def convert_date_to_format(yyyymmdd):
            """ Convert date from YYYYMMDD to the format used in the list. """
            date = datetime.datetime.strptime(yyyymmdd, "%Y%m%d")
            start_of_year = datetime.datetime(date.year, 1, 1)
            day_of_year = (date - start_of_year).days
            return f"{date.year}{day_of_year:03d}"  # ensures day_of_year is a three-digit number
        
        # Open the master_date.txt file in read mode
        with open(self.path_work + 'master_date.txt', 'r') as file:
            # Read the content and strip any trailing newline or whitespace characters
            master_date = file.read().strip()
        
        master_date = convert_date_to_format(master_date)


        def modify_file(merge_list_path, master_date):

            # Read the existing data from the file
            with open(merge_list_path, 'r') as file:
                lines = file.readlines()

            # Find the first line containing the master_date and bring it to the top
            for i, line in enumerate(lines):
                if master_date==str(line.split('/')[3][0:7]):
                    # Move this line to the top of the list
                    lines.insert(0, lines.pop(i))
                    break

            # Save the modified list back to the file
            with open(merge_list_path, 'w') as file:
                file.writelines(lines)

            return lines

        lines = modify_file(self.path_work + 'merge/merge_list', master_date)

        original_file_path = f'{self.path_work}F{self.list_of_IW_numbers[0]}/batch_tops.config'
        source_directory = self.path_work + 'merge/'

        symlink_path = os.path.join(source_directory, 'batch_tops.config')
        os.symlink(original_file_path, symlink_path)

        # Splitting merge_list file to different parts. the first part creates the trans.dat file. then all of intf are merged in a parallel manner.
        # Merging can be parallel because: 
        # # You can parallel the process since it is written in gmtsar handbook that: be aware that merge_batch.csh will not overwrite an existing trans.dat file when it runs the next time.

        input_file = os.path.join(self.path_work + 'merge/', 'merge_list')
        output_prefix = os.path.join(self.path_work + 'merge/', 'merge_list')

        # Read the input file
        with open(input_file, 'r') as file:
            lines = file.readlines()

        # Write the first two rows to merge_list1
        with open(f'{output_prefix}1', 'w') as file:
            file.writelines(lines[:2])

        num_parts = self.n_jobs_for_merging

        # Split the remaining lines into parts
        remaining_lines = lines[2:]
        num_lines_per_part = len(remaining_lines) // num_parts
        extra_lines = len(remaining_lines) % num_parts

        start = 0
        for i in range(2, num_parts + 2):
            end = start + num_lines_per_part + (1 if i <= extra_lines + 1 else 0)
            with open(f'{output_prefix}{i}', 'w') as file:
                file.writelines(remaining_lines[start:end])
            start = end

    def merge_first(self):
        print('Starting to merge the first intf...')
        # Merging first part
        directory = self.path_work + 'merge/'
        os.chdir(directory)  # Change the working directory to where the script is

        # Command to execute the script using tcsh shell
        command = "tcsh -c 'merge_batch.csh merge_list1 batch_tops.config'"

        # Run the command
        try:
            # result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # print("Output:", result.stdout)
            # print("Error:", result.stderr)
        except subprocess.CalledProcessError as e:
            print("An error occurred while executing the shell command.")

    def merge_otherintfs(self):
        print('Starting to merge other intfs...')
        # Merging other parts

        def run_command(command, directory):
            # Run the command and suppress output by redirecting stdout and stderr to DEVNULL
            subprocess.run(command, shell=True, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=directory)

        commands = [f"tcsh -c 'merge_batch.csh merge_list{merge_part_number} batch_tops.config'" for merge_part_number in range(2, self.n_jobs_for_merging + 2)]

        # Using ThreadPoolExecutor to run commands in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Map the run_command function to the commands, providing the directory for each
            futures = {executor.submit(run_command, cmd, self.path_work + 'merge/'): cmd for cmd in commands}


        ### Removing all merge_list files from the directory

        def clean_merge_list_files(directory):
            # List all files in the directory
            for file_name in os.listdir(directory):
                # Check if the file name starts with 'intf', ends with '.in', and has more than 'intf.in'
                if file_name.startswith('merge_list') and file_name != 'merge_list':
                    file_path = os.path.join(directory, file_name)
                    # Delete the file
                    os.remove(file_path)

        clean_merge_list_files(self.path_work + 'merge/')


    def create_pdf_of_merged(self):

        ### I want to create a corr.pdf file of all merged corr.grd files

        print('Creating PDFs of corr.grd of the merged intfs...')

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
                    subprocess.run(['tcsh', '-c', 'gmt psconvert temp.ps -A -P -Tf -Fcorr'])
                    subprocess.run(['tcsh', '-c', 'rm temp.ps'])
                else:
                    # Print the directory name if 'corr.grd' is not found
                    print(f"No corr.grd found in {subdir_path}")
                # Check if 'corr.grd' exists in the current subdirectory
                if 'phasefilt.grd' in os.listdir(subdir_path):
                    # Change the current working directory to the subdirectory containing 'corr.grd'
                    os.chdir(subdir_path)
                    subprocess.run(['tcsh', '-c', 'gmt grdimage phasefilt.grd -Crainbow -JX6i -P -K > temp.ps'])
                    subprocess.run(['tcsh', '-c', 'gmt psbasemap -Rphasefilt.grd -J -O -Bxa -Bya >> temp.ps'])
                    subprocess.run(['tcsh', '-c', 'gmt psconvert temp.ps -A -P -Tf -Fphasefilt'])
                    subprocess.run(['tcsh', '-c', 'rm temp.ps'])
                else:
                    # Print the directory name if 'corr.grd' is not found
                    print(f"No phasefilt.grd found in {subdir_path}")
        # Define the root directory to start the search
        root_directory = os.path.join(self.path_work, 'merge')

        # Call the function to process folders
        process_folders(root_directory)



    def check_merging(self):

        ## I want to check if the merging has been done correcting by checking the size of all "corr.grd", "mask.grd", "phasefilt.grd" files and returning the unique size
        ## It simultaneously check whether all the .grd files exist or not and also have the same size or not.

        def get_shape(file_path):
            with rasterio.open(file_path) as src:
            # Read the first band
                array = src.read(1)
                return array.shape
                
        def check_folder(folder_path):
            files = ["corr.grd", "mask.grd", "phasefilt.grd"]
            shapes = []
            for file_name in files:
                file_path = os.path.join(folder_path, file_name)
                if not os.path.exists(file_path):
                    print(f"File {file_name} not found in {folder_path}")
                    return None
                shape = get_shape(file_path)
                if shape is None:
                    return None
                shapes.append(shape)
            if shapes[0] == shapes[1] == shapes[2]:
                return shapes[0]
            else:
                print(f"Different shapes in folder: {folder_path}")
                return None
            

        directory = self.path_work + 'merge/'    
        unique_shapes = set()
        for root, dirs, files in os.walk(directory):
            for dir_name in dirs:
                folder_path = os.path.join(root, dir_name)
                shape = check_folder(folder_path)
                if shape:
                    unique_shapes.add(shape)

        if len(unique_shapes) == 1:
            print("Merging has been done successfully (Check was completed)")

        else:
            print("Merging error, check the outputs...")
            # print("Unique shapes found:")
            # for shape in unique_shapes:
            #     print(shape)