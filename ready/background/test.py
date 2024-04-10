import torch

# Check if CUDA (GPU support) is available
print("CUDA Available:", torch.cuda.is_available())

# Get the name of the CUDA device
cuda = torch.device('cuda')
print("CUDA Device Name:", torch.cuda.get_device_name(cuda))
