# First run standard must-gather
oc adm must-gather --dest-dir=./must-gather-data

# Create base directory for must-gather with proper HOME path
BASE_COLLECTION_PATH="${HOME}/must-gather"
mkdir -p "${BASE_COLLECTION_PATH}"

#################################################
# GPU Operator Collection
#################################################
echo "Collecting NVIDIA GPU ClusterPolicy resources..."
GPU_PATH="${BASE_COLLECTION_PATH}/gpu-operator"
mkdir -p "${GPU_PATH}"

POLICIES_PATH="${GPU_PATH}/clusterpolicies"
mkdir -p "${POLICIES_PATH}"

# Get all clusterpolicies
oc get clusterpolicies.nvidia.com -o yaml > "${POLICIES_PATH}/clusterpolicies.yaml" 2>/dev/null || echo "No ClusterPolicies found"

# Get individual clusterpolicies with more details
for policy in $(oc get clusterpolicies.nvidia.com -o custom-columns=NAME:.metadata.name --no-headers 2>/dev/null); do
  echo "Collecting details for ClusterPolicy: ${policy}"
  oc describe clusterpolicy.nvidia.com "${policy}" > "${POLICIES_PATH}/${policy}-describe.txt"
  oc get clusterpolicy.nvidia.com "${policy}" -o yaml > "${POLICIES_PATH}/${policy}.yaml"
done

# Collect related resources
echo "Collecting GPU operator related resources..."
RESOURCES_PATH="${GPU_PATH}/related-resources"
mkdir -p "${RESOURCES_PATH}"

# Get GPU operator pods - try multiple possible labels
NAMESPACE=""
for label in "app=gpu-operator" "app.kubernetes.io/name=gpu-operator" "app.kubernetes.io/part-of=gpu-operator"; do
  NAMESPACE=$(oc get pods --all-namespaces -l "${label}" -o custom-columns=NAMESPACE:.metadata.namespace --no-headers 2>/dev/null | head -n 1)
  if [ -n "${NAMESPACE}" ]; then
    echo "Found GPU operator in namespace: ${NAMESPACE}"
    break
  fi
done

# If namespace found, collect pods and logs
if [ -n "${NAMESPACE}" ]; then
  mkdir -p "${RESOURCES_PATH}/pods"
  mkdir -p "${RESOURCES_PATH}/logs"

  # Get GPU operator pods
  oc get pods -n "${NAMESPACE}" -l app=gpu-operator -o yaml > "${RESOURCES_PATH}/pods/gpu-operator-pods.yaml" 2>/dev/null
  oc get pods -n "${NAMESPACE}" -l app.kubernetes.io/name=gpu-operator -o yaml >> "${RESOURCES_PATH}/pods/gpu-operator-pods.yaml" 2>/dev/null

  # Get logs from GPU operator pods - try multiple possible labels
  for label in "app=gpu-operator" "app.kubernetes.io/name=gpu-operator"; do
    for pod in $(oc get pods -n "${NAMESPACE}" -l "${label}" -o name 2>/dev/null); do
      pod_name=$(echo "${pod}" | cut -d/ -f2)
      echo "Collecting logs for GPU pod: ${pod_name}"
      oc logs "${pod}" -n "${NAMESPACE}" > "${RESOURCES_PATH}/logs/${pod_name}.log"
    done
  done

  # Collect GPU operator ConfigMaps
  mkdir -p "${RESOURCES_PATH}/configmaps"
  oc get configmap -n "${NAMESPACE}" -l app=gpu-operator -o yaml > "${RESOURCES_PATH}/configmaps/gpu-configmaps.yaml" 2>/dev/null

  # Collect GPU operator events
  mkdir -p "${RESOURCES_PATH}/events"
  oc get events -n "${NAMESPACE}" > "${RESOURCES_PATH}/events/gpu-events.txt"
else
  echo "GPU operator namespace not found, continuing with node collection"
fi

# Get GPU nodes information using multiple possible labels
mkdir -p "${RESOURCES_PATH}/nodes"
oc get nodes -o yaml -l feature.node.kubernetes.io/pci-10de.present=true > "${RESOURCES_PATH}/nodes/gpu-nodes.yaml" 2>/dev/null
oc get nodes -o yaml -l nvidia.com/gpu.present=true >> "${RESOURCES_PATH}/nodes/gpu-nodes.yaml" 2>/dev/null

