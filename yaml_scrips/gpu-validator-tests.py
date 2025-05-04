"""
Unit Tests for GPU Validation Module

This module contains comprehensive unit tests for the GPU validation functions.
Tests use mocking to simulate OpenShift command outputs and responses.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import io
import sys
import os
import tempfile

# Add parent directory to path to import the gpu_validator module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import module to test
from gpu_validator import GPUValidator, validate_gpu_setup, test_gpu_workload

class TestGPUValidator(unittest.TestCase):
    """Test cases for the GPUValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = GPUValidator()
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('subprocess.Popen')
    def test_run_command(self, mock_popen):
        """Test the run_command method."""
        # Setup mock process
        process_mock = MagicMock()
        process_mock.communicate.return_value = ("sample output", "sample error")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        # Run the method
        stdout, stderr, return_code = self.validator.run_command(["test", "command"])

        # Assertions
        mock_popen.assert_called_once_with(
            ["test", "command"],
            stdout=unittest.mock.ANY,
            stderr=unittest.mock.ANY,
            universal_newlines=True
        )
        self.assertEqual(stdout, "sample output")
        self.assertEqual(stderr, "sample error")
        self.assertEqual(return_code, 0)

    @patch('subprocess.Popen')
    def test_run_command_exception(self, mock_popen):
        """Test the run_command method when an exception occurs."""
        # Setup mock process to raise an exception
        mock_popen.side_effect = Exception("Command failed")

        # Run the method
        stdout, stderr, return_code = self.validator.run_command(["test", "command"])

        # Assertions
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "Command failed")
        self.assertEqual(return_code, 1)

    @patch.object(GPUValidator, 'run_command')
    def test_validate_oc_connection_success(self, mock_run_command):
        """Test validate_oc_connection with successful connection."""
        # Setup mock command output
        mock_run_command.return_value = ("test-user", "", 0)

        # Run the method
        result = self.validator.validate_oc_connection()

        # Assertions
        mock_run_command.assert_called_once_with(["oc", "whoami"])
        self.assertTrue(result)
        self.assertEqual(self.validator.validation_results["oc_connection"]["status"], "passed")

    @patch.object(GPUValidator, 'run_command')
    def test_validate_oc_connection_failure(self, mock_run_command):
        """Test validate_oc_connection with failed connection."""
        # Setup mock command output
        mock_run_command.return_value = ("", "error: you must be logged in", 1)

        # Run the method
        result = self.validator.validate_oc_connection()

        # Assertions
        mock_run_command.assert_called_once_with(["oc", "whoami"])
        self.assertFalse(result)
        self.assertEqual(self.validator.validation_results["oc_connection"]["status"], "failed")

    @patch.object(GPUValidator, 'run_command')
    def test_validate_gpu_operator_installation_success(self, mock_run_command):
        """Test validate_gpu_operator_installation with successful installation."""
        # Setup mock command output
        csv_data = {
            "items": [
                {
                    "metadata": {"name": "gpu-operator-certified.v1.10.1"},
                    "spec": {"version": "1.10.1"}
                }
            ]
        }
        mock_run_command.return_value = (json.dumps(csv_data), "", 0)

        # Run the method
        result = self.validator.validate_gpu_operator_installation()

        # Assertions
        mock_run_command.assert_called_once_with([
            "oc", "get", "csv", "-n", "nvidia-gpu-operator", "-o", "json"
        ])
        self.assertTrue(result)
        self.assertEqual(self.validator.validation_results["gpu_operator"]["status"], "passed")
        self.assertEqual(self.validator.validation_results["gpu_operator"]["details"]["version"], "1.10.1")

    @patch.object(GPUValidator, 'run_command')
    def test_validate_gpu_operator_installation_not_found(self, mock_run_command):
        """Test validate_gpu_operator_installation when operator not found."""
        # Setup mock command output
        csv_data = {"items": [{"metadata": {"name": "other-operator"}}]}
        mock_run_command.return_value = (json.dumps(csv_data), "", 0)

        # Run the method
        result = self.validator.validate_gpu_operator_installation()

        # Assertions
        self.assertFalse(result)
        self.assertEqual(self.validator.validation_results["gpu_operator"]["status"], "failed")

    @patch.object(GPUValidator, 'run_command')
    def test_validate_gpu_operator_installation_command_error(self, mock_run_command):
        """Test validate_gpu_operator_installation with command error."""
        # Setup mock command output
        mock_run_command.return_value = ("", "error: namespace not found", 1)

        # Run the method
        result = self.validator.validate_gpu_operator_installation()

        # Assertions
        self.assertFalse(result)
        self.assertEqual(self.validator.validation_results["gpu_operator"]["status"], "failed")

    @patch.object(GPUValidator, 'run_command')
    def test_validate_gpu_operator_installation_json_error(self, mock_run_command):
        """Test validate_gpu_operator_installation with invalid JSON."""
        # Setup mock command output
        mock_run_command.return_value = ("invalid json", "", 0)

        # Run the method
        result = self.validator.validate_gpu_operator_installation()

        # Assertions
        self.assertFalse(result)
        self.assertEqual(self.validator.validation_results["gpu_operator"]["status"], "failed")

    @patch.object(GPUValidator, 'run_command')
    def test_validate_gpu_operator_pods_all_running(self, mock_run_command):
        """Test validate_gpu_operator_pods with all pods running."""
        # Setup mock command output
        pod_data = {
            "items": [
                {
                    "metadata": {"name": "nvidia-driver-daemonset-1234"},
                    "status": {
                        "phase": "Running",
                        "containerStatuses": [
                            {"ready": True}
                        ]
                    }
                },
                {
                    "metadata": {"name": "nvidia-device-plugin-daemonset-5678"},
                    "status": {
                        "phase": "Running",
                        "containerStatuses": [
                            {"ready": True}
                        ]
                    }
                }
            ]
        }
        mock_run_command.return_value = (json.dumps(pod_data), "", 0)

        # Run the method
        result = self.validator.validate_gpu_operator_pods()

        # Assertions
        mock_run_command.assert_called_once_with([
            "oc", "get", "pods", "-n", "nvidia-gpu-operator", "-o", "json"
        ])
        self.assertTrue(result)
        self.assertEqual(self.validator.validation_results["gpu_operator_pods"]["status"], "passed")

    @patch.object(GPUValidator, 'run_command')
    def test_validate_gpu_operator_pods_some_failing(self, mock_run_command):
        """Test validate_gpu_operator_pods with some pods failing."""
        # Setup mock command output
        pod_data = {
            "items": [
                {
                    "metadata": {"name": "nvidia-driver-daemonset-1234"},
                    "status": {
                        "phase": "Running",
                        "containerStatuses": [
                            {"ready": True}
                        ]
                    }
                },
                {
                    "metadata": {"name": "nvidia-device-plugin-daemonset-5678"},
                    "status": {
                        "phase": "CrashLoopBackOff",
                        "containerStatuses": [
                            {
                                "ready": False,
                                "state": {
                                    "waiting": {
                                        "reason": "CrashLoopBackOff",
                                        "message": "Container failed to start"
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        }
        mock_run_command.return_value = (json.dumps(pod_data), "", 0)

        # Run the method
        result = self.validator.validate_gpu_operator_pods()

        # Assertions
        self.assertFalse(result)
        self.assertEqual(self.validator.validation_results["gpu_operator_pods"]["status"], "failed")
        self.assertEqual(len(self.validator.validation_results["gpu_operator_pods"]["details"]), 1)

    @patch.object(GPUValidator, 'run_command')
    def test_validate_node_gpu_status_gpus_found(self, mock_run_command):
        """Test validate_node_gpu_status with GPUs found."""
        # Setup mock command output
        node_data = {
            "items": [
                {
                    "metadata": {"name": "node1.example.com"},
                    "status": {
                        "capacity": {
                            "nvidia.com/gpu": "2"
                        }
                    }
                },
                {
                    "metadata": {"name": "node2.example.com"},
                    "status": {
                        "capacity": {
                            "cpu": "8",
                            "memory": "32Gi"
                        }
                    }
                }
            ]
        }
        mock_run_command.return_value = (json.dumps(node_data), "", 0)

        # Run the method
        result = self.validator.validate_node_gpu_status()

        # Assertions
        mock_run_command.assert_called_once_with([
            "oc", "get", "nodes", "-o", "json"
        ])
        self.assertTrue(result)
        self.assertEqual(self.validator.validation_results["node_gpu_status"]["status"], "passed")
        self.assertEqual(len(self.validator.validation_results["node_gpu_status"]["details"]["nodes_with_gpus"]), 1)

    @patch.object(GPUValidator, 'run_command')
    def test_validate_node_gpu_status_no_gpus(self, mock_run_command):
        """Test validate_node_gpu_status with no GPUs found."""
        # Setup mock command output
        node_data = {
            "items": [
                {
                    "metadata": {"name": "node1.example.com"},
                    "status": {
                        "capacity": {
                            "cpu": "8",
                            "memory": "32Gi"
                        }
                    }
                },
                {
                    "metadata": {"name": "node2.example.com"},
                    "status": {
                        "capacity": {
                            "cpu": "8",
                            "memory": "32Gi"
                        }
                    }
                }
            ]
        }
        mock_run_command.return_value = (json.dumps(node_data), "", 0)

        # Run the method
        result = self.validator.validate_node_gpu_status()

        # Assertions
        self.assertFalse(result)
        self.assertEqual(self.validator.validation_results["node_gpu_status"]["status"], "failed")
        self.assertEqual(len(self.validator.validation_results["node_gpu_status"]["details"]["nodes_without_gpus"]), 2)

    @patch.object(GPUValidator, 'run_command')
    def test_validate_gpu_feature_discovery_success(self, mock_run_command):
        """Test validate_gpu_feature_discovery with successful discovery."""
        # Setup mock command output
        node_data = {
            "items": [
                {
                    "metadata": {
                        "name": "node1.example.com",
                        "labels": {
                            "feature.node.kubernetes.io/pci-10de.present": "true",
                            "nvidia.com/gpu.present": "true",
                            "nvidia.com/gpu.count": "2",
                            "nvidia.com/gpu.product": "Tesla-V100",
                            "nvidia.com/gpu.memory": "32GB"
                        }
                    },
                    "status": {
                        "capacity": {
                            "nvidia.com/gpu": "2"
                        }
                    }
                }
            ]
        }
        mock_run_command.return_value = (json.dumps(node_data), "", 0)

        # Run the method
        result = self.validator.validate_gpu_feature_discovery()

        # Assertions
        mock_run_command.assert_called_once_with([
            "oc", "get", "nodes", "-o", "json"
        ])
        self.assertTrue(result)
        self.assertEqual(self.validator.validation_results["gpu_feature_discovery"]["status"], "passed")

    @patch.object(GPUValidator, 'run_command')
    def test_validate_gpu_feature_discovery_missing_labels(self, mock_run_command):
        """Test validate_gpu_feature_discovery with missing labels."""
        # Setup mock command output
        node_data = {
            "items": [
                {
                    "metadata": {
                        "name": "node1.example.com",
                        "labels": {
                            "feature.node.kubernetes.io/pci-10de.present": "true",
                            "nvidia.com/gpu.count": "2"
                            # Missing some labels
                        }
                    },
                    "status": {
                        "capacity": {
                            "nvidia.com/gpu": "2"
                        }
                    }
                }
            ]
        }
        mock_run_command.return_value = (json.dumps(node_data), "", 0)

        # Run the method
        result = self.validator.validate_gpu_feature_discovery()

        # Assertions
        self.assertFalse(result)
        self.assertEqual(self.validator.validation_results["gpu_feature_discovery"]["status"], "failed")
        self.assertEqual(len(self.validator.validation_results["gpu_feature_discovery"]["details"]["nodes_with_missing_labels"]), 1)

    @patch.object(GPUValidator, 'run_command')
    def test_validate_driver_daemonset_success(self, mock_run_command):
        """Test validate_driver_daemonset with successful driver installation."""
        # Setup mock command output
        ds_data = {
            "items": [
                {
                    "metadata": {"name": "nvidia-driver-daemonset"},
                    "status": {
                        "desiredNumberScheduled": 2,
                        "currentNumberScheduled": 2,
                        "numberReady": 2
                    }
                }
            ]
        }
        mock_run_command.return_value = (json.dumps(ds_data), "", 0)

        # Run the method
        result = self.validator.validate_driver_daemonset()

        # Assertions
        mock_run_command.assert_called_once_with([
            "oc", "get", "daemonset", "-n", "nvidia-gpu-operator", "-o", "json"
        ])
        self.assertTrue(result)
        self.assertEqual(self.validator.validation_results["driver_daemonset"]["status"], "passed")

    @patch.object(GPUValidator, 'run_command')
    def test_validate_driver_daemonset_not_ready(self, mock_run_command):
        """Test validate_driver_daemonset with not ready driver."""
        # Setup mock command output
        ds_data = {
            "items": [
                {
                    "metadata": {"name": "nvidia-driver-daemonset"},
                    "status": {
                        "desiredNumberScheduled": 2,
                        "currentNumberScheduled": 2,
                        "numberReady": 1
                    }
                }
            ]
        }
        mock_run_command.return_value = (json.dumps(ds_data), "", 0)

        # Run the method
        result = self.validator.validate_driver_daemonset()

        # Assertions
        self.assertFalse(result)
        self.assertEqual(self.validator.validation_results["driver_daemonset"]["status"], "failed")

    @patch.object(GPUValidator, 'run_command')
    def test_validate_driver_daemonset_not_found(self, mock_run_command):
        """Test validate_driver_daemonset with driver not found."""
        # Setup mock command output
        ds_data = {
            "items": [
                {
                    "metadata": {"name": "other-daemonset"},
                    "status": {
                        "desiredNumberScheduled": 2,
                        "currentNumberScheduled": 2,
                        "numberReady": 2
                    }
                }
            ]
        }
        mock_run_command.return_value = (json.dumps(ds_data), "", 0)

        # Run the method
        result = self.validator.validate_driver_daemonset()

        # Assertions
        self.assertFalse(result)
        self.assertEqual(self.validator.validation_results["driver_daemonset"]["status"], "failed")

    @patch.object(GPUValidator, 'run_command')
    def test_validate_gpu_workload_success(self, mock_run_command):
        """Test validate_gpu_workload with successful workload."""
        # Setup mock command output for pod info
        pod_data = {
            "status": {
                "phase": "Running",
                "containerStatuses": [
                    {"ready": True}
                ]
            },
            "spec": {
                "containers": [
                    {
                        "resources": {
                            "limits": {
                                "nvidia.com/gpu": "1"
                            },
                            "requests": {
                                "nvidia.com/gpu": "1"
                            }
                        }
                    }
                ]
            }
        }
        # Setup mock command output for pod logs
        pod_logs = "NVIDIA-SMI 470.57.02    Driver Version: 470.57.02    CUDA Version: 11.4"
        
        # Use side_effect to return different values for different calls
        mock_run_command.side_effect = [
            (json.dumps(pod_data), "", 0),  # First call: get pod info
            (pod_logs, "", 0)               # Second call: get pod logs
        ]

        # Run the method
        result = self.validator.validate_gpu_workload("test-namespace", "test-pod")

        # Assertions
        self.assertTrue(result)
        self.assertEqual(self.validator.validation_results["gpu_workload"]["status"], "passed")

    @patch.object(GPUValidator, 'run_command')
    def test_validate_gpu_workload_not_running(self, mock_run_command):
        """Test validate_gpu_workload with non-running workload."""
        # Setup mock command output
        pod_data = {
            "status": {
                "phase": "Pending",
                "containerStatuses": [
                    {
                        "ready": False,
                        "state": {
                            "waiting": {
                                "reason": "ContainerCreating",
                                "message": "Container is being created"
                            }
                        }
                    }
                ]
            },
            "spec": {
                "containers": [
                    {
                        "resources": {
                            "limits": {
                                "nvidia.com/gpu": "1"
                            },
                            "requests": {
                                "nvidia.com/gpu": "1"
                            }
                        }
                    }
                ]
            }
        }
        mock_run_command.return_value = (json.dumps(pod_data), "", 0)

        # Run the method
        result = self.validator.validate_gpu_workload("test-namespace", "test-pod")

        # Assertions
        self.assertFalse(result)
        self.assertEqual(self.validator.validation_results["gpu_workload"]["status"], "failed")

    @patch.object(GPUValidator, 'run_command')
    def test_validate_gpu_workload_no_gpu_request(self, mock_run_command):
        """Test validate_gpu_workload with no GPU request."""
        # Setup mock command output
        pod_data = {
            "status": {
                "phase": "Running",
                "containerStatuses": [
                    {"ready": True}
                ]
            },
            "spec": {
                "containers": [
                    {
                        "resources": {
                            "limits": {},
                            "requests": {}
                        }
                    }
                ]
            }
        }
        mock_run_command.return_value = (json.dumps(pod_data), "", 0)

        # Run the method
        result = self.validator.validate_gpu_workload("test-namespace", "test-pod")

        # Assertions
        self.assertFalse(result)
        self.assertEqual(self.validator.validation_results["gpu_workload"]["status"], "failed")

    @patch.object(GPUValidator, 'run_command')
    def test_validate_gpu_workload_errors_in_logs(self, mock_run_command):
        """Test validate_gpu_workload with errors in logs."""
        # Setup mock command output for pod info
        pod_data = {
            "status": {
                "phase": "Running",
                "containerStatuses": [
                    {"ready": True}
                ]
            },
            "spec": {
                "containers": [
                    {
                        "resources": {
                            "limits": {
                                "nvidia.com/gpu": "1"
                            },
                            "requests": {
                                "nvidia.com/gpu": "1"
                            }
                        }
                    }
                ]
            }
        }
        # Setup mock command output for pod logs with errors
        pod_logs = "Failed to initialize NVML: Driver/library version mismatch"
        
        # Use side_effect to return different values for different calls
        mock_run_command.side_effect = [
            (json.dumps(pod_data), "", 0),  # First call: get pod info
            (pod_logs, "", 0)               # Second call: get pod logs
        ]

        # Run the method
        result = self.validator.validate_gpu_workload("test-namespace", "test-pod")

        # Assertions
        self.assertFalse(result)
        self.assertEqual(self.validator.validation_results["gpu_workload"]["status"], "failed")
        self.assertIn("Failed to initialize NVML", self.validator.validation_results["gpu_workload"]["details"]["errors"][0])

    @patch.object(GPUValidator, 'run_command')
    def test_validate_nvidia_smi_on_node_success(self, mock_run_command):
        """Test validate_nvidia_smi_on_node with successful execution."""
        # Setup mock command outputs
        create_pod_output = ("pod/nvidia-smi-debug-node1 created", "", 0)
        pod_status_output = (json.dumps({"status": {"phase": "Running"}}), "", 0)
        nvidia_smi_output = (
            "Tue Mar 18 12:34:56 2025       \n"
            "+-----------------------------------------------------------------------------+\n"
            "| NVIDIA-SMI 470.57.02    Driver Version: 470.57.02    CUDA Version: 11.4     |\n"
            "|-------------------------------+----------------------+----------------------+\n"
            "| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |\n"
            "| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |\n"
            "|===============================+======================+======================|\n"
            "|   0  Tesla V100-SXM2...  On   | 00000000:00:1E.0 Off |                    0 |\n"
            "| N/A   35C    P0    40W / 300W |   1234MiB / 32510MiB |      0%      Default |\n"
            "+-------------------------------+----------------------+----------------------+\n",
            "",
            0
        )
        delete_pod_output = ("pod/nvidia-smi-debug-node1 deleted", "", 0)
        
        # Set up side_effect to return different outputs for different calls
        mock_run_command.side_effect = [
            create_pod_output,
            pod_status_output,
            nvidia_smi_output,
            delete_pod_output
        ]

        # Patch open to mock file operations
        with patch('builtins.open', mock_open()):
            # Patch json.dump to do nothing
            with patch('json.dump') as mock_json_dump:
                # Run the method
                result = self.validator.validate_nvidia_smi_on_node("node1.example.com")

                # Assertions
                self.assertTrue(result)
                self.assertEqual(self.validator.validation_results["nvidia_smi_node1.example.com"]["status"], "passed")
                self.assertEqual(self.validator.validation_results["nvidia_smi_node1.example.com"]["details"]["driver_version"], "470.57.02")
                self.assertIn("Tesla V100", self.validator.validation_results["nvidia_smi_node1.example.com"]["details"]["gpu_info"][0])

    @patch.object(GPUValidator, 'run_command')
    def test_validate_nvidia_smi_on_node_failure(self, mock_run_command):
        """Test validate_nvidia_smi_on_node with nvidia-smi failure."""
        # Setup mock command outputs
        create_pod_output = ("pod/nvidia-smi-debug-node1 created", "", 0)
        pod_status_output = (json.dumps({"status": {"phase": "Running"}}), "", 0)
        nvidia_smi_output = (
            "NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver.",
            "Make sure that the latest NVIDIA driver is installed and running.",
            1
        )
        delete_pod_output = ("pod/nvidia-smi-debug-node1 deleted", "", 0)
        
        # Set up side_effect to return different outputs for different calls
        mock_run_command.side_effect = [
            create_pod_output,
            pod_status_output,
            nvidia_smi_output,
            delete_pod_output
        ]

        # Patch open to mock file operations
        with patch('builtins.open', mock_open()):
            # Patch json.dump to do nothing
            with patch('json.dump') as mock_json_dump:
                # Run the method
                result = self.validator.validate_nvidia_smi_on_node("node1.example.com")

                # Assertions
                self.assertFalse(result)
                self.assertEqual(self.validator.validation_results["nvidia_smi_node1.example.com"]["status"], "failed")

    @patch.object(GPUValidator, 'validate_oc_connection')
    @patch.object(GPUValidator, 'validate_gpu_operator_installation')
    @patch.object(GPUValidator, 'validate_gpu_operator_pods')
    @patch.object(GPUValidator, 'validate_node_gpu_status')
    @patch.object(GPUValidator, 'validate_gpu_feature_discovery')
    @patch.object(GPUValidator, 'validate_driver_daemonset')
    def test_run_all_validations(self, mock_driver, mock_feature, mock_node, mock_pods, mock_operator, mock_connection):
        """Test run_all_validations method."""
        # Setup mocks
        mock_connection.return_value = True
        mock_operator.return_value = True
        mock_pods.return_value = True
        mock_node.return_value = True
        mock_feature.return_value = True
        mock_driver.return_value = True
        
        # Mock the run_command for get nodes
        with patch.object(self.validator, 'run_command') as mock_run_command:
            # No nodes with GPUs
            mock_run_command.return_value = (json.dumps({"items": []}), "", 0)
            
            # Run the method
            results = self.validator.run_all_validations()
            
            # Assertions
            mock_connection.assert_called_once()
            mock_operator.assert_called_once()
            mock_pods.assert_called_once()
            mock_node.assert_called_once()
            mock_feature.assert_called_once()
            mock_driver.assert_called_once()
            self.assertIsInstance(results, dict)

    @patch.object(GPUValidator, 'run_all_validations')
    def test_print_validation_results(self, mock_run_all_validations):
        """Test print_validation_results method."""
        # Setup mock validation results
        self.validator.validation_results = {
            "test_pass": {
                "status": "passed",
                "message": "Test passed"
            },
            "test_fail": {
                "status": "failed",
                "message": "Test failed"
            },
            "test_warning": {
                "status": "warning",
                "message": "Test warning"
            }
        }
        
        # Redirect stdout to capture printed output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        # Call the method
        self.validator.print_validation_results()
        
        # Reset stdout
        sys.stdout = sys.__stdout__
        
        # Assertions
        output = captured_output.getvalue()
        self.assertIn("PASSED", output)
        self.assertIn("FAILED", output)
        self.assertIn("WARNING", output)
        self.assertIn("test_pass", output)
        self.assertIn("test_fail", output)
        self.assertIn("test_warning", output)

    @patch('gpu_validator.GPUValidator')
    def test_validate_gpu_setup(self, mock_validator_class):
        """Test validate_gpu_setup function."""
        # Setup mock validator
        mock_validator = MagicMock()
        mock_validator.run_all_validations.return_value = {"test": "result"}
        mock_validator_class.return_value = mock_validator
        
        # Call the function
        result = validate_gpu_setup("test-namespace")
        
        # Assertions
        mock_validator_class.assert_called_once_with("test-namespace")
        mock_validator.run_all_validations.assert_called_once()
        mock_validator.print_validation_results.assert_called_once()
        self.assertEqual(result, {"test": "result"})

    @patch('gpu_validator.GPU