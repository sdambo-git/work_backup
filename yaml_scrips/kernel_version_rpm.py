import platform
import subprocess
import os

# Fixed folder location inside the container where the RPM packages are stored.
FIXED_RPM_FOLDER = "/root/mft/rpms"  # Update this to the actual folder path

def get_kernel_version():
    """
    Returns the Linux kernel version as a string.
    It extracts the part before the first '-' from the release string.
    For example, from '4.18.0-147.el8.x86_64', it returns '4.18.0'.
    """
 #   return platform.uname().release.split('-')[0]
    return platform.uname().release
      
def install_rpm(kernel_version):
    """
    Installs the kernel-devel package using dnf from the fixed RPM folder.
    Constructs the package filename using the kernel version.
    """
    package_file = f"kernel-devel-{kernel_version}.rpm"
    package_path = os.path.join(FIXED_RPM_FOLDER, package_file)
    
    try:
        subprocess.run(["rpm", "-ivh" , "--replacepkgs" , package_path , "--nodeps"], check=True)
        print(f"Successfully installed {package_file}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package_file}. Error: {e}")

def main():
    kernel_version = get_kernel_version()
    print(f"Kernel Version: {kernel_version}")
    print(f"Using RPM package from fixed folder: {FIXED_RPM_FOLDER}")
    install_rpm(kernel_version)

if __name__ == "__main__":
    main()
