#!/bin/bash
# Set working dir
cd /root

# Configure and install cuda-toolkit
#dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
#dnf clean all
#dnf -y install cuda-toolkit-12-8

# Export CUDA library paths
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:
export LIBRARY_PATH=/usr/local/cuda/lib64:

# Git clone perftest repository
git clone https://github.com/linux-rdma/perftest.git

# Change into perftest directory
cd /root/perftest

# Build perftest with the cuda libraries included
./autogen.sh
./configure CUDA_H_PATH=/usr/local/cuda/include/cuda.h
make -j
make install

# Sleep container indefinitly
# sleep infinity & wait
