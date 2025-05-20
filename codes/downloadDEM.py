import os
import glob
import xml.etree.ElementTree as ET
import numpy as np
import math
import simplekml
import subprocess               

# IF you have multipleSwaths, it goes to one of .SAFE files randomly, gets the two .xml files and then download the whole swaths DEM

class DEMdownloader:

    def __init__(self, path_base, path_work):
        self.path_base = path_base
        self.path_work = path_work

    def get_first_safe_annotation_xml_files(self):

        # List all .SAFE directories in the parent directory
        safe_dirs = sorted([d for d in os.listdir(self.path_base) if d.endswith('.SAFE')])
        
        if not safe_dirs:
            return []
        
        # Get the first .SAFE directory (sorted alphabetically)
        first_safe_dir = safe_dirs[0]
        
        # Path to the annotation folder within the first .SAFE directory
        annotation_folder = os.path.join(self.path_base, first_safe_dir, 'annotation')
        
        
        # List all .xml files in the annotation folder
        xml_files = glob.glob(os.path.join(annotation_folder, '*.xml'))
        
        return xml_files
    

    def get_boundingbox_from_xml(self, annotation_file):
        """Extract the bounding box from the XML file."""
        tree = ET.parse(annotation_file)
        root = tree.getroot()

        geolocation_points = []
        for point in root.findall(".//geolocationGridPoint"):
            data = {
                'line': point.find('line').text if point.find('line') is not None else None,
                'pixel': point.find('pixel').text if point.find('pixel') is not None else None,
                'latitude': point.find('latitude').text if point.find('latitude') is not None else None,
                'longitude': point.find('longitude').text if point.find('longitude') is not None else None,
            }
            geolocation_points.append(data)

        max_line = max(geolocation_points, key=lambda x: int(x['line']))['line']
        max_pixel = max(geolocation_points, key=lambda x: int(x['pixel']))['pixel']

        def find_coordinates(line, pixel):
            for coord in geolocation_points:
                if coord['line'] == line and coord['pixel'] == pixel:
                    return coord['latitude'], coord['longitude']
            return None

        point_line_0_pixel_0 = find_coordinates('0', '0')
        point_line_0_pixel_max = find_coordinates('0', max_pixel)
        point_line_max_pixel_0 = find_coordinates(max_line, '0')
        point_line_max_pixel_max = find_coordinates(max_line, max_pixel)

        bounding_box_coordinates_SN = np.array([float(point_line_0_pixel_0[0]), 
                                                float(point_line_0_pixel_max[0]),
                                                float(point_line_max_pixel_max[0]),
                                                float(point_line_max_pixel_0[0])])

        bounding_box_coordinates_EW = np.array([float(point_line_0_pixel_0[1]), 
                                                float(point_line_0_pixel_max[1]),
                                                float(point_line_max_pixel_max[1]),
                                                float(point_line_max_pixel_0[1])])

        bounding_box_DEM = np.zeros(4)

        bounding_box_DEM[3] = math.ceil((np.max(bounding_box_coordinates_SN) + 0.1) * 10) / 10  # N
        bounding_box_DEM[1] = math.ceil((np.max(bounding_box_coordinates_EW) + 0.1) * 10) / 10  # E
        bounding_box_DEM[2] = round(np.min(bounding_box_coordinates_SN) - 0.1, 1)  # S
        bounding_box_DEM[0] = round(np.min(bounding_box_coordinates_EW) - 0.1, 1)  # W

        return bounding_box_DEM
    
    def compute_combined_bounding_box(self, all_bounding_boxes):
        """Compute the combined bounding box from all individual bounding boxes."""
        combined_bounding_box = np.zeros(4)
        combined_bounding_box[0] = min(bb[0] for bb in all_bounding_boxes)  # Min longitude (West)
        combined_bounding_box[1] = max(bb[1] for bb in all_bounding_boxes)  # Max longitude (East)
        combined_bounding_box[2] = min(bb[2] for bb in all_bounding_boxes)  # Min latitude (South)
        combined_bounding_box[3] = max(bb[3] for bb in all_bounding_boxes)  # Max latitude (North)
        return combined_bounding_box

    def create_kml_file(self, combined_bounding_box):
        """Create a KML file with the combined bounding box."""
        kml = simplekml.Kml()

        # Define the coordinates for the bounding box (clockwise)
        coords = [
            (combined_bounding_box[0], combined_bounding_box[2]),  # West, South
            (combined_bounding_box[1], combined_bounding_box[2]),  # East, South
            (combined_bounding_box[1], combined_bounding_box[3]),  # East, North
            (combined_bounding_box[0], combined_bounding_box[3]),  # West, North
            (combined_bounding_box[0], combined_bounding_box[2])   # Closing the loop
        ]

        # Add a polygon to the KML
        pol = kml.newpolygon(name="BoundingBox", outerboundaryis=coords)
        pol.style.linestyle.color = simplekml.Color.red  # Optional: set line color
        pol.style.linestyle.width = 2  # Optional: set line width
        pol.style.polystyle.color = simplekml.Color.changealphaint(100, simplekml.Color.yellow)  # Optional: set fill color with transparency

        # Save the KML to a file
        kml.save(os.path.join(self.path_work, 'topo', 'DEM_boundingbox.kml'))


    def download_dem(self, combined_bounding_box):
        """Download the DEM using the combined bounding box."""
        directory_to_save = os.path.join(self.path_work, 'topo')

        # Construct the command
        command = [
            "make_dem.csh",
            str(combined_bounding_box[0]),
            str(combined_bounding_box[1]),
            str(combined_bounding_box[2]),
            str(combined_bounding_box[3]),
            "1"
        ]

        # Change to the desired directory
        os.chdir(directory_to_save)

        # Run the command, suppressing the output
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print("DEM download complete...")


    # Symbolic links of dem.grd to all F# folders and merge folder
    def symboliklink_DEM(self):

        # Path to the dem.grd file in the topo folder of the main directory
        source_file = os.path.join(self.path_work, 'topo', 'dem.grd')

        # Ensure the source file exists
        if not os.path.isfile(source_file):
            print(f"The source file {source_file} does not exist.")
            exit(1)

        # Iterate through all directories in the main directory
        for folder_name in os.listdir(self.path_work):
            folder_path = os.path.join(self.path_work, folder_name)

            # Check if the item is a directory and matches the pattern F1, F2, F3, etc.
            if os.path.isdir(folder_path) and folder_name.startswith('F') and folder_name[1:].isdigit():
                topo_folder_path = os.path.join(folder_path, 'topo')

                # Ensure the topo folder exists in the current directory
                if os.path.exists(topo_folder_path):
                    # Path for the symbolic link
                    link_name = os.path.join(topo_folder_path, 'dem.grd')
                    os.symlink(source_file, link_name)

            # Check if the item is a directory and matches the pattern F1, F2, F3, etc.
            if os.path.isdir(folder_path) and folder_name.startswith('F') and folder_name[1:].isdigit():
                raw_folder_path = os.path.join(folder_path, 'raw')

                # Ensure the raw folder exists in the current directory
                if os.path.exists(raw_folder_path):
                    # Path for the symbolic link
                    link_name = os.path.join(raw_folder_path, 'dem.grd')
                    os.symlink(source_file, link_name)
            

            # Check if the item is a directory and matches the pattern F1, F2, F3, etc.
            if os.path.isdir(folder_path) and folder_name.startswith('merge'):
                link_name = os.path.join(folder_path, 'dem.grd')
                os.symlink(source_file, link_name)




    def process(self):
        """Main processing function."""

        xml_file_paths = self.get_first_safe_annotation_xml_files()

        all_bounding_boxes = []
        for xml_file in xml_file_paths:
            bounding_box = self.get_boundingbox_from_xml(xml_file)
            all_bounding_boxes.append(bounding_box)

        # Compute the combined bounding box
        combined_bounding_box = self.compute_combined_bounding_box(all_bounding_boxes)

        # Create a KML file
        self.create_kml_file(combined_bounding_box)

        # Download DEM
        self.download_dem(combined_bounding_box)

        #Symbolik link
        self.symboliklink_DEM()