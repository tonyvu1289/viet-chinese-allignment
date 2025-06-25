import os
import yaml
import re
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring
import glob
import math

# Define input and output directories
aligned_folder = './aligned_output/'
output_folder = './xml_output/'
metadata_file = './meta_data.yaml'

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

def read_metadata():
    """Read metadata from YAML file."""
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = yaml.safe_load(f)
    
    # Fix the typo in TIITLE -> TITLE if needed
    if 'TIITLE' in metadata and 'TITLE' not in metadata:
        metadata['TITLE'] = metadata.pop('TIITLE')
    
    # Fix the typo in PEROID -> PERIOD if needed
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

def create_xml_structure(file_number, aligned_data, metadata, main_section=4):
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

def process_aligned_file(aligned_file, metadata):
    """Process a single aligned file and create XML output."""
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
    output_file = os.path.join(output_folder, f'{base_id}_{file_number:03d}.xml')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        # Skip the first line of the prettified XML which is another XML declaration
        f.write(xml_string.split('\n', 1)[1])
    
    print(f"Created XML file: {output_file}")

def main():
    # Read metadata
    metadata = read_metadata()
    
    # Find all aligned files
    aligned_files = glob.glob(os.path.join(aligned_folder, 'aligned_*.txt'))
    
    print(f"Found {len(aligned_files)} aligned files.")
    
    # Process each aligned file
    for aligned_file in sorted(aligned_files):
        process_aligned_file(aligned_file, metadata)
    
    print(f"All aligned files processed. Output XML files saved to {output_folder}")

if __name__ == "__main__":
    main()