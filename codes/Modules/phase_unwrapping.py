import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import subprocess

class PhaseUnwrapping():

    def __init__(self, path_work, TH1_unwrapping, TH2_unwrapping, first_column, last_column, first_row, last_row, n_jobs_for_unwrapping):

        self.path_work = path_work
        self.TH1_unwrapping = TH1_unwrapping
        self.TH2_unwrapping = TH2_unwrapping
        self.first_column = first_column
        self.last_column = last_column
        self.first_row = first_row
        self.last_row = last_row
        self.n_jobs_for_unwrapping = n_jobs_for_unwrapping


    def create_unwrapcsh(self):

        print('Writing unwrap_intf.csh...')
        #### Preparing unwrap_intf.csh

        # Construct the content of the shell script

        # Define the script content with placeholders
        script_content = f"""#!/bin/csh -f
        # intflist contains a list of all date1_date2 directories.
        foreach dir (`cat $1`)
            cd $dir
            snaphu_interp.csh {self.TH1_unwrapping} {self.TH2_unwrapping} {self.first_column}/{self.last_column}/{self.first_row}/{self.last_row}
            cd ..
        end
        """

        # Write the content to unwrap_intf.csh
        with open('/usr/local/GMTSAR/bin/unwrap_intf_mine.csh', "w") as file:
            file.write(script_content)


    def parallel_unwrapping(self):
        # Parallel processing of unwrapping

        # I have to create a file: intflist whith the names of all the folders in intf_all main folder.
        print('Unwrapping starts...')
        directory = self.path_work + 'merge/'
        dirs = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
        dirs.sort()

        with open(self.path_work + 'merge/intflist', 'w') as file:
            # Write each item in the list to the file on a new line
            for item in dirs:
                file.write(f"{item}\n")  # The '\n' ensures each item is on a new line


        # Splitting intflist
        def split_file(input_file, output_directory, num_parts):

            # Read all lines from the file
            with open(input_file, 'r') as file:
                lines = file.readlines()

            # Calculate the number of lines per file
            total_lines = len(lines)
            part_size = total_lines // num_parts
            remainder = total_lines % num_parts

            part_files = []

            # Write each part to a new file
            for i in range(num_parts):
                start_index = i * part_size + min(i, remainder)
                end_index = start_index + part_size + (1 if i < remainder else 0)
                part_lines = lines[start_index:end_index]
                
                # Construct the filename
                part_filename = f"intflist{i+1}"
                part_path = os.path.join(output_directory, part_filename)

                # Write to the part file
                with open(part_path, 'w') as part_file:
                    part_file.writelines(part_lines)

                part_files.append(part_filename)

            return part_files

        input_file = self.path_work + 'merge/intflist'
        output_directory = self.path_work + 'merge/'
        num_parts = self.n_jobs_for_unwrapping

        part_files = split_file(input_file, output_directory, num_parts)


        directory = '/usr/local/GMTSAR/bin/'  # Replace with your directory path

        # Define the original script path
        original_script = os.path.join(directory, 'unwrap_intf_mine.csh')

        for i in range(1, num_parts + 1):
            new_script = os.path.join(directory, f'unwrap_intf_mine{i}.csh')
            shutil.copyfile(original_script, new_script)

        # 21- Phase unwrapping
        # I first need to make sure that unwrap_intf.csh is executable in /usr/local/GMTSAR/bin/. So:

        # Define the directory containing the scripts
        directory = '/usr/local/GMTSAR/bin/'

        # Change to the directory
        os.chdir(directory)

        # Make unwrap_intf_mine*.csh scripts executable where * is from 1 to n
        for i in range(1, num_parts + 1):
            script_name = f"unwrap_intf_mine{i}.csh"
            subprocess.run(f"tcsh -c 'chmod +x {script_name}'", shell=True, check=True, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Function to execute a single script
        def run_script(script_index):
            os.chdir(self.path_work + 'merge/')
            script_name = f"unwrap_intf_mine{script_index}.csh"
            intflist_name = f"intflist{script_index}"
            command = f"tcsh -c '{script_name} {intflist_name}'"
            subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Run all scripts concurrently
        with ThreadPoolExecutor() as executor:
            executor.map(run_script, range(1, num_parts + 1))

        print('Unwrapping finishing...')

        ## Clear all the intflist1, intflist2, and ... but preserving intflist

        def clean_int_files(directory):
            # List all files in the directory
            for file_name in os.listdir(directory):
                # Check if the file name starts with 'intf', ends with '.in', and has more than 'intf.in'
                if file_name.startswith('intflist') and file_name != 'intflist':
                    file_path = os.path.join(directory, file_name)
                    # Delete the file
                    os.remove(file_path)

        clean_int_files(self.path_work + 'merge/')

        ## Clear all the unwrap_intf1.csh, unwrap_intf2.csh, and ... but preserving unwrap_intf.csh

        def clean_int_files(directory):
            # List all files in the directory
            for file_name in os.listdir(directory):
                # Check if the file name starts with 'intf', ends with '.in', and has more than 'intf.in'
                if file_name.startswith('unwrap_intf_mine') and file_name != 'unwrap_intf.csh':
                    file_path = os.path.join(directory, file_name)
                    # Delete the file
                    os.remove(file_path)

        clean_int_files('/usr/local/GMTSAR/bin/')