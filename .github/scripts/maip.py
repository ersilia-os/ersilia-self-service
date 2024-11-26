from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import sys
import csv
import os
from time import sleep

# parse arguments
input_file = sys.argv[1]
output_file = sys.argv[2]

# read SMILES from .csv file, assuming one column with header
with open(input_file, "r") as f:
    reader = csv.reader(f)
    next(reader) # skip header
    smiles_list = [r[0] for r in reader]
    print("SMILES LIST: ", smiles_list)
    
# save smiles to a dataframe
smiles = pd.DataFrame(smiles_list, columns=['smiles'])

id_col = np.arange(0, len(smiles) ,1)
id_col = [str(x) for x in id_col ]
smiles.insert(0, column = 'id', value = id_col)

smiles.to_csv('maip.csv', index=False)

url = 'https://www.ebi.ac.uk/chembl/interface_api/delayed_jobs/submit/mmv_job'
file = {'input1': open('maip.csv', 'rb')}
payload = { 'standardise': True,'dl__ignore_cache': False}

session = requests.Session()
while True:
    r = session.post(url, files=file, data = payload)
    print("Status code: ", r.status_code)
    if r.status_code == 200:
        break
    sleep(1)

soup = BeautifulSoup(r.text, features = 'html.parser')
job_id = str(soup.text)

job_id = job_id.split(':')[1].strip().translate({ ord(c): None for c in "\"}" })
print("JOB ID: ", job_id)
while True:
    download_url = 'http://www.ebi.ac.uk/chembl/interface_api/delayed_jobs/outputs/' + job_id + '/predictions.csv'
    download_response = session.get(download_url,allow_redirects=True)
    print("Status code: ", download_response.status_code)
    if download_response.status_code == 200:
        break
    sleep(1)
    
output_file_temp = sys.argv[2]

print("DOWNLOAD RESPONSE: ", download_response.content)
open(output_file_temp , "wb").write(download_response.content)

pred = pd.read_csv(output_file_temp)

# convert model_score to list
outputs = pred['model_score'].tolist()



# write output in a .csv file
with open(output_file, "w") as f:
    writer = csv.writer(f)
    writer.writerow(["model_score"]) # header
    for o in outputs:
        writer.writerow([o])
        

os.remove('maip.csv')
