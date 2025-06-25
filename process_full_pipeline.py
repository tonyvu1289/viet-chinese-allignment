import os
import sys
import glob
import yaml
import re
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring
import math

# Add Bertalign package to the Python path
sys.path.append('./bertalign-code/modified_bertalign')
from bertalign import Bertalign

# Define input and output directories
chinese_folder = './data_ingestion_chinese/'
vietnamese_folder = './data_ingestion_vn/'
aligned_folder = './aligned_output/'
xml_folder = './xml_output/'
metadata_file = './meta_data.yaml'

# Ensure the output folders exist
os.makedirs(aligned_folder, exist_ok=True)
os.makedirs(xml_folder, exist_ok=True)

def read_metadata():
    """Read metadata from YAML file."""
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = yaml.safe_load(f)
    
    # Fix common typos in metadata
    if 'TIITLE' in metadata and 'TITLE' not in metadata:
        metadata['TITLE'] = metadata.pop('TIITLE')
    
    if 'PEROID' in metadata and 'PERIOD' not in metadata:
        metadata['PERIOD'] = metadata.pop('PEROID')
    
    return metadata

def clean_text(text):
    """Clean and normalize text by removing extra whitespace."""
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def align_files(chinese_file, vietnamese_file, output_file):
    """
    Align sentences from Chinese and Vietnamese files using Bertalign
    and save the results to an output file with one Chinese sentence per row.
    """
    try:
        # Read source and target texts
        with open(chinese_file, 'r', encoding='utf-8') as f_src:
            src = f_src.read()
        
        with open(vietnamese_file, 'r', encoding='utf-8') as f_tgt:
            tgt = f_tgt.read()
        
        # Create Bertalign object and align sentences
        print(f"Aligning {os.path.basename(chinese_file)} with {os.path.basename(vietnamese_file)}...")
        aligner = Bertalign(src, tgt)
        alignments = aligner.align_sents()
        
        # Save aligned sentences to output file
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for bead in alignments:
                src_line = get_line(bead[0], aligner.src_sents)
                tgt_line = get_line(bead[1], aligner.tgt_sents)
                
                if src_line and tgt_line:
                    # Clean up any newlines within the aligned text to ensure one pair per line
                    src_line = src_line.replace('\n', ' ').strip()
                    tgt_line = tgt_line.replace('\n', ' ').strip()
                    f_out.write(f"{src_line}\t{tgt_line}\n")
        
        print(f"Alignment saved to {output_file}")
        return True
    
    except Exception as e:
        print(f"Error aligning {chinese_file} and {vietnamese_file}: {e}")
        return False

def get_line(bead, lines):
    """
    Get a line of text from the given bead and lines.
    This is similar to Bertalign._get_line method.
    """
    line = ''
    if len(bead) > 0:
        line = ' '.join(lines[bead[0]:bead[-1]+1])
    return line

def create_xml_structure(file_number, aligned_data, metadata):
    """Create XML structure for the aligned data with proper IDs."""
    # Create root element
    root = Element('root')
    
    # Create FILE element with the ID from metadata
    file_id = metadata.get('ID', 'HCS_001')
    file_elem = SubElement(root, 'FILE', {'ID': file_id})
    
    # Create meta element
    meta_elem = SubElement(file_elem, 'meta')
    
    # Add metadata elements
    SubElement(meta_elem, 'TITLE').text = metadata.get('TITLE', '')
    SubElement(meta_elem, 'VOLUME').text = metadata.get('VOLUME', '')
    SubElement(meta_elem, 'AUTHOR').text = metadata.get('AUTHOR', '')
    SubElement(meta_elem, 'PERIOD').text = metadata.get('PERIOD', '')
    SubElement(meta_elem, 'LANGUAGE').text = 'Hán-Việt'
    SubElement(meta_elem, 'TRANSLATOR').text = metadata.get('TRANSLATOR', '')
    SubElement(meta_elem, 'SOURCE').text = metadata.get('SOURCE', '')
    
    # Create SECT element with proper ID format (HCS_001.075)
    sect_id = f"{file_id}.{file_number:03d}"
    sect_elem = SubElement(file_elem, 'SECT', {
        'ID': sect_id,
        'NAME': metadata.get('TITLE', '')
    })
    
    # For larger datasets, split into multiple pages with up to 50 entries per page
    max_items_per_page = 50
    num_pages = math.ceil(len(aligned_data) / max_items_per_page)
    
    for page_idx in range(num_pages):
        page_id = f"{sect_id}.{page_idx+1:03d}"
        page_elem = SubElement(sect_elem, 'PAGE', {'ID': page_id})
        
        # Get data for this page
        start_idx = page_idx * max_items_per_page
        end_idx = min((page_idx + 1) * max_items_per_page, len(aligned_data))
        page_data = aligned_data[start_idx:end_idx]
        
        # Add each aligned sentence pair as an STC element
        for idx, (chinese, vietnamese) in enumerate(page_data, 1):
            stc_id = f"{page_id}.{idx:03d}"
            stc_elem = SubElement(page_elem, 'STC', {'ID': stc_id})
            
            c_elem = SubElement(stc_elem, 'C')
            c_elem.text = clean_text(chinese)
            
            v_elem = SubElement(stc_elem, 'V')
            v_elem.text = clean_text(vietnamese)
    
    return root

