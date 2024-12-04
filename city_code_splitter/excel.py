import os
import re
import pandas as pd

from constants import FILENAME_SPLITTER, OUTPUT_FOLDER

city_code_pattern = re.compile(r'^[A-Z]{3}$')


def count_city_codes(series):
    return series.apply(lambda x: bool(city_code_pattern.match(str(x)))).sum()


def split_by_city_code(source_file_path):
    source_file_name = os.path.basename(source_file_path).split('.')[0].split(FILENAME_SPLITTER)[1]
    # Read the Excel file
    df = pd.read_excel(source_file_path)

    # Extract the title (column names)
    title = df.columns

    # Create a dictionary to hold city-specific rows
    city_to_rows = {}

    code_counts = df.apply(count_city_codes)
    most_likely_column = code_counts.idxmax()

    # Iterate over the rows in the DataFrame
    for _, row in df.iterrows():
        city = row[most_likely_column]
        if pd.notnull(city) and city_code_pattern.match(city):
            if city not in city_to_rows:
                city_to_rows[city] = []
            city_to_rows[city].append(row)

    # Write city-specific data to separate Excel files

    file_paths = []
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    os.makedirs(f"{OUTPUT_FOLDER}/{source_file_name}", exist_ok=True)
    for city, rows in city_to_rows.items():
        city_df = pd.DataFrame(rows, columns=title)
        file_path = f"{OUTPUT_FOLDER}/{source_file_name}/{source_file_name} {city}.xlsx"
        city_df.to_excel(file_path, index=False)
        file_paths.append(file_path)

    return file_paths


# def main():
#     # Find all xlsm files in the current directory
#     xlsm_files = glob.glob("./*.xlsx")
#
#     # Process each file
#     for file_path in xlsm_files:
#         split_by_city_code(file_path)


# if __name__ == '__main__':
#     main()