# Get NVIDIA device plugin pods if they exist
NVIDIA_DEVICE_NS=$(oc get pods --all-namespaces -l name=nvidia-device-plugin-daemonset -o custom-columns=NAMESPACE:.metadata.namespace --no-headers 2>/dev/null | head -n 1)
if [ -n "${NVIDIA_DEVICE_NS}" ]; then
  mkdir -p "${RESOURCES_PATH}/device-plugin"
  echo "Found NVIDIA device plugin in namespace: ${NVIDIA_DEVICE_NS}"
  oc get pods -n "${NVIDIA_DEVICE_NS}" -l name=nvidia-device-plugin-daemonset -o yaml > "${RESOURCES_PATH}/device-plugin/device-plugin-pods.yaml"

  # Get logs from device plugin pods
  for pod in $(oc get pods -n "${NVIDIA_DEVICE_NS}" -l name=nvidia-device-plugin-daemonset -o name 2>/dev/null); do
    pod_name=$(echo "${pod}" | cut -d/ -f2)
    echo "Collecting logs for device plugin pod: ${pod_name}"
    oc logs "${pod}" -n "${NVIDIA_DEVICE_NS}" > "${RESOURCES_PATH}/device-plugin/${pod_name}.log"
  done
fi


#################################################
# Node Feature Discovery (NFD) Operator Collection - Revised
#################################################

# First run standard must-gather
oc adm must-gather --dest-dir=./must-gather-data

echo "Collecting NFD operator resources..."
# Create error log file for NFD collection
ERROR_LOG="${BASE_COLLECTION_PATH}/nfd-error.log"
touch "${ERROR_LOG}"
echo "Starting NFD collection at $(date)" > "${ERROR_LOG}"

# First check specifically for openshift-nfd namespace
if oc get namespace openshift-nfd >/dev/null 2>&1; then
  NFD_NAMESPACE="openshift-nfd"
  echo "Found NFD namespace: openshift-nfd"
else
  # Try several known possible namespaces for NFD
  POSSIBLE_NFD_NAMESPACES=("nfd" "openshift-node-feature-discovery" "node-feature-discovery")
  NFD_NAMESPACE=""
  
  # Try finding namespace through known patterns
  for ns in "${POSSIBLE_NFD_NAMESPACES[@]}"; do
    if oc get namespace "${ns}" >/dev/null 2>&1; then
      echo "Found potential NFD namespace: ${ns}"
      NFD_NAMESPACE="${ns}"
      break
    fi
  done
  
  # If still not found, try label-based detection
  if [ -z "${NFD_NAMESPACE}" ]; then
    for label in "app=nfd" "app=node-feature-discovery"; do
      NFD_NAMESPACE=$(oc get pods --all-namespaces -l "${label}" -o custom-columns=NAMESPACE:.metadata.namespace --no-headers 2>/dev/null | head -n 1)
      if [ -n "${NFD_NAMESPACE}" ]; then
        echo "Found NFD operator using label ${label} in namespace: ${NFD_NAMESPACE}"
        break
      fi
    done
  fi
fi

