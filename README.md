# Streamlit as a CAII Application

![The Streamlit logo](docs/images/streamlit-logo.png)

A minimal example of a [Streamlit](https://www.streamlit.io/) application running as a CAII Application.
We display and chart a small dataset with Seaborn.

## Repository Structure

```bash
.
├── cml                     # This folder contains scripts that facilitate the project launch on CAII.
├── docs/images             # Storage for the images in this README.
├── .project-metadata.yaml  # Declarative specification of this project
├── app.py                  # The Streamlit app script.
├── LICENSE                 # This code has an Apache 2.0 License
├── README.md               # This file!
└── requirements.txt        # Python 3 package requirements.
```

## Launching the project on CAII

To launch this project on CAII:
1. Create a CAII cluster in Cloudera AI Control Plane UI. [CAII documentation](https://docs.cloudera.com/machine-learning/cloud/ai-inference/topics/ml-caii-use-caii.html)
2. Navigate to the "Applications" Tab in Cloudera AI Control Plane.
3. Click "Deploy Application" and fill out the fields.

## Using the app

Once the CAII Application has been deployed, you can select it in the Applications List Page and select the link to "Open Application"
This should open a browser window, with a Streamlit application running at a URL
similar to `streamlit.serving-apps.caii-domain.com`.

If everything worked, you should see an application like this:

![An image of the Streamlit application](docs/images/streamlit-amp-screenshot.png)

IMPORTANT: Please read the following before proceeding. Cloudera, Inc. (“Cloudera”) makes available to you this optional software, which may include accelerators for machine learning projects (“AMPs”), Hugging Face Spaces, or AI models, constitutes reference machine learning projects (“Reference Projects”). By configuring and launching this Reference Project, you acknowledge and assume the risk that using Reference Projects may (i) cause third party software, such as third-party large language models, to be downloaded directly into your environment and/or (ii) enable third-party services, such as third-party AI services, and transmission of data and metadata to such third-party services providers. Any such third-party software is not validated or maintained by Cloudera. Any support provided for Reference Projects is at Cloudera’s sole discretion. You agree to comply with any applicable license terms or terms of use, including any third-party license terms, for Reference Projects.

If you do not wish to download and install the third party software packages, do not configure, launch or otherwise use this Reference Project. By configuring, launching or otherwise using the Reference Project, you acknowledge the foregoing statement and agree that Cloudera is not responsible or liable in any way for any third party software packages.
