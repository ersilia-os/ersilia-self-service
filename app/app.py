# Imports
import os
import requests
import zipfile
import time
import streamlit as st
from io import BytesIO
import pandas as pd
from dotenv import load_dotenv
from github import Github

st.set_page_config(layout="wide", page_title="Ersilia Self Service")

# Load environment variables
load_dotenv()
GITHUB_API_KEY = os.getenv("GITHUB_PAT")
REPO_NAME = "ersilia-os/ersilia-self-service"
MODELS_METADATA_URL = "https://ersilia-model-hub.s3.eu-central-1.amazonaws.com/models.json"
ISSUE_LABEL = "model-inference-run"
TARGET_MESSAGE = "We have successfully completed your model inference run"
DOWNLOAD_MESSAGE = "You can download your results"

EXAMPLE_INPUT = [
    "COc1ccc2c(NC(=O)Nc3cccc(C(F)(F)F)n3)ccnc2c1",
    "O=C(O)c1ccccc1NC(=O)N1CCC(c2ccccc2C(F)(F)F)CC1",
    "Cc1ccc(N2CCN(Cc3nc4ccccc4[nH]3)CC2)cc1C"
]


# Function to download models.json
@st.cache_data
def load_models_metadata():
    response = requests.get(MODELS_METADATA_URL)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to load models metadata.")
        return {}

# Function to create a GitHub issue with a label
def create_github_issue(title, body, labels=[ISSUE_LABEL]):
    g = Github(GITHUB_API_KEY)
    repo = g.get_repo(REPO_NAME)
    issue = repo.create_issue(title=title, body=body, labels=labels)
    return issue

# Wait for issue to complete
def wait_for_comment(issue, target_message=TARGET_MESSAGE):
    with st.spinner("Waiting for model inference run to complete. This will take a while. Please be patient... You can monitor the [GitHub Actions workflow](https://github.com/ersilia-os/ersilia-self-service/actions)."):
        while True:
            comments = issue.get_comments()
            for comment in comments:
                if target_message in comment.body:
                    st.success("Model inference run completed successfully!")
                    return comment
            time.sleep(5)

# Download generated file
def download_generated_file(issue_number):
    g = Github(GITHUB_API_KEY)
    repo = g.get_repo(REPO_NAME)
    issue = repo.get_issue(number=issue_number)
    comments = issue.get_comments()
    download_url = None
    for comment in comments:
        if DOWNLOAD_MESSAGE in comment.body:
            download_url = comment.body.split(DOWNLOAD_MESSAGE + " [here](")[1].split(")")[0]
            st.toast("Downloading artifact from {0}".format(download_url))
            df = download_artifact(download_url)
            st.write(df)
    return df

# Download artifact     
def download_artifact(download_url):
    token = GITHUB_API_KEY
    artifact_id = download_url.split("/")[-1]
    repo = "ersilia-os/ersilia-self-service"
    url = f"https://api.github.com/repos/{repo}/actions/artifacts/{artifact_id}/zip"
    st.toast("Artifact can be found in {0}".format(url))
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        file_list = z.namelist()
        csv_file = file_list[0]
        with z.open(csv_file) as f:
            df = pd.read_csv(f)
            return df


# Load models metadata
models_metadata = load_models_metadata()

# Side bar layout
st.sidebar.title("About Ersilia")
st.sidebar.markdown("The [Ersilia Open Source Initiative](www.ersilia.io) is a tech **nonprofit organization** aimed at supporting research **scientists in the Global South** with **AI/ML tools for drug discovery and infectious disease research**.")
st.sidebar.markdown("The current Ersilia Self Service tool was **developed by a team of GitHub for Social Good** volunteers.")

# Main app layout
st.title(":rocket: Ersilia Self Service")
st.markdown("This app runs [Ersilia Model Hub](https://github.com/ersilia-os/ersilia) predictions online using GitHub Actions. The app is just a wrapper for the [Ersilia Self Service](https://github.com/ersilia-os/ersilia-self-service) repository.")
st.warning("The ultimate goal of Ersilia is to offer a low-latency cloud-based solution for users to run models online. This is just a proof of concept and a provisional solution to cover the urgent needs of our current users. Expect high latency.")

select_options = [(model["Identifier"], model["Slug"], model["Title"]) for model in models_metadata]
select_options = sorted(select_options, key=lambda x: x[0])
select_options = [x for x in select_options if not x[0].startswith("eos0")]
select_options = ["{0} / {1} : {2}".format(x[0], x[1], x[2]) for x in select_options]
default_option = "eos2gth / maip-malaria-surrogate : MAIP distillation: antimalarial potential prediction"
selected_model = st.selectbox(options=select_options, label="Select a model", index=select_options.index(default_option))
if selected_model is not None:
    model_id = selected_model.split(" / ")[0]
    st.header("Write an input for model [{0}](https://github.com/ersilia-os/{0})".format(model_id))
    input_text = st.text_area(label="Each input is one line. A maximum of 100 lines are permitted", value="\n".join(EXAMPLE_INPUT), height=200)
    if input_text is None:
        pass
    else:
        input_text = input_text.split("\n")
        input_list = [x.strip() for x in input_text]
        input_list = [x for x in input_list if x != ""]
        if len(input_text) == 0:
            st.info("Input at least one item")
        elif len(input_text) > 100:
            st.error("A maximum of 100 lines is permitted")
        else:
            st.success("Your input has {0} items".format(len(input_list)))
            issue_title = "Model Inference Run: {0}".format(selected_model.split(" / ")[1].split(" : ")[0])
            model_title = selected_model.split(" : ")[1].strip()
            if st.button("Run predictions!"):
                issue_body = ""
                issue_body += "### Model\n"
                issue_body += "{0} - {1}\n".format(model_title, model_id)
                issue_body += "### Molecules\n"
                issue_body += "\n".join(input_list)
                issue_labels = [ISSUE_LABEL]
                issue = create_github_issue(issue_title, issue_body, labels=issue_labels)
                issue_number = int(issue.html_url.split("/")[-1])
                st.write("Issue created: [#{0}]({0})".format(issue_number, issue.html_url))
                wait_for_comment(issue)
                df = download_generated_file(issue_number)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="Download data as CSV",
                    data=csv_data,
                    file_name="ersilia_self_service_issue_{0}.csv".format(issue_number),
                    mime="text/csv"
                )

