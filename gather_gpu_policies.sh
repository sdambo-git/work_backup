#!/bin/bash
# First run standard must-gather
oc adm must-gather --dest-dir=./must-gather-data

# Create directory for GPU data
mkdir -p ./must-gather-data/gpu-operator/clusterpolicies

# Collect ClusterPolicy resources
oc get clusterpolicies.nvidia.com -o yaml > ./must-gather-data/gpu-operator/clusterpolicies/all-policies.yaml

# Get individual ClusterPolicies
for policy in $(oc get clusterpolicies.nvidia.com -o custom-columns=NAME:.metadata.name --no-headers); do
  oc get clusterpolicy.nvidia.com ${policy} -o yaml > ./must-gather-data/gpu-operator/clusterpolicies/${policy}.yaml
done

# Collect GPU operator logs
namespace=$(oc get pods --all-namespaces -l app=gpu-operator -o custom-columns=NAMESPACE:.metadata.namespace --no-headers | head -n 1)
mkdir -p ./must-gather-data/gpu-operator/logs
for pod in $(oc get pods -n ${namespace} -l app=gpu-operator -o name); do
  pod_name=$(echo ${pod} | cut -d/ -f2)
  oc logs ${pod} -n ${namespace} > ./must-gather-data/gpu-operator/logs/${pod_name}.log
done
