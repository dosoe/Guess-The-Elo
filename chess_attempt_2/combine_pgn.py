import os

def read_file_with_fallback(file_path):
    # Try reading the file with utf-8 encoding
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        print(f"Unicode error with {file_path}, trying with latin-1 encoding...")
        # If utf-8 fails, try latin-1 encoding
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()

def combine_pgn_files(source_folder, output_file):
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for filename in os.listdir(source_folder):
            if filename.endswith('.pgn'):
                file_path = os.path.join(source_folder, filename)
                print(f"Copying contents of {filename} into {output_file}...")

                # Read file with fallback mechanism for encoding issues
                file_content = read_file_with_fallback(file_path)
                outfile.write(file_content)
                
                # Ensure that there's a blank line between games
                outfile.write('\n\n')
    
    print(f"All PGN files copied into {output_file}")

# Example usage:
source_folder = 'utf8_games'  # Folder containing PGN files
output_file = 'combined_games.pgn'  # Output file for the combined PGN

combine_pgn_files(source_folder, output_file)
