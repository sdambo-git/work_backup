#ARG IMAGE_NAME
#FROM ${IMAGE_NAME}:12.8.0-base-ubi9 as base
FROM registry.access.redhat.com/ubi9/ubi:latest as base

ENV NV_CUDA_LIB_VERSION 12.8.0-1

FROM base as base-amd64

ENV NV_NVTX_VERSION 12.8.55-1
ENV NV_LIBNPP_VERSION 12.3.3.65-1
ENV NV_LIBNPP_PACKAGE libnpp-12-8-${NV_LIBNPP_VERSION}
ENV NV_LIBCUBLAS_VERSION 12.8.3.14-1
ENV NV_LIBNCCL_PACKAGE_NAME libnccl
ENV NV_LIBNCCL_PACKAGE_VERSION 2.25.1-1
ENV NV_LIBNCCL_VERSION 2.25.1
ENV NCCL_VERSION 2.25.1
ENV NV_LIBNCCL_PACKAGE ${NV_LIBNCCL_PACKAGE_NAME}-${NV_LIBNCCL_PACKAGE_VERSION}+cuda12.8
ENV NVARCH x86_64
ENV NVIDIA_REQUIRE_CUDA "cuda>=12.8 brand=unknown,driver>=470,driver<471 brand=grid,driver>=470,driver<471 brand=tesla,driver>=470,driver<471 brand=nvidia,driver>=470,driver<471 brand=quadro,driver>=470,driver<471 brand=quadrortx,driver>=470,driver<471 brand=nvidiartx,driver>=470,driver<471 brand=vapps,driver>=470,driver<471 brand=vpc,driver>=470,driver<471 brand=vcs,driver>=470,driver<471 brand=vws,driver>=470,driver<471 brand=cloudgaming,driver>=470,driver<471 brand=unknown,driver>=535,driver<536 brand=grid,driver>=535,driver<536 brand=tesla,driver>=535,driver<536 brand=nvidia,driver>=535,driver<536 brand=quadro,driver>=535,driver<536 brand=quadrortx,driver>=535,driver<536 brand=nvidiartx,driver>=535,driver<536 brand=vapps,driver>=535,driver<536 brand=vpc,driver>=535,driver<536 brand=vcs,driver>=535,driver<536 brand=vws,driver>=535,driver<536 brand=cloudgaming,driver>=535,driver<536 brand=unknown,driver>=550,driver<551 brand=grid,driver>=550,driver<551 brand=tesla,driver>=550,driver<551 brand=nvidia,driver>=550,driver<551 brand=quadro,driver>=550,driver<551 brand=quadrortx,driver>=550,driver<551 brand=nvidiartx,driver>=550,driver<551 brand=vapps,driver>=550,driver<551 brand=vpc,driver>=550,driver<551 brand=vcs,driver>=550,driver<551 brand=vws,driver>=550,driver<551 brand=cloudgaming,driver>=550,driver<551 brand=unknown,driver>=560,driver<561 brand=grid,driver>=560,driver<561 brand=tesla,driver>=560,driver<561 brand=nvidia,driver>=560,driver<561 brand=quadro,driver>=560,driver<561 brand=quadrortx,driver>=560,driver<561 brand=nvidiartx,driver>=560,driver<561 brand=vapps,driver>=560,driver<561 brand=vpc,driver>=560,driver<561 brand=vcs,driver>=560,driver<561 brand=vws,driver>=560,driver<561 brand=cloudgaming,driver>=560,driver<561 brand=unknown,driver>=565,driver<566 brand=grid,driver>=565,driver<566 brand=tesla,driver>=565,driver<566 brand=nvidia,driver>=565,driver<566 brand=quadro,driver>=565,driver<566 brand=quadrortx,driver>=565,driver<566 brand=nvidiartx,driver>=565,driver<566 brand=vapps,driver>=565,driver<566 brand=vpc,driver>=565,driver<566 brand=vcs,driver>=565,driver<566 brand=vws,driver>=565,driver<566 brand=cloudgaming,driver>=565,driver<566"
ENV NV_CUDA_CUDART_VERSION 12.8.57-1
ENV NV_CUDNN_VERSION 9.7.0.66-1
ENV NV_CUDNN_PACKAGE libcudnn9-cuda-12-${NV_CUDNN_VERSION}


