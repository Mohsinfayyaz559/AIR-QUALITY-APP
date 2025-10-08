import pandas as pd
import os
import glob

# Path to the folder with CSVs
folder_path = ''

# Find all CSV files in the folder
csv_files = glob.glob(os.path.join(folder_path, '*.csv'))

# Read and concatenate them into a single DataFrame
combined_df = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)

# Save the result to a new CSV file (optional)
combined_df.to_csv('historical_air_pollution_2022-01-01_to_2025-3-01_rawalpindi.csv', index=False)
