# backup_script.py
import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import shutil

def run_backup():
    """
    Executes a backup of the MongoDB database using the mongodump utility.
    """
    print("Starting database backup...")

    # --- 1. Check for mongodump command ---
    if not shutil.which("mongodump"):
        print("\nERROR: 'mongodump' command not found.")
        print("Please ensure you have MongoDB Database Tools installed and that")
        print("'mongodump' is available in your system's PATH.")
        print("Installation guide: https://www.mongodb.com/docs/database-tools/installation/installation/")
        return

    # --- 2. Load Environment Variables ---
    load_dotenv()
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("ERROR: MONGO_URI not found in .env file. Aborting.")
        return

    # --- 3. Prepare Backup Directory ---
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    backup_dir = os.path.join('backups', f'backup_{timestamp}')
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        print(f"Backup will be saved to: '{backup_dir}'")
    except OSError as e:
        print(f"ERROR: Could not create backup directory. {e}")
        return

    # --- 4. Construct and Run mongodump Command ---
    # The command will be: mongodump --uri="your_mongo_uri" --out="backups/backup_YYYY-MM-DD_HHMMSS"
    command = [
        'mongodump',
        f'--uri={mongo_uri}',
        f'--out={backup_dir}'
    ]

    print("\nExecuting mongodump...")
    try:
        # Using subprocess.run to execute the command
        result = subprocess.run(
            command,
            capture_output=True,  # Capture stdout and stderr
            text=True,            # Decode output as text
            check=True            # Raise an exception for non-zero exit codes
        )
        
        # Print the output from mongodump
        print("\n--- mongodump output ---")
        print(result.stdout)
        if result.stderr:
            print("\n--- mongodump errors/warnings ---")
            print(result.stderr)
        
        print("\n✅ Backup completed successfully!")

    except FileNotFoundError:
        # This is another way to catch if mongodump is not installed
        print("\nERROR: 'mongodump' command not found. Please check your installation.")
    except subprocess.CalledProcessError as e:
        # This catches errors from mongodump itself (e.g., bad URI)
        print("\n❌ ERROR: mongodump failed with an error.")
        print("\n--- mongodump output (stdout) ---")
        print(e.stdout)
        print("\n--- mongodump error output (stderr) ---")
        print(e.stderr)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    run_backup()
