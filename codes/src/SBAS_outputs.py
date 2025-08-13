import subprocess
import os
import shutil
import rasterio
from rasterio.enums import Resampling
# from osgeo import gdal

class SBASoutputs:

    def __init__(self, path_work, filter_wavelength_resolution):

        self.path_work = path_work
        self.filter_wavelength_resolution = filter_wavelength_resolution


    def create_vel_llgrd(self):

        print('Exporting Started...')

        # 23-SBAS outputs
        # Specify the working directory where the commands will be executed
        working_directory = self.path_work + 'SBAS/'

        # Change the working directory
        os.chdir(working_directory)

        # 400 directly effects the output reolution. this is because I set decimation 5x20 so the resoltion will be ~100m. Since the command considers
        # 1/4 of the 400, so the output will be fine. Even 360 is also so close with no gaps.

        #if you want to find the right value for this command (by running the code for several times), 
        # you have to first clean these files if they exist and then run the command:

        commands = [
            f"proj_ra2ll.csh trans.dat vel.grd vel_ll.grd {self.filter_wavelength_resolution}",
            "gmt grd2cpt vel_ll.grd -T= -Z -Cjet > vel_ll.cpt",
            "grd2kml.csh vel_ll vel_ll.cpt"
        ]
        complete_command = " && ".join(commands)

        # Add the tcsh wrapper
        command = f"tcsh -c '{complete_command}'"

        subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


    def grds_to_grdll(self):
        # 24- Converting Displacement.grd files to lat and long
        # Define the directory containing the `.grd` files

        working_directory = self.path_work + 'SBAS/'

        # Change to the working directory
        os.chdir(working_directory)

        # Get the list of `.grd` files matching the pattern 'disp_*.grd'
        grd_files = [f for f in os.listdir(working_directory) if f.startswith("disp_") and f.endswith(".grd")]

        # Loop through each `.grd` file and run the `proj_ra2ll.csh` command
        for grd_file in grd_files:
            # Extract the base name without the file extension
            base_name = os.path.splitext(grd_file)[0]
            ll_grd_file = f"{base_name}_ll.grd"  # Generate the new `.grd` file name

            # Create the command string
            command = f"tcsh -c 'proj_ra2ll.csh trans.dat {grd_file} {ll_grd_file} {self.filter_wavelength_resolution}'"

            result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Define the destination directory where files will be moved
        # destination_directory = path_work + 'F' + str(IW_number) + '/SBAS/disp_ll_grd'
        destination_directory = working_directory + '/disp_ll_grd'

        # Create the destination directory if it doesn't exist
        os.makedirs(destination_directory, exist_ok=True)

        # Iterate through all files in the source directory
        for filename in os.listdir(working_directory):
            # Check if the file name starts with 'disp' and ends with 'll.grd'
            if filename.startswith('disp') and filename.endswith('ll.grd'):
                # Build the full path for the source and destination
                source_file = os.path.join(working_directory, filename)
                destination_file = os.path.join(destination_directory, filename)

                # Move the file from source to destination
                shutil.move(source_file, destination_file)


    def grdll_to_geotif(self):
        # Exporting final outputs to geotiff data



        def convert_grd_to_geotiff(input_grd, output_tiff): # Converts each grd file to exact tif file (grd file must have a coordinate system)
            # Define the CRS from the provided projection system
            crs = 'EPSG:4326'  # WGS 84

            with rasterio.open(input_grd) as src:
                transform = src.transform

                meta = src.meta.copy()
                meta.update({
                    'driver': 'GTiff',
                    'crs': crs,
                    'transform': transform
                })

                # Read and resample the data
                data = src.read(
                    out_shape=(
                        src.count,
                        int(src.height), int(src.width)
                    ),
                    resampling=Resampling.nearest
                )

                # Write the data to a new GeoTIFF file
                with rasterio.open(output_tiff, 'w', **meta) as dst:
                    dst.write(data)


        def process_directory(directory):
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith("ll.grd"):
                        input_file = os.path.join(root, file)
                        output_file = os.path.splitext(input_file)[0] + ".tif"
                        convert_grd_to_geotiff(input_file, output_file)

        process_directory(self.path_work + 'SBAS/disp_ll_grd/')

        # Also converting the vel_ll.grd to geotiff.

        convert_grd_to_geotiff(self.path_work + 'SBAS/vel_ll.grd', self.path_work + 'SBAS/vel_ll.tif')

        print('Exporting Finished...')