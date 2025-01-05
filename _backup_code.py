import os
import shutil
from tqdm import tqdm
import subprocess

# Hardcoded paths
SOURCE_DIR = "C:/ParseThat/QuizMasterPro"
DEST_BASE = "C:/ParseThat/QuizMasterPro_backups"

# Ensure source directory exists
if not os.path.isdir(SOURCE_DIR):
    print(f"Source directory does not exist: {SOURCE_DIR}")
    exit(1)

# Determine the destination directory with incremented number suffix
counter = 1
while os.path.exists(f"{DEST_BASE}_{counter:02}"):
    counter += 1

DEST_DIR = f"{DEST_BASE}_{counter:02}"

# Create the destination directory
os.makedirs(DEST_DIR)

# Get the list of files to copy using git
try:
    result = subprocess.run(
        ["git", "-C", SOURCE_DIR, "ls-files"],
        capture_output=True, text=True, check=True
    )
    files_to_copy = result.stdout.splitlines()
except subprocess.CalledProcessError as e:
    print(f"Error running git command: {e}")
    exit(1)

# Copy files with a progress bar
with tqdm(total=len(files_to_copy), desc="Copying Files", unit="file") as pbar:
    for rel_path in files_to_copy:
        src_file = os.path.join(SOURCE_DIR, rel_path)
        dest_file = os.path.join(DEST_DIR, rel_path)
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        shutil.copy2(src_file, dest_file)
        pbar.update(1)

print(f"Files copied to: {DEST_DIR}")
