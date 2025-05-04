import subprocess

# Run the OpenShift command to get nodes with labels
try:
    data = subprocess.check_output(["oc", "get", "nodes", "--show-labels"]).decode("utf-8")
except subprocess.CalledProcessError as e:
    print("Error executing oc command:", e)
    data = ""

# Split the output on commas and join with newlines
formatted_output = "\n".join(data.split(","))

print(formatted_output)

