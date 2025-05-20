import os
import glob

def create_required_directories(path_work, IW_number):

    # Iterate over each number in the IW_number list
    for number in IW_number:
        # Create the main directory
        main_dir = os.path.join(path_work, 'F' + str(number))
        os.makedirs(main_dir, exist_ok=True)

        # Create the 'raw' subdirectory
        raw_dir = os.path.join(main_dir, 'raw')
        os.makedirs(raw_dir, exist_ok=True)
        
        # Create the 'topo' subdirectory
        topo_dir = os.path.join(main_dir, 'topo')
        os.makedirs(topo_dir, exist_ok=True)

    # # Creating a topo folder next to F# folder

    os.makedirs(path_work + 'topo/', exist_ok=True)
    os.makedirs(path_work + 'orbit/', exist_ok=True)
    os.makedirs(path_work + 'merge/', exist_ok=True)

def create_symboliklink_EOF(path_base, path_work):

    # 3- The EOF orbit files must also be copied to 'raw' folder.

    for item in os.listdir(path_base):
        if item.endswith('.EOF'):
            # Construct the full path to the current .SAFE folder
            EOF_path = os.path.join(path_base, item)
            destination_file_path = os.path.join(path_work + 'orbit', item)
            # shutil.copy2(EOF_path, destination_file_path)
            os.symlink(EOF_path, destination_file_path)

    ## Symbolic links of .EOF files
    orbit_directory = os.path.join(path_work, 'orbit')

    # Get list of .eof files in the orbit directory
    eof_files = glob.glob(os.path.join(orbit_directory, '*.EOF'))

    # Iterate through all directories in the main directory
    for folder_name in os.listdir(path_work):
        folder_path = os.path.join(path_work, folder_name)
        
        # Check if the item is a directory and matches the pattern F1, F2, F3, etc.
        if os.path.isdir(folder_path) and folder_name.startswith('F') and folder_name[1:].isdigit():
            raw_folder_path = os.path.join(folder_path, 'raw')

            # Ensure the raw folder exists in the current directory
            if os.path.exists(raw_folder_path):
                # Create symbolic links for each .eof file
                for eof_file in eof_files:
                    link_name = os.path.join(raw_folder_path, os.path.basename(eof_file))
                    os.symlink(eof_file, link_name)


def create_symboliklink_Tif(path_base, path_work, list_of_IW_numbers):
    
    for IW_number in list_of_IW_numbers:
        # Loop through all items in the base directory
        for item in os.listdir(path_base):
            if item.endswith('.SAFE'):
                # Construct the full path to the current .SAFE folder
                safe_folder_path = os.path.join(path_base, item)

                # Paths to the 'measurement' and 'annotation' folders
                measurement_folder_path = os.path.join(safe_folder_path, 'measurement')
                annotation_folder_path = os.path.join(safe_folder_path, 'annotation')

                # Search for the .tiff file in the 'measurement' folder
                for file in os.listdir(measurement_folder_path):
                    if file.endswith('.tiff'):
                        if f'iw{IW_number}' in file:
                            source_file_path = os.path.join(measurement_folder_path, file)
                            destination_file_path = os.path.join(path_work + 'F' + str(IW_number) + '/' + 'raw', file)

                            os.symlink(source_file_path, destination_file_path)

                            # shutil.copy2(source_file_path, destination_file_path)

                # Search for the .xml file in the 'annotation' folder
                for file in os.listdir(annotation_folder_path):
                    if file.endswith('.xml'):
                        if f'iw{IW_number}' in file:
                            source_file_path = os.path.join(annotation_folder_path, file)
                            destination_file_path = os.path.join(path_work + 'F' + str(IW_number) + '/' + 'raw', file)
                            # shutil.copy2(source_file_path, destination_file_path)
                            os.symlink(source_file_path, destination_file_path)