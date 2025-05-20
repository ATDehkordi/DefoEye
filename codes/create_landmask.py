import os
import subprocess
import re


class Landmask:

    def __init__(self, path_work):

        self.path_work = path_work

    def create_land_mask(self):

        # 20- So far, all the interferograms are generated. I want to create a landmask for removing water-related regions
        # For creating a landmask, I need grid x and y coordinates which can be accessed in one of the intf folders in merge

        directory = self.path_work + 'merge/'

        dirs = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
        dirs.sort()  # Sort the directories alphabetically

        os.chdir(os.path.join(directory, dirs[0])) # Randomly select the first one

        command = f'gmt grdinfo phasefilt.grd'
            
        result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
        
        def extract_grid_info(grdinfo_output):
            # Regular expression to find the x_min, x_max, y_min, y_max
            x_min_max_pattern = r"x_min: ([\d\.]+) x_max: ([\d\.]+)"
            y_min_max_pattern = r"y_min: ([\d\.]+) y_max: ([\d\.]+)"

            # Search for x_min and x_max
            x_match = re.search(x_min_max_pattern, grdinfo_output)
            if x_match:
                x_min, x_max = x_match.groups()
            else:
                x_min, x_max = None, None

            # Search for y_min and y_max
            y_match = re.search(y_min_max_pattern, grdinfo_output)
            if y_match:
                y_min, y_max = y_match.groups()
            else:
                y_min, y_max = None, None

            return {
                'x_min': x_min,
                'x_max': x_max,
                'y_min': y_min,
                'y_max': y_max
            }

        grid_info = extract_grid_info(result)


        # Now I have 4 grids, so I make landmask it topo folder (I tested different folders and only topo was successfull)

        print('Creating landmask for phase unwrapping...')

        os.chdir(self.path_work + 'merge/') # Randomly select the first one
        command = f"landmask.csh {grid_info['x_min']}/{grid_info['x_max']}/{grid_info['y_min']}/{grid_info['y_max']}"
        # result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


        # Linking the landmask to all of interferograms

        target_directory = self.path_work + 'merge/'
        landmaskfile = self.path_work + 'merge/landmask_ra.grd'

        for entry in os.listdir(target_directory):
                    subdir = os.path.join(target_directory, entry)
                    if os.path.isdir(subdir):  # Check if it is a directory
                        link_path = os.path.join(subdir, os.path.basename(landmaskfile))
                        # Create the symbolic link
                        try:
                            subprocess.run(['ln', '-sfn', landmaskfile, link_path], check=True)
                            # print(f"Linked {source_file} to {link_path}")
                        except subprocess.CalledProcessError as e:
                            print(f"Failed to create link in {subdir}: {e}")


        print('Finishing landmask for phase unwrapping...')
