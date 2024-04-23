import requests
import json
import os
from ruamel.yaml import YAML
import argparse

current_directory = os.getcwd()

# Define command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('url', help='URL of the S3 bucket')
args = parser.parse_args()

# print out the parsed url argument
print("Attempting to fetch the list of models from: " + args.url)

# Fetch JSON file from S3 bucket
response = requests.get(args.url)
data = response.json()

# Load YAML file
yaml = YAML()
with open('.github/ISSUE_TEMPLATE/model-inference-run.yml', 'r') as file:
    yaml_data = yaml.load(file)

# Update dropdown list
dropdown = yaml_data['body'][1]  # Assuming the dropdown is the second item in the 'body' list
dropdown['attributes']['options'] = ["{} - {}".format(item['Title'], item['Identifier']) for item in data if 'Identifier' in item and 'Title' in item and item['Status'] == 'Ready']

# Sort the dropdown list
dropdown['attributes']['options'] = sorted(dropdown['attributes']['options'])

# Write back to the YAML file
with open('.github/ISSUE_TEMPLATE/model-inference-run.yml', 'w') as file:
    yaml.dump(yaml_data, file)

print("Successfully updated the dropdown list in the model-inference-run.yml file")
print(yaml_data)
