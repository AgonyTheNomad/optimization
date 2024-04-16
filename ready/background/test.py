import os
import psutil

# Get the number of logical CPUs available to the OS (includes hyper-threaded cores)
logical_cores = psutil.cpu_count()
# Get the number of physical cores only
physical_cores = psutil.cpu_count(logical=False)

# Total memory
memory_info = psutil.virtual_memory()
total_memory_gb = memory_info.total / (1024**3)  # Convert from bytes to GB

print(f"Logical CPU cores: {logical_cores}")
print(f"Physical CPU cores: {physical_cores}")
print(f"Total Memory: {total_memory_gb:.2f} GB")
