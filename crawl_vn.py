import os
import PyPDF2
import re

# Define the folder containing PDF files
pdf_folder = './vn/'
output_folder = './output/'

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)


def extract_chapters_from_pdf(pdf_path):
    """Extract chapters from a PDF file."""
    chapters = []
    current_chapter = None
    current_content = []

    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_number, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    # Ensure proper handling of Vietnamese text
                    text = text.encode('utf-8').decode('utf-8')
                    lines = text.split('\n')
                    for line in lines:
                        if line.startswith('Chapter') or line.isupper():
                            if current_chapter:
                                chapters.append(
                                    (
                                        current_chapter,
                                        '\n'.join(current_content)
                                    )
                                )
                            current_chapter = line.strip()
                            current_content = [text]
                            break
                    else:
                        if current_chapter:
                            current_content.append(text)
            if current_chapter:
                chapters.append(
                    (
                        current_chapter,
                        '\n'.join(current_content)
                    )
                )
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

    return chapters


def save_chapters_to_txt(chapters, base_filename):
    """Save chapters to TXT files."""
    for chapter_title, content in chapters:
        chapter_title = chapter_title.replace(' ', '_')
        # Extract chapter title using regex
        match = re.search(r'(QUYỂN)(_.*)', chapter_title)
        if match:
            sanitized_title = match.group(2).replace('_', '')
        else:
            sanitized_title = chapter_title.replace(' ', '_').replace('/', '_')
        
        txt_filename = os.path.join(
            output_folder, f"{sanitized_title}.txt"
        )
        with open(txt_filename, 'w', encoding='utf-8') as txtfile:
            txtfile.write(content.encode('utf-8').decode('utf-8'))


# Process each PDF file in the folder
for pdf_file in os.listdir(pdf_folder)[:]: 
    if pdf_file.endswith('.pdf'):
        pdf_path = os.path.join(pdf_folder, pdf_file)
        chapters = extract_chapters_from_pdf(pdf_path)
        base_filename = os.path.splitext(pdf_file)[0]
        save_chapters_to_txt(chapters, base_filename)

print("Processing complete. Check the 'output' folder for results.")