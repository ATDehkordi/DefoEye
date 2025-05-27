import os
from datetime import datetime
import subprocess
import shutil

class Create_baselinetable_of_S1_data:

    def __init__(self, path_work, list_of_IW_numbers):

        self.path_work = path_work
        self.list_of_IW_numbers = list_of_IW_numbers


    # 6- create a data.in file consisting of diffrent rows in raw folder, each row: tif file id without tif:EOF file with .EOF
    def create_datain_file(self):

        for IW_number in self.list_of_IW_numbers:

            files = os.listdir(self.path_work + 'F' + str(IW_number) + '/' + 'raw/')

            tif_files = sorted([file for file in files if file.endswith('.tiff')])
            eof_files = sorted([file for file in files if file.endswith('.EOF')])


            with open(os.path.join(self.path_work + 'F' + str(IW_number) + '/' + 'raw/', 'data.in'), 'w') as data_file:
                for i in range(len(tif_files)):
                    # Remove the '.tif' extension and extract the id for the .EOF
                    tif_date = tif_files[i][15:23]
                    tif_date = datetime.strptime(tif_date, '%Y%m%d')

                    for j in range(len(eof_files)):
                        start_date = eof_files[j][42:50]
                        end_date = eof_files[j][58:66]

                        start_date = datetime.strptime(start_date, '%Y%m%d')
                        end_date = datetime.strptime(end_date, '%Y%m%d')
                    
                        ## Here I want to check that the same date of EOF files come with the corresponding tiff files.
                        if start_date <= tif_date <= end_date:
                            # Write the formatted string to the file
                            data_file.write(f"{tif_files[i][:-5]}:{eof_files[j]}\n")


    def create_baselinetable_file(self):

        for IW_number in self.list_of_IW_numbers:

            # Define the directory where the script and data.in file are located
            directory = self.path_work + 'F' + str(IW_number) + '/' + 'raw/'
            os.chdir(directory)  # Change the working directory to where the script is

            # Command to execute the script using tcsh shell
            # command = "tcsh -c 'preproc_batch_tops.csh data.in dem.grd 1'"

            command = "tcsh -c 'preproc_batch_tops_parallel.csh data.in dem.grd 8 1'"

            # Run the command
            try:
                # result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                result = subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # print("Output:", result.stdout)
                # print("Error:", result.stderr)
            except subprocess.CalledProcessError as e:
                print("An error occurred while executing the shell command.")

            # 8- Copy baseline_table.dat file from raw folder to F2 folder
            shutil.copy2(self.path_work + 'F' + str(IW_number) + '/' + 'raw/' + 'baseline_table.dat', self.path_work + 'F' + str(IW_number) + '/' + 'baseline_table.dat')

            print(f'Baseline information of the images were computed for IW{IW_number}!')