import os
import subprocess
import numpy as np

class Coregistration:

    def __init__(self, path_work, list_of_IW_numbers):

        self.path_work = path_work
        self.list_of_IW_numbers = list_of_IW_numbers


    def coregistration(self):

        for IW_number in self.list_of_IW_numbers:

            print(f'Start of image coregistration in IW{IW_number}...')
            # Define the directory where the script and data.in file are located
            directory = self.path_work + 'F' + str(IW_number) + '/' + 'raw/'
            os.chdir(directory)  # Change the working directory to where the script is

            # Command to execute the script using tcsh shell
            # command = "tcsh -c 'preproc_batch_tops.csh data.in dem.grd 2'"

            # This is for paralleling the code
            command = "tcsh -c 'preproc_batch_tops_parallel.csh data.in dem.grd 8 2'" 

            # Run the command
            try:
                # result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                result = subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # print("Output:", result.stdout)
                # print("Error:", result.stderr)
            except subprocess.CalledProcessError as e:
                print("An error occurred while executing the shell command.")

            # I want to check whether all the .SLC files are correctly written

            # List to store the file names and sizes
            files_with_sizes = []
            
            # Loop through the directory
            for file in os.listdir(directory):
                if file.endswith(".SLC"):
                    file_path = os.path.join(directory, file)
                    size = os.path.getsize(file_path) / (1024 * 1024)  # Get size in megabytes
                    files_with_sizes.append((file, size))

            sizes = [size for _, size in files_with_sizes]
            median_size = np.median(sizes)

            files_out_of_range = []

            range_mb = 5

            for file, size in files_with_sizes:
                if size < median_size - range_mb or size > median_size + range_mb:
                    files_out_of_range.append((file, size))

            if len(files_out_of_range)==0:

                print(f'Finishing coregistration in IW{IW_number}...')

            else:

                print("Files outside of the median size:")
                for file, size in files_out_of_range:
                    print(f"{file}: {size:.2f} MB")