import os

# Get the total number of CPU cores
total_cores = os.cpu_count()

# Calculate half of the total cores (rounded down if necessary)
half_cores = total_cores // 2  # Use integer division to get a whole number

print(f"Total cores available: {total_cores}")
print(f"Using half of the cores: {half_cores}")