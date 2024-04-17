import os

# Get the current working directory
current_working_directory = os.getcwd()

# Define your custom path
custom_path = "OneDrive/desktop/optimize/optimization/ready"

# Join the current working directory with the custom path
full_path = os.path.join(current_working_directory, custom_path)

print("The full path is:", full_path)
