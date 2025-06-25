import os
import glob
import sys


from bertalign import Bertalign

# Define input and output directories
chinese_folder = './data_ingestion_chinese/'
vietnamese_folder = './data_ingestion_vn/'
output_folder = './aligned_output/'

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

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

def main():
    # Get command line arguments for testing a small set
    test_mode = False
    file_numbers = []
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            test_mode = True
            # Use the file numbers provided as arguments
            if len(sys.argv) > 2:
                file_numbers = sys.argv[2:]
            else:
                # Default to first few files if no specific files are provided
                file_numbers = ['1', '10', '75']
    
    # Get all text files in the Chinese folder
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
    
    for chinese_file in sorted(chinese_files):
        # Extract the number from the filename (assuming it's the basename)
        file_number = os.path.splitext(os.path.basename(chinese_file))[0]
        
        # Find the corresponding Vietnamese file
        vietnamese_file = os.path.join(vietnamese_folder, f"{file_number}.txt")
        
        if os.path.exists(vietnamese_file):
            # Create output file path
            output_file = os.path.join(output_folder, f"aligned_{file_number}.txt")
            
            # Align the files
            align_files(chinese_file, vietnamese_file, output_file)
        else:
            print(f"No matching Vietnamese file found for {chinese_file}")

if __name__ == "__main__":
    main()