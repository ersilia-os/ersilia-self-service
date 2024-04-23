import requests
import json
import os
from ruamel.yaml import YAML
import argparse

current_directory = os.getcwd()
print("Current working directory:" + current_directory)
# Define command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('url', help='URL of the S3 bucket')
args = parser.parse_args()

# print out the parsed url argument
print("Attempting to fetch the list of models from: " + args.url)

# Fetch JSON file from S3 bucket
response = requests.get(args.url)
print(response.text)
data = response.json()

# write out the data to the console
print(data)

# Load YAML file
yaml = YAML()
with open('.github/ISSUE_TEMPLATE/model-inference-run.yml', 'r') as file:
    yaml_data = yaml.load(file)

print(yaml_data)

# Update dropdown list
dropdown = yaml_data['body'][1]  # Assuming the dropdown is the second item in the 'body' list
dropdown['attributes']['options'] = [item['model_id'] for item in data if 'model_id' in item]  # Extract 'model_id' values
# Write back to the YAML file
with open('.github/ISSUE_TEMPLATE/model-inference-run.yml', 'w') as file:
    yaml.dump(yaml_data, file)

print("Successfully updated the dropdown list in the model-inference-run.yml file")
print(yaml_data)