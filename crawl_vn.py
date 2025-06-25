import os
import PyPDF2
import csv
import re

# Define the folder containing PDF files
pdf_folder = './vn/'
output_folder = './output/'

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)


def extract_chapters_from_pdf(pdf_path):
    """Extract chapters from a PDF file."""
    chapters = []
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            # Add debugging to inspect extracted text
            for page_number, page in enumerate(reader.pages):
                text = page.extract_text()
                # Update logic to identify chapters based on patterns
                if text.strip():  # Check if the page has content
                    lines = text.split('\n')
                    for line in lines:
                        if line.startswith('Chapter') or line.isupper():
                            chapter_title = line.strip()
                            chapters.append((chapter_title, text))
                            break
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return chapters


def save_chapters_to_csv(chapters, base_filename):
    """Save chapters to CSV files."""
    for chapter_title, content in chapters:
        # Extract chapter title using regex
        match = re.search(r'(QUYỂN)(_.*)', chapter_title)
        if match:
            sanitized_title = match.group(1).replace(' ', '_')
            sanitized_title = sanitized_title.replace('/', '_')
        else:
            sanitized_title = chapter_title.replace(' ', '_').replace('/', '_')
        
        csv_filename = os.path.join(
            output_folder, f"{base_filename}_{sanitized_title}.csv"
        )
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Title', 'Content'])
            writer.writerow([chapter_title, content])


# Process each PDF file in the folder
for pdf_file in os.listdir(pdf_folder)[3:]:  # Skip the first three files
    if pdf_file.endswith('.pdf'):
        pdf_path = os.path.join(pdf_folder, pdf_file)
        chapters = extract_chapters_from_pdf(pdf_path)
        # print(chapters)
        base_filename = os.path.splitext(pdf_file)[0]
        save_chapters_to_csv(chapters, base_filename)

print("Processing complete. Check the 'output' folder for results.")