import os
import subprocess
import shutil

class Referencing():

    def __init__(self, path_work, lat_reference, lon_reference, neighbourhoodsize):

        self.path_work = path_work
        self.lat_reference = lat_reference
        self.lon_reference = lon_reference
        self.neighbourhoodsize = neighbourhoodsize

    def referencing(self):
        
        print('start point referencing procedure...')
        # Create the content for the reference_point.ll file
        content = f"{self.lon_reference} {self.lat_reference}"

        # Specify the directory and file name
        directory = self.path_work + 'merge/'
        file_name = "reference_point.ll"
        file_path = f"{directory}/{file_name}"

        # Write the content to the file
        with open(file_path, "w") as file:
            file.write(content)


        # get height value of reference point from DEM

        os.chdir(self.path_work + 'merge/')
        subprocess.run(['tcsh', '-c', 'gmt grdtrack reference_point.ll -Gdem.grd > reference_point.llh'])

        #Copies reference_point.llh to the first folder in merge
        #Reads the supermaster.PRM file in that folder to get the .LED value.
        #Checks if the .LED file exists in the same folder.
        #If not, searches in the main_source_directory and copies the led_file to the initial folder.

        folders = [f for f in sorted(os.listdir(directory)) if os.path.isdir(os.path.join(directory, f))]

        # Get the first folder in the sorted list
        first_folder = folders[0]
        first_folder_path = os.path.join(directory, first_folder)

        # Copy reference_point.llh to the first folder
        reference_point_file = os.path.join(directory, 'reference_point.llh')
        destination_reference_point_file = os.path.join(first_folder_path, 'reference_point.llh')
        shutil.copy(reference_point_file, destination_reference_point_file)

        # Read the supermaster.PRM file
        prm_file_path = os.path.join(first_folder_path, 'supermaster.PRM')

        if not os.path.exists(prm_file_path):
            print(f"supermaster.PRM not found in {first_folder_path}")
        else:
            led_file_value = None
            with open(prm_file_path, 'r') as prm_file:
                for line in prm_file:
                    if line.startswith('led_file'):
                        led_file_value = line.split('=')[1].strip()

        if not led_file_value:
            print("led_file value not found in supermaster.PRM")

        # Check if the led_file exists in the same folder
        led_file_path = os.path.join(first_folder_path, led_file_value)

        if os.path.exists(led_file_path) or os.path.islink(led_file_path):
            pass
            # print(f"{led_file_value} already exists in {first_folder_path}")
        else:
            # If the file does not exist, find and copy it from the main_source_directory
            led_file_parts = led_file_value.split('_')
            f_folder = led_file_parts[-1].split('.')[0]  # Extract F* (e.g., F1)

            source_folder = os.path.join(self.path_work, f_folder, 'raw') # main_source_directory is from Harddrive
            source_led_file_path = os.path.join(source_folder, led_file_value)
            shutil.copy(source_led_file_path, first_folder_path)

        os.chdir(first_folder_path)
        subprocess.run(['tcsh', '-c', 'SAT_llt2rat supermaster.PRM 1 < reference_point.llh > reference_point.rahll'])

        reference_point_file = os.path.join(first_folder_path, 'reference_point.rahll')
        destination_reference_point_file = os.path.join(directory, 'reference_point.rahll')
        shutil.copy(reference_point_file, destination_reference_point_file)


        def create_csh_script(directory, threshold):
            # Read the reference point from reference_point.rahll file
            with open(os.path.join(directory, 'reference_point.rahll'), 'r') as file:
                line = file.readline()
                ref_point = line.split()
                x_coord = int(float(ref_point[0]))
                y_coord = int(float(ref_point[1]))

            # Calculate region
            x_min = x_coord - int(threshold)
            x_max = x_coord + int(threshold)
            y_min = y_coord - int(threshold)
            y_max = y_coord + int(threshold)

            region = f"{x_min}/{x_max}/{y_min}/{y_max}"

            # Create the .csh script content
            script_content = f"""#!/bin/csh

        # Setting the ref region in radar coordinates
        set region = "{region}"
        foreach folder (`ls -d 20*`)
        cd $folder
        gmt grdcut unwrap.grd -R$region -Gtmp.grd
        set a = `gmt grdinfo tmp.grd -L2 -C | awk '{{print $12}}'`
        gmt grdmath unwrap.grd $a SUB = unwrap_pin.grd
        cd ..
        end
        """


            # Write the script content to a .csh file
            script_path = os.path.join(directory, 'unwrap_referencepoint.csh')
            with open(script_path, 'w') as script_file:
                script_file.write(script_content)

            # Make the .csh file executable
            os.chmod(script_path, 0o755)

        # Example usage
        directory = self.path_work + 'merge/'  # Replace with your directory path

        create_csh_script(directory, self.neighbourhoodsize)

        os.chdir(directory)
        subprocess.run(['unwrap_referencepoint.csh'], shell=True, check=True, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print('Creating PDF of unwrap.grd...')
        ### I want to create a unwrap_pin.pdf file of all unwrap_pin

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

        print('Referencing Finished...')