COPY cuda.repo-x86_64 /etc/yum.repos.d/cuda.repo

FROM base as base-arm64

ENV NVARCH sbsa
ENV NVIDIA_REQUIRE_CUDA "cuda>=12.8 brand=unknown,driver>=470,driver<471 brand=grid,driver>=470,driver<471 brand=tesla,driver>=470,driver<471 brand=nvidia,driver>=470,driver<471 brand=quadro,driver>=470,driver<471 brand=quadrortx,driver>=470,driver<471 brand=nvidiartx,driver>=470,driver<471 brand=vapps,driver>=470,driver<471 brand=vpc,driver>=470,driver<471 brand=vcs,driver>=470,driver<471 brand=vws,driver>=470,driver<471 brand=cloudgaming,driver>=470,driver<471 brand=unknown,driver>=535,driver<536 brand=grid,driver>=535,driver<536 brand=tesla,driver>=535,driver<536 brand=nvidia,driver>=535,driver<536 brand=quadro,driver>=535,driver<536 brand=quadrortx,driver>=535,driver<536 brand=nvidiartx,driver>=535,driver<536 brand=vapps,driver>=535,driver<536 brand=vpc,driver>=535,driver<536 brand=vcs,driver>=535,driver<536 brand=vws,driver>=535,driver<536 brand=cloudgaming,driver>=535,driver<536 brand=unknown,driver>=550,driver<551 brand=grid,driver>=550,driver<551 brand=tesla,driver>=550,driver<551 brand=nvidia,driver>=550,driver<551 brand=quadro,driver>=550,driver<551 brand=quadrortx,driver>=550,driver<551 brand=nvidiartx,driver>=550,driver<551 brand=vapps,driver>=550,driver<551 brand=vpc,driver>=550,driver<551 brand=vcs,driver>=550,driver<551 brand=vws,driver>=550,driver<551 brand=cloudgaming,driver>=550,driver<551 brand=unknown,driver>=560,driver<561 brand=grid,driver>=560,driver<561 brand=tesla,driver>=560,driver<561 brand=nvidia,driver>=560,driver<561 brand=quadro,driver>=560,driver<561 brand=quadrortx,driver>=560,driver<561 brand=nvidiartx,driver>=560,driver<561 brand=vapps,driver>=560,driver<561 brand=vpc,driver>=560,driver<561 brand=vcs,driver>=560,driver<561 brand=vws,driver>=560,driver<561 brand=cloudgaming,driver>=560,driver<561 brand=unknown,driver>=565,driver<566 brand=grid,driver>=565,driver<566 brand=tesla,driver>=565,driver<566 brand=nvidia,driver>=565,driver<566 brand=quadro,driver>=565,driver<566 brand=quadrortx,driver>=565,driver<566 brand=nvidiartx,driver>=565,driver<566 brand=vapps,driver>=565,driver<566 brand=vpc,driver>=565,driver<566 brand=vcs,driver>=565,driver<566 brand=vws,driver>=565,driver<566 brand=cloudgaming,driver>=565,driver<566"
ENV NV_CUDA_CUDART_VERSION 12.8.57-1
ENV NV_NVTX_VERSION 12.8.55-1
ENV NV_LIBNPP_VERSION 12.3.3.65-1
ENV NV_LIBNPP_PACKAGE libnpp-12-8-${NV_LIBNPP_VERSION}
ENV NV_LIBCUBLAS_VERSION 12.8.3.14-1
ENV NV_LIBNCCL_PACKAGE_NAME libnccl
ENV NV_LIBNCCL_PACKAGE_VERSION 2.25.1-1
ENV NV_LIBNCCL_VERSION 2.25.1
ENV NCCL_VERSION 2.25.1
ENV NV_LIBNCCL_PACKAGE ${NV_LIBNCCL_PACKAGE_NAME}-${NV_LIBNCCL_PACKAGE_VERSION}+cuda12.8
ENV NV_CUDNN_VERSION 9.7.0.66-1
ENV NV_CUDNN_PACKAGE libcudnn9-cuda-12-${NV_CUDNN_VERSION}


