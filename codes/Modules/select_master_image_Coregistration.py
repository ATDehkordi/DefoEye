import pandas as pd
import numpy as np
import os

class Master_selection:

    def __init__(self, path_work, list_of_IW_numbers):

        self.path_work = path_work
        self.list_of_IW_numbers = list_of_IW_numbers
    

    def giving_options(self):

        filename = self.path_work + 'F' + str(self.list_of_IW_numbers[0]) + '/' + 'raw/' + 'baseline_table.dat'

        # Read the file
        data = pd.read_csv(filename, sep=" ", header=None)
        
        # Assign column names for easier access
        data.columns = ['ID', 'Date', 'DoNotKnow1', 'DoNotKnow2', 'Baseline']

        # Calculate medians
        median_date = np.median(data['Date'])
        median_baseline = np.median(data['Baseline'])

        # Calculate the absolute differences from the medians
        data['Date_Diff'] = abs(data['Date'] - median_date)
        data['Baseline_Diff'] = abs(data['Baseline'] - median_baseline)

        # Normalize differences using min-max scaling
        min_date_diff = data['Date_Diff'].min()
        max_date_diff = data['Date_Diff'].max()
        min_baseline_diff = data['Baseline_Diff'].min()
        max_baseline_diff = data['Baseline_Diff'].max()
        
        data['Normalized_Date_Diff'] = (data['Date_Diff'] - min_date_diff) / (max_date_diff - min_date_diff)
        data['Normalized_Baseline_Diff'] = (data['Baseline_Diff'] - min_baseline_diff) / (max_baseline_diff - min_baseline_diff)

        # Sum up the normalized differences to find the closest entries
        data['Total_Diff'] = data['Normalized_Date_Diff'] + data['Normalized_Baseline_Diff']

        # Sort by the total difference and select the top 5
        selected_entries = data.sort_values(by='Total_Diff').head(5)

        options = selected_entries['ID'].tolist()

        print('The best options among the images for being selected as the master date:')
        # Printing the date of S1 images
        counter = 1
        for image_id in options:
            print(f'Option {counter} - ', image_id[3:11])
            counter += 1


    def get_master_from_user(self):

        print('Please insert the master image date (it could be either from the above recommondations or your preferred date- format: YYYYMMDD):')

        self.master_date = input()

        # Define the full path to the file
        file_path = os.path.join(self.path_work, "master_date.txt")
        
        # Write the variable value to the file
        with open(file_path, 'w') as file:
            file.write(self.master_date)

        for IW_number in self.list_of_IW_numbers:

            data_in_path = self.path_work + 'F' + str(IW_number) + '/' + 'raw/' + 'data.in'

            with open(data_in_path, 'r') as file:
                    lines = file.readlines()

            target_row = None
            other_rows = []

            for i in range(len(lines)):
                    if lines[i][15:23] == self.master_date:
                            target_row = lines[i]
                    else:
                        other_rows.append(lines[i])

            with open(data_in_path, 'w') as file:
                    file.write(target_row)  # Write the target row first
                    file.writelines(other_rows)  # Write all other rows