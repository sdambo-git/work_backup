import yaml

# Read the YAML file
with open('nv-tools-build.yml', 'r') as file:
    buildconfig = yaml.safe_load(file)

# Extract the Dockerfile content
dockerfile_content = buildconfig['spec']['source']['dockerfile']

# Write it to a Dockerfile
with open('Dockerfile_nvidia_tools', 'w') as dockerfile:
    dockerfile.write(dockerfile_content)

print("Dockerfile extracted successfully!")