COPY cuda.repo-arm64 /etc/yum.repos.d/cuda.repo

FROM base-${TARGETARCH}

ARG TARGETARCH

LABEL maintainer "NVIDIA CORPORATION <sw-cuda-installer@nvidia.com>"

RUN NVIDIA_GPGKEY_SUM=d0664fbbdb8c32356d45de36c5984617217b2d0bef41b93ccecd326ba3b80c87 && \
    curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/rhel9/${NVARCH}/D42D0685.pub | sed '/^Version/d' > /etc/pki/rpm-gpg/RPM-GPG-KEY-NVIDIA && \
    echo "$NVIDIA_GPGKEY_SUM  /etc/pki/rpm-gpg/RPM-GPG-KEY-NVIDIA" | sha256sum -c --strict -

RUN yum install -y \
    cuda-libraries-12-8-${NV_CUDA_LIB_VERSION} \
    cuda-nvtx-12-8-${NV_NVTX_VERSION} \
    ${NV_LIBNPP_PACKAGE} \
    libcublas-12-8-${NV_LIBCUBLAS_VERSION} \
    ${NV_LIBNCCL_PACKAGE} \
    && yum clean all \
    && rm -rf /var/cache/yum/*


# For libraries in the cuda-compat-* package: https://docs.nvidia.com/cuda/eula/index.html#attachment-a
#RUN yum install -y \
#    cuda-cudart-12-8-${NV_CUDA_CUDART_VERSION} \
#    cuda-compat-12-8 \
#    && yum clean all \
#    && rm -rf /var/cache/yum/*


#Add entrypoint items
COPY entrypoint.d/ /opt/nvidia/entrypoint.d/
COPY nvidia_entrypoint.sh /opt/nvidia/
ENV NVIDIA_PRODUCT_NAME="CUDA"
ENTRYPOINT ["/opt/nvidia/nvidia_entrypoint.sh"]

# Upgrade python to version 3.12 & install pip
RUN dnf install -y python3.12  \
    && dnf install -y python3-pip \
    && ln -s /usr/bin/python3.12 /usr/bin/python \
    # && ln -s /usr/bin/pip3.12 /usr/bin/pip \
    && pip install --upgrade pip \
    && dnf clean all 

#Install cuDNN    
RUN dnf install -y \
    ${NV_CUDNN_PACKAGE} \
    && dnf clean all \

#Verify installation
RUN python3 --version && pip --version

# Install python modules
RUN python3 -m pip install wheel pandas torch torchvision requests opencv-python torchaudio  
#numpy scipy matplotlib keras tensorflow-gpu Cython jupyter opencv-contrib-python mlflow seaborn plotly xgboost networkx pyspark tqdm pandarallel sqlalchemy dpkt hkdf pycrypto scapy selenium vertica_python sqlalchemy-vertica   

# Install OpenSSH server
RUN dnf install -y openssh-server openssh-clients passwd wget procps \
    && dnf clean all

# Create SSH directory and set permissions
RUN mkdir -p /run/sshd && chmod 0755 /run/sshd && ssh-keygen -A

# Create a user with password "password" (change as needed)
RUN useradd -m -s /bin/bash sdambo && echo "sdambo:password" | chpasswd && echo "root:password" | chpasswd

# Start SSH service
CMD ["/usr/sbin/sshd", "-D"]

#Modify LD_LIBRARY_PATH
ENV LD_LIBRARY_PATH=/usr/local/cuda-12.8/lib64:/usr/local/lib64/python3.9/site-packages/triton/backends/nvidia/lib/cupti:/usr/local/lib/python3.9/site-packages/cusparselt/lib
