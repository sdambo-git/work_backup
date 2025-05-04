"""
NVIDIA GPU Validation Module for OpenShift

This module provides validation functions to check GPU configuration and identify
common issues in OpenShift environments. It can help troubleshoot problems related
to NVIDIA GPU setup, driver installation, and container configuration.
"""

import os
import subprocess
import re
import json
import logging
from typing import Dict, List, Tuple, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("gpu_validator")

class GPUValidator:
    """
    Main class for validating GPU configuration in OpenShift environments.
    """
    
    def __init__(self, namespace: str = "nvidia-gpu-operator"):
        """
        Initialize the GPU validator.
        
        Args:
            namespace: The OpenShift namespace where GPU operators are installed
        """
        self.namespace = namespace
        self.validation_results = {}
    
    def run_command(self, command: List[str]) -> Tuple[str, str, int]:
        """
        Run a shell command and return its output.
        
        Args:
            command: List of command components
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            stdout, stderr = process.communicate()
            return stdout, stderr, process.returncode
        except Exception as e:
            logger.error(f"Error executing command {' '.join(command)}: {str(e)}")
            return "", str(e), 1
    
    def validate_oc_connection(self) -> bool:
        """Check if OpenShift client is connected to a cluster."""
        stdout, stderr, return_code = self.run_command(["oc", "whoami"])
        
        if return_code != 0:
            self.validation_results["oc_connection"] = {
                "status": "failed",
                "message": "Not connected to OpenShift cluster. Please run 'oc login' first.",
                "details": stderr
            }
            return False
        
        self.validation_results["oc_connection"] = {
            "status": "passed",
            "message": f"Connected to OpenShift cluster as {stdout.strip()}"
        }
        return True
    
    def validate_gpu_operator_installation(self) -> bool:
        """Check if GPU operator is installed and which version."""
        stdout, stderr, return_code = self.run_command([
            "oc", "get", "csv", "-n", self.namespace, "-o", "json"
        ])
        
        if return_code != 0:
            self.validation_results["gpu_operator"] = {
                "status": "failed",
                "message": f"Failed to get ClusterServiceVersions from {self.namespace} namespace",
                "details": stderr
            }
            return False
        
        try:
            csv_data = json.loads(stdout)
            items = csv_data.get("items", [])
            gpu_operator_found = False
            
            for item in items:
                name = item.get("metadata", {}).get("name", "")
                if "gpu-operator" in name.lower():
                    gpu_operator_found = True
                    version = item.get("spec", {}).get("version", "unknown")
                    self.validation_results["gpu_operator"] = {
                        "status": "passed",
                        "message": f"GPU Operator installed, version: {version}",
                        "details": {
                            "name": name,
                            "version": version
                        }
                    }
                    break
            
            if not gpu_operator_found:
                self.validation_results["gpu_operator"] = {
                    "status": "failed",
                    "message": "GPU Operator not found in the specified namespace",
                }
                return False
            
            return True
                
        except json.JSONDecodeError:
            self.validation_results["gpu_operator"] = {
                "status": "failed",
                "message": "Failed to parse JSON output from OpenShift",
                "details": stdout
            }
            return False
    
    def validate_gpu_operator_pods(self) -> bool:
        """Check if all GPU operator pods are running."""
        stdout, stderr, return_code = self.run_command([
            "oc", "get", "pods", "-n", self.namespace, "-o", "json"
        ])
        
        if return_code != 0:
            self.validation_results["gpu_operator_pods"] = {
                "status": "failed",
                "message": f"Failed to get pods from {self.namespace} namespace",
                "details": stderr
            }
            return False
        
        try:
            pod_data = json.loads(stdout)
            pods = pod_data.get("items", [])
            
            problematic_pods = []
            for pod in pods:
                pod_name = pod.get("metadata", {}).get("name", "unknown")
                pod_status = pod.get("status", {})
                phase = pod_status.get("phase", "Unknown")
                
                if phase != "Running":
                    container_statuses = pod_status.get("containerStatuses", [])
                    reasons = []
                    
                    for container in container_statuses:
                        if not container.get("ready", False):
                            waiting = container.get("state", {}).get("waiting", {})
                            reason = waiting.get("reason", "Unknown")
                            message = waiting.get("message", "No details available")
                            reasons.append(f"{reason}: {message}")
                    
                    problematic_pods.append({
                        "name": pod_name,
                        "phase": phase,
                        "reasons": reasons
                    })
            
            if problematic_pods:
                self.validation_results["gpu_operator_pods"] = {
                    "status": "failed",
                    "message": f"Found {len(problematic_pods)} problematic pods",
                    "details": problematic_pods
                }
                return False
            else:
                self.validation_results["gpu_operator_pods"] = {
                    "status": "passed",
                    "message": f"All pods in {self.namespace} namespace are running"
                }
                return True
                
        except json.JSONDecodeError:
            self.validation_results["gpu_operator_pods"] = {
                "status": "failed",
                "message": "Failed to parse JSON output from OpenShift",
                "details": stdout
            }
            return False
    
    def validate_node_gpu_status(self) -> bool:
        """Check if GPUs are properly exposed on nodes."""
        stdout, stderr, return_code = self.run_command([
            "oc", "get", "nodes", "-o", "json"
        ])
        
        if return_code != 0:
            self.validation_results["node_gpu_status"] = {
                "status": "failed",
                "message": "Failed to get nodes information",
                "details": stderr
            }
            return False
        
        try:
            node_data = json.loads(stdout)
            nodes = node_data.get("items", [])
            
            nodes_with_gpus = []
            nodes_without_gpus = []
            
            for node in nodes:
                node_name = node.get("metadata", {}).get("name", "unknown")
                capacity = node.get("status", {}).get("capacity", {})
                
                # Check for NVIDIA GPUs
                nvidia_gpu_count = capacity.get("nvidia.com/gpu", "0")
                
                if nvidia_gpu_count and int(nvidia_gpu_count) > 0:
                    nodes_with_gpus.append({
                        "name": node_name,
                        "gpu_count": nvidia_gpu_count
                    })
                else:
                    nodes_without_gpus.append(node_name)
            
            if not nodes_with_gpus:
                self.validation_results["node_gpu_status"] = {
                    "status": "failed",
                    "message": "No nodes with GPUs found in the cluster",
                    "details": {
                        "nodes_checked": len(nodes),
                        "nodes_without_gpus": nodes_without_gpus
                    }
                }
                return False
            else:
                self.validation_results["node_gpu_status"] = {
                    "status": "passed",
                    "message": f"Found {len(nodes_with_gpus)} nodes with GPUs",
                    "details": {
                        "nodes_with_gpus": nodes_with_gpus,
                        "nodes_without_gpus": nodes_without_gpus
                    }
                }
                return True
                
        except json.JSONDecodeError:
            self.validation_results["node_gpu_status"] = {
                "status": "failed",
                "message": "Failed to parse JSON output from OpenShift",
                "details": stdout
            }
            return False
    
    def validate_gpu_feature_discovery(self) -> bool:
        """Check if GPU feature discovery is working."""
        stdout, stderr, return_code = self.run_command([
            "oc", "get", "nodes", "-o", "json"
        ])
        
        if return_code != 0:
            self.validation_results["gpu_feature_discovery"] = {
                "status": "failed",
                "message": "Failed to get nodes information",
                "details": stderr
            }
            return False
        
        try:
            node_data = json.loads(stdout)
            nodes = node_data.get("items", [])
            
            nodes_with_gpu_labels = []
            nodes_missing_labels = []
            
            for node in nodes:
                node_name = node.get("metadata", {}).get("name", "unknown")
                labels = node.get("metadata", {}).get("labels", {})
                capacity = node.get("status", {}).get("capacity", {})
                
                # Check if node has GPUs
                nvidia_gpu_count = capacity.get("nvidia.com/gpu", "0")
                if int(nvidia_gpu_count) == 0:
                    continue
                
                # Check for GPU feature discovery labels
                gpu_labels = {}
                missing_labels = []
                
                # Key GPU feature discovery labels
                expected_labels = [
                    "feature.node.kubernetes.io/pci-10de.present",  # NVIDIA vendor ID
                    "nvidia.com/gpu.present",
                    "nvidia.com/gpu.count",
                    "nvidia.com/gpu.product",
                    "nvidia.com/gpu.memory"
                ]
                
                for label in expected_labels:
                    if label in labels:
                        gpu_labels[label] = labels[label]
                    else:
                        missing_labels.append(label)
                
                if missing_labels:
                    nodes_missing_labels.append({
                        "name": node_name,
                        "missing_labels": missing_labels,
                        "existing_gpu_labels": gpu_labels
                    })
                else:
                    nodes_with_gpu_labels.append({
                        "name": node_name,
                        "gpu_labels": gpu_labels
                    })
            
            if nodes_missing_labels:
                self.validation_results["gpu_feature_discovery"] = {
                    "status": "failed",
                    "message": f"Found {len(nodes_missing_labels)} nodes with missing GPU feature labels",
                    "details": {
                        "nodes_with_complete_labels": nodes_with_gpu_labels,
                        "nodes_with_missing_labels": nodes_missing_labels
                    }
                }
                return False
            elif not nodes_with_gpu_labels:
                self.validation_results["gpu_feature_discovery"] = {
                    "status": "failed",
                    "message": "No nodes with GPU feature labels found",
                }
                return False
            else:
                self.validation_results["gpu_feature_discovery"] = {
                    "status": "passed",
                    "message": f"Found {len(nodes_with_gpu_labels)} nodes with proper GPU feature labels",
                    "details": {
                        "nodes": nodes_with_gpu_labels
                    }
                }
                return True
                
        except json.JSONDecodeError:
            self.validation_results["gpu_feature_discovery"] = {
                "status": "failed",
                "message": "Failed to parse JSON output from OpenShift",
                "details": stdout
            }
            return False
    
    def validate_driver_daemonset(self) -> bool:
        """Check if NVIDIA driver daemonset is properly installed."""
        stdout, stderr, return_code = self.run_command([
            "oc", "get", "daemonset", "-n", self.namespace, "-o", "json"
        ])
        
        if return_code != 0:
            self.validation_results["driver_daemonset"] = {
                "status": "failed",
                "message": f"Failed to get daemonsets from {self.namespace} namespace",
                "details": stderr
            }
            return False
        
        try:
            ds_data = json.loads(stdout)
            daemonsets = ds_data.get("items", [])
            
            driver_ds = None
            for ds in daemonsets:
                name = ds.get("metadata", {}).get("name", "")
                if "nvidia-driver" in name.lower():
                    driver_ds = ds
                    break
            
            if not driver_ds:
                self.validation_results["driver_daemonset"] = {
                    "status": "failed",
                    "message": "NVIDIA driver daemonset not found"
                }
                return False
            
            # Check daemonset status
            status = driver_ds.get("status", {})
            desired_count = status.get("desiredNumberScheduled", 0)
            current_count = status.get("currentNumberScheduled", 0)
            ready_count = status.get("numberReady", 0)
            
            if desired_count == 0:
                self.validation_results["driver_daemonset"] = {
                    "status": "failed",
                    "message": "NVIDIA driver daemonset exists but is not scheduled on any nodes",
                }
                return False
            
            if ready_count < desired_count:
                self.validation_results["driver_daemonset"] = {
                    "status": "failed",
                    "message": f"NVIDIA driver daemonset not fully ready: {ready_count}/{desired_count} ready",
                    "details": {
                        "name": driver_ds.get("metadata", {}).get("name", ""),
                        "desired": desired_count,
                        "current": current_count,
                        "ready": ready_count
                    }
                }
                return False
            
            self.validation_results["driver_daemonset"] = {
                "status": "passed",
                "message": f"NVIDIA driver daemonset is running properly: {ready_count}/{desired_count} ready",
                "details": {
                    "name": driver_ds.get("metadata", {}).get("name", ""),
                    "desired": desired_count,
                    "current": current_count,
                    "ready": ready_count
                }
            }
            return True
                
        except json.JSONDecodeError:
            self.validation_results["driver_daemonset"] = {
                "status": "failed",
                "message": "Failed to parse JSON output from OpenShift",
                "details": stdout
            }
            return False
    
    def validate_gpu_workload(self, namespace: str, pod_name: str) -> bool:
        """
        Check if a specific GPU workload is running correctly.
        
        Args:
            namespace: The namespace where the pod is running
            pod_name: The name of the pod to check
        """
        stdout, stderr, return_code = self.run_command([
            "oc", "get", "pod", pod_name, "-n", namespace, "-o", "json"
        ])
        
        if return_code != 0:
            self.validation_results["gpu_workload"] = {
                "status": "failed",
                "message": f"Failed to get pod {pod_name} in namespace {namespace}",
                "details": stderr
            }
            return False
        
        try:
            pod_data = json.loads(stdout)
            phase = pod_data.get("status", {}).get("phase", "Unknown")
            
            if phase != "Running":
                # Check for GPU-related issues
                container_statuses = pod_data.get("status", {}).get("containerStatuses", [])
                reasons = []
                
                for container in container_statuses:
                    if not container.get("ready", False):
                        waiting = container.get("state", {}).get("waiting", {})
                        reason = waiting.get("reason", "Unknown")
                        message = waiting.get("message", "No details available")
                        reasons.append(f"{reason}: {message}")
                
                self.validation_results["gpu_workload"] = {
                    "status": "failed",
                    "message": f"GPU workload pod {pod_name} is not running (status: {phase})",
                    "details": {
                        "reasons": reasons
                    }
                }
                return False
            
            # Check for GPU allocation
            resources = pod_data.get("spec", {}).get("containers", [{}])[0].get("resources", {})
            limits = resources.get("limits", {})
            requests = resources.get("requests", {})
            
            gpu_limit = limits.get("nvidia.com/gpu", "0")
            gpu_request = requests.get("nvidia.com/gpu", "0")
            
            if gpu_limit == "0" and gpu_request == "0":
                self.validation_results["gpu_workload"] = {
                    "status": "failed",
                    "message": f"Pod {pod_name} is not requesting any GPUs",
                }
                return False
            
            # Check for GPU usage in logs
            stdout, stderr, return_code = self.run_command([
                "oc", "logs", pod_name, "-n", namespace
            ])
            
            if return_code != 0:
                self.validation_results["gpu_workload"] = {
                    "status": "warning",
                    "message": f"Pod {pod_name} is running but could not retrieve logs",
                    "details": {
                        "gpu_limit": gpu_limit,
                        "gpu_request": gpu_request,
                        "log_error": stderr
                    }
                }
                return True
            
            # Check for common GPU errors in logs
            gpu_errors = [
                "CUDA_ERROR_NOT_INITIALIZED",
                "CUDA_ERROR_NO_DEVICE",
                "Failed to initialize NVML",
                "no CUDA-capable device is detected",
                "NVIDIA-SMI has failed"
            ]
            
            found_errors = []
            for error in gpu_errors:
                if error in stdout:
                    found_errors.append(error)
            
            if found_errors:
                self.validation_results["gpu_workload"] = {
                    "status": "failed",
                    "message": f"Pod {pod_name} has GPU-related errors in logs",
                    "details": {
                        "errors": found_errors
                    }
                }
                return False
            
            self.validation_results["gpu_workload"] = {
                "status": "passed",
                "message": f"GPU workload pod {pod_name} is running correctly",
                "details": {
                    "gpu_limit": gpu_limit,
                    "gpu_request": gpu_request
                }
            }
            return True
                
        except json.JSONDecodeError:
            self.validation_results["gpu_workload"] = {
                "status": "failed",
                "message": "Failed to parse JSON output from OpenShift",
                "details": stdout
            }
            return False
    
    def validate_nvidia_smi_on_node(self, node_name: str) -> bool:
        """
        Check if nvidia-smi is working on a specific node.
        
        Args:
            node_name: The name of the node to check
        """
        debug_pod_name = f"nvidia-smi-debug-{node_name.split('.')[0]}"
        
        # Create a debug pod
        pod_json = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": debug_pod_name
            },
            "spec": {
                "containers": [{
                    "name": "nvidia-smi-debug",
                    "image": "nvidia/cuda:11.8.0-base-ubuntu22.04",
                    "command": ["sleep", "infinity"],
                    "resources": {
                        "limits": {
                            "nvidia.com/gpu": "1"
                        }
                    }
                }],
                "nodeSelector": {
                    "kubernetes.io/hostname": node_name
                },
                "restartPolicy": "Never"
            }
        }
        
        # Create a temporary file for the pod definition
        temp_file = "/tmp/nvidia-smi-debug.json"
        with open(temp_file, "w") as f:
            json.dump(pod_json, f)
        
        # Create the pod
        stdout, stderr, return_code = self.run_command([
            "oc", "create", "-f", temp_file
        ])
        
        if return_code != 0:
            self.validation_results[f"nvidia_smi_{node_name}"] = {
                "status": "failed",
                "message": f"Failed to create debug pod on node {node_name}",
                "details": stderr
            }
            return False
        
        # Wait for the pod to be running
        import time
        for _ in range(30):  # Wait up to 30 seconds
            stdout, stderr, return_code = self.run_command([
                "oc", "get", "pod", debug_pod_name, "-o", "json"
            ])
            
            if return_code == 0:
                pod_data = json.loads(stdout)
                phase = pod_data.get("status", {}).get("phase", "Unknown")
                if phase == "Running":
                    break
            
            time.sleep(1)
        
        # Run nvidia-smi in the pod
        stdout, stderr, return_code = self.run_command([
            "oc", "exec", debug_pod_name, "--", "nvidia-smi"
        ])
        
        # Clean up the pod
        self.run_command([
            "oc", "delete", "pod", debug_pod_name
        ])
        
        if return_code != 0:
            self.validation_results[f"nvidia_smi_{node_name}"] = {
                "status": "failed",
                "message": f"nvidia-smi failed on node {node_name}",
                "details": stderr
            }
            return False
        
        # Check for expected output
        if "NVIDIA-SMI" in stdout and "Driver Version" in stdout:
            # Extract driver version
            driver_version_match = re.search(r"Driver Version: (\d+\.\d+\.\d+)", stdout)
            driver_version = driver_version_match.group(1) if driver_version_match else "Unknown"
            
            # Extract GPU information
            gpu_info = []
            lines = stdout.strip().split("\n")
            for i, line in enumerate(lines):
                if "|" in line and "%" in line and "MiB" in line:
                    gpu_info.append(line.strip())
            
            self.validation_results[f"nvidia_smi_{node_name}"] = {
                "status": "passed",
                "message": f"nvidia-smi is working on node {node_name}",
                "details": {
                    "driver_version": driver_version,
                    "gpu_info": gpu_info
                }
            }
            return True
        else:
            self.validation_results[f"nvidia_smi_{node_name}"] = {
                "status": "failed",
                "message": f"nvidia-smi output is not as expected on node {node_name}",
                "details": stdout
            }
            return False
    
    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validations and return the results."""
        # Check OpenShift connection first
        if not self.validate_oc_connection():
            return self.validation_results
        
        # Run all validations
        self.validate_gpu_operator_installation()
        self.validate_gpu_operator_pods()
        self.validate_node_gpu_status()
        self.validate_gpu_feature_discovery()
        self.validate_driver_daemonset()
        
        # Check GPU nodes with nvidia-smi
        stdout, stderr, return_code = self.run_command([
            "oc", "get", "nodes", "-o", "json"
        ])
        
        if return_code == 0:
            try:
                node_data = json.loads(stdout)
                nodes = node_data.get("items", [])
                
                for node in nodes:
                    node_name = node.get("metadata", {}).get("name", "unknown")
                    capacity = node.get("status", {}).get("capacity", {})
                    
                    # Check for NVIDIA GPUs
                    nvidia_gpu_count = capacity.get("nvidia.com/gpu", "0")
                    
                    if nvidia_gpu_count and int(nvidia_gpu_count) > 0:
                        self.validate_nvidia_smi_on_node(node_name)
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON output from OpenShift")
        
        return self.validation_results
    
    def print_validation_results(self) -> None:
        """Print validation results in a human-readable format."""
        print("\n===== GPU Validation Results =====\n")
        
        for validation_name, result in self.validation_results.items():
            status = result.get("status", "unknown")
            message = result.get("message", "No message")
            
            if status == "passed":
                status_str = "✅ PASSED"
            elif status == "failed":
                status_str = "❌ FAILED"
            elif status == "warning":
                status_str = "⚠️ WARNING"
            else:
                status_str = "❓ UNKNOWN"
            
            print(f"{status_str} - {validation_name}: {message}")
        
        print("\nFor detailed results, use the .validation_results dictionary.")

