import os
import glob
import subprocess

# Define the path to the 'ready' directory
ready_dir = './'

# List all .py files in the 'ready' directory, excluding 'hypercandles.py'
py_files = [f for f in glob.glob(os.path.join(ready_dir, '*.py')) if 'hypercandles.py' not in f]

# Iterate over the Python files and run them one by one
for file_path in py_files:
    try:
        # Skip the 'hypercandles.py' file
        if 'hypercandles.py' in file_path:
            continue
        if 'optimize.py' in file_path:
            continue
        if 'aave.py' in file_path:
            continue
        if 'alt.py' in file_path:
            continue
        if 'arb.py' in file_path:
            continue
        if 'btc.py' in file_path:
            continue
        if 'eth.py' in file_path:
            continue
        
        # Run the Python script using subprocess.run
        print(f"Running script: {file_path}")
        result = subprocess.run(['python', file_path], capture_output=True, text=True, check=True)

        # Print the output and error (if any)
        print(result.stdout)
        if result.stderr:
            print("Error:", result.stderr)
    except subprocess.CalledProcessError as e:
        # Log the error if the script failed to run
        print(f"An error occurred while running the script {file_path}: {e}")