import csv
import os
import re


def extract_data(input_path, output_path):
    """
    Extracts the number and the second column (German noun) from the input CSV.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    extracted_data = []

    with open(input_path, "r", encoding="utf-8") as f:
        # It seems the file is tab-separated based on previous analysis
        reader = csv.reader(f, delimiter="\t")

        for row in reader:
            if not row:
                continue

            # Row structure based on 'cat -A':
            # Col 0: "1. Time", Col 1: "Die Zeit", Col 2: "Die Zeiten"
            if len(row) >= 2:
                first_col = row[0].strip()
                second_col = row[1].strip()

                # Extract number from first column (e.g., "1. Time" -> "1")
                match = re.match(r"^(\d+)", first_col)
                if match:
                    number = match.group(1)
                    extracted_data.append([number, second_col])

    # Write to output CSV
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Number", "German Word"])  # Header
        writer.writerows(extracted_data)

    print(f"Extracted {len(extracted_data)} rows to {output_path}")


if __name__ == "__main__":
    input_file = "data/raw/DE/nouns/top2000.csv"
    output_file = "data/dicts/DE/nouns/top2000.csv"

    # Resolve paths relative to the project root if running from root
    # Or just use absolute paths if preferred, but relative is usually safer for portability within the project
    # Assuming script is run from project root
    if not os.path.exists(input_file):
        # Try to find it relative to the script location if run from scripts dir
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        input_file = os.path.join(project_root, "data", "raw", "DE", "nouns", "top2000.csv")
        output_file = os.path.join(project_root, "data", "dicts", "DE", "nouns", "top2000.csv")

    extract_data(input_file, output_file)
