import os
import re
import pandas as pd
import glob

# Define input and output directories
input_folder = './chinese/'
output_folder = './data_ingestion_chinese/'

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

def process_excel_file(file_path):
    """
    Process an Excel file, extract content column and save as a text file.
    """
    try:
        # Extract the number from the filename using regex
        match = re.search(r'卷(\d+)', os.path.basename(file_path))
        if not match:
            print(f"No volume number found in {file_path}, skipping.")
            return
        
        volume_number = match.group(1)
        output_filename = f"{volume_number}.txt"
        output_path = os.path.join(output_folder, output_filename)
        
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # Find the content column - assuming it might have different names
        content_col = None
        for col in df.columns:
            if 'content' in col.lower() or '内容' in col:
                content_col = col
                break
        
        if not content_col:
            print(f"No content column found in {file_path}, skipping.")
            return
        
        # Concatenate all text from the content column
        content_text = '\n'.join(df[content_col].dropna().astype(str))
        
        # Save to text file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content_text)
        
        print(f"Processed {file_path} -> {output_path}")
    
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")

def main():
    # Find all Excel files with pattern 卷\d+ (volume number)
    excel_files = glob.glob(os.path.join(input_folder, '*卷*'))
    
    print(f"Found {len(excel_files)} files matching the pattern.")
    
    # Process each file
    for file_path in sorted(excel_files):
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            process_excel_file(file_path)

if __name__ == "__main__":
    main()