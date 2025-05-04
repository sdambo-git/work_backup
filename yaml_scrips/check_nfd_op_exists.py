import subprocess
import shutil
import json

def check_oc_installed():
    """Verify that the oc CLI is installed and available."""
    if shutil.which("oc") is None:
        print("Error: 'oc' command not found. Please install the OpenShift CLI (oc).")
        return False
        return True

def check_node_feature_discovery():
    """Check if NodeFeatureDiscovery is installed in the openshift-nfd namespace."""
    if not check_oc_installed():
        return
    
    try:
        # Run the oc command to get NodeFeatureDiscovery resource in the specified namespace
        result = subprocess.run(
            ["oc", "get", "NodeFeatureDiscovery", "-n", "openshift-nfd"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print("NodeFeatureDiscovery is installed in the 'openshift-nfd' namespace:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("NodeFeatureDiscovery is not installed or the oc command failed:")
        print(e.stderr)

        #if __name__ == "__main__":
        check_node_feature_discovery()