if [ -n "${NFD_NAMESPACE}" ]; then
  echo "Processing NFD resources in namespace: ${NFD_NAMESPACE}"
  
  # Log available API resources for debugging
  echo "Available API resources related to NFD:" >> "${ERROR_LOG}"
  oc api-resources | grep -i feature >> "${ERROR_LOG}" 2>&1
  
  # Create standard must-gather directory structure
  mkdir -p "${BASE_COLLECTION_PATH}/namespaces/${NFD_NAMESPACE}"
  mkdir -p "${BASE_COLLECTION_PATH}/cluster-scoped-resources/nfd.openshift.io"
  
  # Create the specific paths we saw in the diff
  mkdir -p "${BASE_COLLECTION_PATH}/cluster-scoped-resources/nfd.openshift.io/nodefeaturediscoveries"
  
  # Create the required path for NFD operator data
  mkdir -p "${BASE_COLLECTION_PATH}/required/nfd-operator"
  
  echo "Attempting to collect NodeFeatureDiscovery with singular form..." >> "${ERROR_LOG}"
  # Try with the singular form (nodefeaturediscovery)
  if oc get nodefeaturediscovery.nfd.openshift.io -n "${NFD_NAMESPACE}" nfd-instance &>/dev/null; then
    echo "Success: Found resource using singular form (nodefeaturediscovery)" >> "${ERROR_LOG}"
    
    # Save to required path (seen in the diff)
    oc get nodefeaturediscovery.nfd.openshift.io nfd-instance -n "${NFD_NAMESPACE}" -o yaml > "${BASE_COLLECTION_PATH}/required/nfd-operator/nfd-instance.yaml" 2>> "${ERROR_LOG}"
    
    # Also save to standard must-gather path
    oc get nodefeaturediscovery.nfd.openshift.io nfd-instance -n "${NFD_NAMESPACE}" -o yaml > "${BASE_COLLECTION_PATH}/cluster-scoped-resources/nfd.openshift.io/nodefeaturediscoveries/nfd-instance.yaml" 2>> "${ERROR_LOG}"
    
    # Extract worker config data but save as TXT to avoid validation errors
    oc get nodefeaturediscovery.nfd.openshift.io nfd-instance -n "${NFD_NAMESPACE}" -o jsonpath='{.spec.workerConfig.configData}' > "${BASE_COLLECTION_PATH}/required/nfd-operator/worker-config-data.txt" 2>> "${ERROR_LOG}"
  else
    echo "Failed to collect resource using singular form, trying plural..." >> "${ERROR_LOG}"
    
    # Try with the plural form (nodefeatureds)
    if oc get nodefeatureds.nfd.openshift.io -n "${NFD_NAMESPACE}" nfd-instance &>/dev/null; then
      echo "Success: Found resource using plural form (nodefeatureds)" >> "${ERROR_LOG}"
      
      # Save to required path (seen in the diff)
      oc get nodefeatureds.nfd.openshift.io nfd-instance -n "${NFD_NAMESPACE}" -o yaml > "${BASE_COLLECTION_PATH}/required/nfd-operator/nfd-instance.yaml" 2>> "${ERROR_LOG}"
      
      # Also save to standard must-gather path
      oc get nodefeatureds.nfd.openshift.io nfd-instance -n "${NFD_NAMESPACE}" -o yaml > "${BASE_COLLECTION_PATH}/cluster-scoped-resources/nfd.openshift.io/nodefeaturediscoveries/nfd-instance.yaml" 2>> "${ERROR_LOG}"
      
      # Extract worker config data but save as TXT to avoid validation errors
      oc get nodefeatureds.nfd.openshift.io nfd-instance -n "${NFD_NAMESPACE}" -o jsonpath='{.spec.workerConfig.configData}' > "${BASE_COLLECTION_PATH}/required/nfd-operator/worker-config-data.txt" 2>> "${ERROR_LOG}"
    else
      echo "Failed to collect using both singular and plural forms" >> "${ERROR_LOG}"
      
      # Let's try without specifying the API version
      echo "Trying without API group specification..." >> "${ERROR_LOG}"
      oc get -n "${NFD_NAMESPACE}" nfd-instance -o yaml > "${BASE_COLLECTION_PATH}/required/nfd-operator/nfd-instance.yaml" 2>> "${ERROR_LOG}" || echo "Failed to find resource without API group" >> "${ERROR_LOG}"
    fi
  fi
  
  # Collect CRDs
  echo "Collecting NFD-related CRDs..." >> "${ERROR_LOG}"
  mkdir -p "${BASE_COLLECTION_PATH}/cluster-scoped-resources/apiextensions.k8s.io/customresourcedefinitions"
  
  for crd in $(oc get crd | grep -E 'nfd|feature' | awk '{print $1}'); do
    echo "Found CRD: ${crd}" >> "${ERROR_LOG}"
    oc get crd "${crd}" -o yaml > "${BASE_COLLECTION_PATH}/cluster-scoped-resources/apiextensions.k8s.io/customresourcedefinitions/${crd}.yaml" 2>> "${ERROR_LOG}"
  done
  
  # Collect all resources in the NFD namespace
  echo "Collecting all resources in namespace ${NFD_NAMESPACE}..." >> "${ERROR_LOG}"
  mkdir -p "${BASE_COLLECTION_PATH}/namespaces/${NFD_NAMESPACE}/core"
  
  # Get all supported resource types
  for resource in pods deployments daemonsets configmaps services; do
    oc get -n "${NFD_NAMESPACE}" "${resource}" -o yaml > "${BASE_COLLECTION_PATH}/namespaces/${NFD_NAMESPACE}/core/${resource}.yaml" 2>> "${ERROR_LOG}"
  done
  
  # Collect NFD node labels
  echo "Collecting NFD node labels..." >> "${ERROR_LOG}"
  mkdir -p "${BASE_COLLECTION_PATH}/cluster-scoped-resources/core/nodes"
  oc get nodes -o yaml > "${BASE_COLLECTION_PATH}/cluster-scoped-resources/core/nodes/all-nodes.yaml" 2>> "${ERROR_LOG}"
  
  # Extract NFD-specific labels - use .txt extension for non-resource output
  mkdir -p "${BASE_COLLECTION_PATH}/nfd-labels"
  for node in $(oc get nodes -o name); do
    node_name=$(echo "${node}" | cut -d/ -f2)
    echo "Collecting labels for node ${node_name}" >> "${ERROR_LOG}"
    oc get node "${node_name}" -o jsonpath='{.metadata.labels}' | grep -o 'feature.node.kubernetes.io[^"]*' > "${BASE_COLLECTION_PATH}/nfd-labels/${node_name}-nfd-labels.txt" 2>> "${ERROR_LOG}"
  done
  
  # For status information, save as TXT files to avoid validation issues
  mkdir -p "${BASE_COLLECTION_PATH}/required/nfd-operator/status"
  if oc get nodefeaturediscovery.nfd.openshift.io nfd-instance -n "${NFD_NAMESPACE}" &>/dev/null; then
    # Extract status as text file instead of JSON to avoid validation errors
    oc get nodefeaturediscovery.nfd.openshift.io nfd-instance -n "${NFD_NAMESPACE}" -o jsonpath='{.status}' > "${BASE_COLLECTION_PATH}/required/nfd-operator/status/nfd-instance-status.txt" 2>> "${ERROR_LOG}"
    oc get nodefeaturediscovery.nfd.openshift.io nfd-instance -n "${NFD_NAMESPACE}" -o jsonpath='{.status.conditions}' > "${BASE_COLLECTION_PATH}/required/nfd-operator/status/nfd-instance-conditions.txt" 2>> "${ERROR_LOG}"
  elif oc get nodefeatureds.nfd.openshift.io nfd-instance -n "${NFD_NAMESPACE}" &>/dev/null; then
    # Try plural form
    oc get nodefeatureds.nfd.openshift.io nfd-instance -n "${NFD_NAMESPACE}" -o jsonpath='{.status}' > "${BASE_COLLECTION_PATH}/required/nfd-operator/status/nfd-instance-status.txt" 2>> "${ERROR_LOG}"
    oc get nodefeatureds.nfd.openshift.io nfd-instance -n "${NFD_NAMESPACE}" -o jsonpath='{.status.conditions}' > "${BASE_COLLECTION_PATH}/required/nfd-operator/status/nfd-instance-conditions.txt" 2>> "${ERROR_LOG}"
  fi
  
  # Create legacy paths for compatibility
  echo "Creating legacy paths for compatibility..." >> "${ERROR_LOG}"
  mkdir -p "${BASE_COLLECTION_PATH}/nfd-operator/nodefeatureds"
  
  # Try both versions (direct file copy to avoid repeated API calls)
  if [ -f "${BASE_COLLECTION_PATH}/required/nfd-operator/nfd-instance.yaml" ]; then
    cp "${BASE_COLLECTION_PATH}/required/nfd-operator/nfd-instance.yaml" "${BASE_COLLECTION_PATH}/nfd-operator/nodefeatureds/nfd-instance.yaml"
    # Also create the exact file with the name seen in the diff
    cp "${BASE_COLLECTION_PATH}/required/nfd-operator/nfd-instance.yaml" "${BASE_COLLECTION_PATH}/nfd-openshift-io-v1_nodefeaturediscovery_openshift-nfd_nfd-instance"
  fi
  
  echo "NFD operator collection completed. Check ${ERROR_LOG} for any errors."
else
  echo "NFD operator namespace not found. Check ${ERROR_LOG} for details." | tee -a "${ERROR_LOG}"
fi
