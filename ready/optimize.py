import os
import glob
import subprocess

# Define the path to the 'ready' directory
ready_dir = './'

# List all .py files in the 'ready' directory, excluding 'hypercandles.py'
py_files = [f for f in glob.glob(os.path.join(ready_dir, '*.py')) if 'hypercandles.py' not in f and 'optimize.py' not in f]

# Iterate over the Python files and run them one by one
for file_path in py_files:
    try:
        print(f"Running script: {file_path}")
        result = subprocess.run(['python', file_path], capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("Error:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the script {file_path}: {e}")
        print("Output:", e.stdout)  # Print the standard output of the failed command
        print("Error Output:", e.stderr)  