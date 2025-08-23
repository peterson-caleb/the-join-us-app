# export_source.py
import os
from datetime import datetime

def export_project_source():
    """
    Walks through the project directory, finds all relevant source code files,
    and consolidates them into a single text file in an 'exports' directory.
    """
    # --- Configuration ---
    # Define which file extensions or names to include in the export.
    INCLUDE_EXTENSIONS = (
        '.py', '.html', '.css', '.js', '.md', '.txt', '.gitignore',
        '.yml', '.yaml', '.json'
    )
    # Add any full filenames that should always be included.
    INCLUDE_FILENAMES = ('Dockerfile',)

    # Define which directories to completely ignore.
    EXCLUDE_DIRS = (
        '.git', 'exports', '.venv', 'venv', 'env', '__pycache__'
    )
    
    # --- Setup ---
    # Create the output directory if it doesn't exist.
    output_dir = 'exports'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: '{output_dir}'")

    # Generate the dated and timed output filename.
    timestamp_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_filename = os.path.join(output_dir, f'{timestamp_str}_all_source_code.txt')
    
    print(f"Starting export... Output will be saved to: {output_filename}")
    
    # --- Main Logic ---
    try:
        with open(output_filename, 'w', encoding='utf-8') as outfile:
            # Get the current date and time for the header.
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Write the timestamp as the first line of the file.
            outfile.write(f'Project Source Code Exported on: {timestamp}\n')
            outfile.write('=' * 50 + '\n\n')

            # Walk through the current directory.
            for root, dirs, files in os.walk('.'):
                # First, modify the list of directories to exclude specific ones.
                # This prevents os.walk from even entering them.
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

                for filename in files:
                    # Check if the file should be included.
                    should_include = (
                        filename.endswith(INCLUDE_EXTENSIONS) or
                        filename in INCLUDE_FILENAMES
                    )
                    
                    if should_include:
                        file_path = os.path.join(root, filename)
                        
                        # Write the file header.
                        outfile.write('---\n')
                        outfile.write(f'FILE: {file_path}\n')
                        outfile.write('---\n')
                        
                        try:
                            # Write the file content.
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                                outfile.write(infile.read())
                                outfile.write('\n\n') # Add space between files.
                        except Exception as e:
                            outfile.write(f"Error reading file: {e}\n\n")

        print("\nExport completed successfully!")

    except IOError as e:
        print(f"\nError writing to output file: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    export_project_source()