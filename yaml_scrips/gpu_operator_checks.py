import subprocess
import sys

def check_oc_installation():
    """Check if the OpenShift CLI (oc) is installed on the system."""
    try:
        version_result = subprocess.run(
            "oc version",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if version_result.returncode == 0:
            print("OpenShift CLI (oc) is installed:")
            print(version_result.stdout)
            return True
        else:
            print("OpenShift CLI (oc) installation check failed:")
            print(version_result.stderr)
            return False
    except FileNotFoundError:
        print("Error: 'oc' command not found")
        print("Please ensure the OpenShift CLI ('oc') is installed and added to your PATH")
        return False

def check_nfd_create():
    # Command to check NodeFeatureDiscovery
    command = "oc get NodeFeatureDiscovery -n openshift-nfd"
    
    try:
        # Execute the command and capture output
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Check the return code
        if result.returncode == 0:
            print("NodeFeatureDiscovery check executed successfully!")
            print("Output:")
            print(result.stdout)
        else:
            print("NodeFeatureDiscovery check failed with the following error:")
            print(result.stderr)
            print("\nPossible issues:")
            print("- Not logged into an OpenShift cluster")
            print("- No access to the 'openshift-nfd' namespace")
            print("- NodeFeatureDiscovery resource doesn't exist")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

 
def check_nvidia_gpu_nodes():
    # Command to check nodes with NVIDIA GPUs
    command = "oc get nodes -l feature.node.kubernetes.io/pci-10de.present"
    
    try:
        # Execute the command and capture output
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Check the return code
        if result.returncode == 0:
            print("NVIDIA GPU nodes check executed successfully!")
            if result.stdout.strip():  # Check if there's any output
                print("Nodes with NVIDIA GPUs found:")
                print(result.stdout)
            else:
                print("No nodes with NVIDIA GPUs found in the cluster")
        else:
            print("NVIDIA GPU nodes check failed with the following error:")
            print(result.stderr)
            print("\nPossible issues:")
            print("- Not logged into an OpenShift cluster")
            print("- Node Feature Discovery operator might not be installed")
            print("- No nodes with NVIDIA GPUs exist in the cluster")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

def check_clusterpolicy_crd():
    """Check if the ClusterPolicy CRD exists in the cluster."""
    command = "oc get crd/clusterpolicies.nvidia.com"
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            print("ClusterPolicy CRD check executed successfully!")
            print("Output:")
            print(result.stdout)
        else:
            print("ClusterPolicy CRD check failed with the following error:")
            print(result.stderr)
            print("\nPossible issues:")
            print("- Not logged into an OpenShift cluster")
            print("- NVIDIA GPU Operator might not be installed")
            print("- ClusterPolicy CRD has not been deployed")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

def check_clusterpolicy_status():
    """Check the status of ClusterPolicy instances and fetch details if not ready."""
    # Step 1: Get the list of ClusterPolicies and their states
    get_command = "oc get clusterpolicy -o custom-columns=NAME:.metadata.name,STATE:.status.state --no-headers"
    try:
        get_result = subprocess.run(
            get_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Check if the oc get command executed successfully
        if get_result.returncode == 0:
            output_lines = get_result.stdout.strip().splitlines()
            if output_lines:
                for line in output_lines:
                    # Parse name and state from each line
                    parts = line.split()
                    if len(parts) >= 2:
                        name, state = parts[0], parts[1]
                        print(f"ClusterPolicy {name}: {state}")
                        
                        # Step 2: If NotReady, run oc describe to get the message
                        if state == "notReady":
                            describe_command = f"oc describe clusterpolicy {name}"
                            try:
                                describe_result = subprocess.run(
                                    describe_command,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True
                                )
                                if describe_result.returncode == 0:
                                    message = parse_ready_condition_message(describe_result.stdout)
                                    if message:
                                        print(f"  Message: {message}")
                                    else:
                                        print("  No detailed message found for the Ready condition")
                                else:
                                    print("  Failed to run oc describe:")
                                    print(f"  {describe_result.stderr}")
                            except Exception as e:
                                print(f"  An error occurred while running oc describe: {str(e)}")
                    else:
                        print(f"Unexpected output format: {line}")
            else:
                print("No ClusterPolicy instances found in the cluster")
        else:
            print("Failed to retrieve ClusterPolicy status:")
            print(get_result.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

def parse_ready_condition_message(describe_output):
    """Parse the oc describe output to find the Message for the Ready condition with Status: False."""
    lines = describe_output.splitlines()
    in_conditions = False
    current_type = None
    current_status = None
    for line in lines:
        line = line.strip()
        if line.startswith("Conditions:"):
            in_conditions = True
        elif in_conditions:
            if line.startswith("Type:"):
                current_type = line.split(":", 1)[1].strip()
            elif line.startswith("Status:"):
                current_status = line.split(":", 1)[1].strip()
            elif line.startswith("Message:") and current_type == "Ready" and current_status == "False":
                return line.split(":", 1)[1].strip()
    return None

def check_gpu_operator_logs():
    """Fetch and display logs for GPU operator pods in the nvidia-gpu-operator namespace."""
    command = "oc logs -n nvidia-gpu-operator -lapp=gpu-operator"
    try:
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            print("GPU operator logs retrieved successfully!")
            if result.stdout.strip():
                print("Logs:")
                print(result.stdout)
            else:
                print("No logs found for GPU operator pods.")
        else:
            print("Failed to retrieve GPU operator logs:")
            print(result.stderr)
            print("\nPossible issues:")
            print("- Not logged into an OpenShift cluster")
            print("- The 'nvidia-gpu-operator' namespace does not exist")
            print("- No pods with label 'app=gpu-operator' found")
            print("- No logs available (e.g., pods haven’t started yet)")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

def check_gpu_operator_pods():
    """Check if the GPU operator pods are running in the nvidia-gpu-operator namespace."""
    command = "oc get pods -n nvidia-gpu-operator -lapp=gpu-operator"
    try:
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            if len(lines) > 1:  # Check if there are pods listed beyond the header
                running_pods = 0
                for line in lines[1:]: # Skip the first line as it is assumed to be a header
                    parts = line.split()
                    if len(parts) >= 3 and parts[2] == 'Running':
                        running_pods += 1
                    elif status == 'ImagePullBackOff':
                        error_messages.append("Pod in 'ImagePullBackOff' status: maybe the NVIDIA registry is down.")
                    elif status == 'CrashLoopBackOff':
                        error_messages.append("Pod in 'CrashLoopBackOff' status: review the operator logs.") 
                        check_gpu_operator_logs()

                if running_pods > 0:
                    print(f"GPU operator is running with {running_pods} pod(s) in 'Running' state.")
                    print("Pod details:")
                    print(result.stdout)
                else:
                    print("GPU operator pods are present but none are in 'Running' state.")
                    print("Pod details:")
                    print(result.stdout)
            else:
                print("No GPU operator pods found in the nvidia-gpu-operator namespace.")
        else:
            print("Failed to check GPU operator pods:")
            print(result.stderr)
            print("\nPossible issues:")
            print("- Not logged into an OpenShift cluster")
            print("- The 'nvidia-gpu-operator' namespace does not exist")
            print("- No pods with label 'app=gpu-operator' found")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

# Run the script
if __name__ == "__main__":
    print("Checking OpenShift CLI installation...")
    check_oc_installation()
    print("\nChecking NodeFeatureDiscovery command...")
    check_nfd_create()
    print("\nChecking for nodes with NVIDIA GPUs...")
    check_nvidia_gpu_nodes()
    print("\nChecking ClusterPolicy CRD...")
    check_clusterpolicy_crd()
    print("\nChecking ClusterPolicy status...")
    check_clusterpolicy_status()
    print("\nChecking GPU operator pods...")
    check_gpu_operator_pods()