def validate_gpu_setup(namespace: str = "nvidia-gpu-operator") -> Dict[str, Any]:
    """
    Validate GPU setup in OpenShift environment.
    
    Args:
        namespace: The namespace where the GPU operator is installed
        
    Returns:
        Dictionary of validation results
    """
    validator = GPUValidator(namespace)
    results = validator.run_all_validations()
    validator.print_validation_results()
    return results

def test_gpu_workload(namespace: str, pod_name: str) -> bool:
    """
    Test if a specific GPU workload is running correctly.
    
    Args:
        namespace: The namespace where the pod is running
        pod_name: The name of the pod to check
        
    Returns:
        True if the workload is running correctly, False otherwise
    """
    validator = GPUValidator()
    validator.validate_oc_connection()
    result = validator.validate_gpu_workload(namespace, pod_name)
    validator.print_validation_results()
    return result

def create_gpu_test_pod(namespace: str, node_name: Optional[str] = None) -> str:
    """
    Create a test pod to validate GPU functionality.
    
    Args:
        namespace: The namespace where to create the pod
        node_name: Optional node name to schedule the pod on
        
    Returns:
        The name of the created pod
    """
    pod_name = f"gpu-test-{int(time.time())}"
    
    # Create a pod definition
    pod_json = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": pod_name,
            "namespace": namespace
        },
        "spec": {
            "containers": [{
                "name": "gpu-test",
                "image": "nvidia/cuda:11.8.0-base-ubuntu22.04",
                "command": [
                    "sh",
                    "-c",
                    "nvidia-smi && sleep 3600"
                ],
                "resources": {
                    "limits": {
                        "nvidia.com/gpu": "1"
                    }
                }
            }],
            "restartPolicy": "Never"
        }
    }
    
    # Add node selector if a node name is provided
    if node_name:
        pod_json["spec"]["nodeSelector"] = {
            "kubernetes.io/hostname": node_name
        }
    
    # Create a temporary file for the pod definition
    temp_file = f"/tmp/gpu-test-pod-{pod_name}.json"
    with open(temp_file, "w") as f:
        json.dump(pod_json, f)
    
    # Create the pod
    stdout, stderr, return_code = subprocess.run(
        ["oc", "create", "-f", temp_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    if return_code != 0:
        logger.error(f"Failed to create GPU test pod: {stderr}")
        return ""
    
    logger.info(f"Created GPU test pod: {pod_name}")
    return pod_name

if __name__ == "__main__":
    print("GPU Validation Module")
    print("Usage:")
    print("  from gpu_validator import validate_gpu_setup")
    print("  results = validate_gpu_setup()")
    print("  # or")
    print("  from gpu_validator import test_gpu_workload")
    print("  is_valid = test_gpu_workload('my-namespace', 'my-gpu-pod')")