def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t", encoding='utf-8').decode('utf-8')

def convert_aligned_to_xml(aligned_file, metadata):
    """Convert an aligned text file to XML format."""
    # Extract file number from the filename
    match = re.search(r'aligned_(\d+).txt', os.path.basename(aligned_file))
    if not match:
        print(f"Could not extract file number from {aligned_file}, skipping.")
        return
    
    file_number = int(match.group(1))
    
    # Read aligned data
    aligned_data = []
    with open(aligned_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split('\t')
                if len(parts) == 2:
                    chinese, vietnamese = parts
                    # Clean up any newlines in the text
                    chinese = chinese.replace('\n', ' ').strip()
                    vietnamese = vietnamese.replace('\n', ' ').strip()
                    aligned_data.append((chinese, vietnamese))
    
    if not aligned_data:
        print(f"No aligned data found in {aligned_file}, skipping.")
        return
    
    # Create XML structure
    root = create_xml_structure(file_number, aligned_data, metadata)
    
    # Generate pretty XML
    xml_string = prettify_xml(root)
    
    # Save to file - remove the duplicate XML declaration
    base_id = metadata.get('ID', 'HCS_001')
    output_file = os.path.join(xml_folder, f'{base_id}_{file_number:03d}.xml')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        # Skip the first line of the prettified XML which is another XML declaration
        f.write(xml_string.split('\n', 1)[1])
    
    print(f"Created XML file: {output_file}")

def main():
    """Main function to process files from start to finish."""
    # Parse command line arguments
    test_mode = False
    file_numbers = []
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            test_mode = True
            # Use the file numbers provided as arguments
            if len(sys.argv) > 2:
                file_numbers = sys.argv[2:]
            else:
                # Default to a few sample files if no specific files are provided
                file_numbers = ['75', '130']
    
    # Get metadata
    metadata = read_metadata()
    
    # Step 1: Determine which files to process
    if test_mode:
        chinese_files = []
        for num in file_numbers:
            file_path = os.path.join(chinese_folder, f"{num}.txt")
            if os.path.exists(file_path):
                chinese_files.append(file_path)
            else:
                print(f"Warning: Chinese file {num}.txt not found")
    else:
        chinese_files = glob.glob(os.path.join(chinese_folder, '*.txt'))
    
    print(f"Processing {len(chinese_files)} files...")
    
    # Step 2: Process each pair of files
    aligned_files = []
    for chinese_file in sorted(chinese_files):
        # Extract the number from the filename
        file_number = os.path.splitext(os.path.basename(chinese_file))[0]
        
        # Find the corresponding Vietnamese file
        vietnamese_file = os.path.join(vietnamese_folder, f"{file_number}.txt")
        
        if os.path.exists(vietnamese_file):
            # Create output file path for aligned text
            aligned_file = os.path.join(aligned_folder, f"aligned_{file_number}.txt")
            
            # Step 2a: Align the files
            if align_files(chinese_file, vietnamese_file, aligned_file):
                aligned_files.append(aligned_file)
        else:
            print(f"No matching Vietnamese file found for {chinese_file}")
    
    print(f"Successfully aligned {len(aligned_files)} file pairs.")
    
    # Step 3: Convert aligned files to XML
    for aligned_file in sorted(aligned_files):
        convert_aligned_to_xml(aligned_file, metadata)
    
    print(f"All files processed. Output XML files saved to {xml_folder}")

if __name__ == "__main__":
    main()