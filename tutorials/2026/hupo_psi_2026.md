# HUPO PSI 2026 tutorial

This tutorial walks you through the complete workflow for submitting mass spectrometry metabolomics data to [MetaboLights](https://www.ebi.ac.uk/metabolights/) using the [mzTab-M](https://github.com/HUPO-PSI/mzTab) format.

In this tutorial, we will follow these steps:

1. Setting up your MetaboLights account & obtaining an API token
2. Installing the mzTab-M to MetaboLights ISA-TAB (mztabm2mtbls) library
3. Creating a provisional study in MetaboLights
4. Preparing local mzTab-M and raw data files
5. Converting mzTab-M to ISA-TAB format with mztabm2mtbls-cli
6. Uploading the metadata & raw data files to MetaboLights
7. Reviewing the submission in the MetaboLights web interface

## 1. Setting up your MetaboLights account & obtaining API token

All programmatic interactions with MetaboLights — creating studies, uploading files, and triggering validation — require an API token for authentication. Follow the steps below to create your free account and retrieve your personal token.

- Set up the [MetaboLights Submission Account](https://www.ebi.ac.uk/metabolights/newAccount)
- Confirm your account by clicking the link in the confirmation email
- Log in at [MetaboLights](https://www.ebi.ac.uk/metabolights/login)
- Click on 'My Account' and copy your [API token](https://www.ebi.ac.uk/metabolights/myAccount)
- Open a terminal and set the API token as an environment variable

```bash
export MTBLS_API_TOKEN=<MTBLS API TOKEN>
echo $MTBLS_API_TOKEN
# your API token should be printed in the terminal
```

## 2. Setting up mzTab-M to MetaboLights ISA-TAB (mztabm2mtbls) library

The `mztabm2mtbls` library is a command-line tool that converts mzTab-M files into the ISA-Tab format required by MetaboLights, and validates the result against MetaboLights submission rules. To get started, you need two prerequisites: the [uv](https://docs.astral.sh/uv/) Python package manager (for dependency management) and [git](https://git-scm.com/) (to clone the repository).

- Install uv python package manager and git (if not already installed):

```bash
# install python package manager uv
curl -LsSf https://releases.astral.sh/github/uv/releases/download/0.11.8/uv-installer.sh | sh

# add $HOME/.local/bin to your PATH, either restart your shell or run
# export PATH=$HOME/.local/bin:$PATH

# install git (https://git-scm.com/install)
# Mac users may install git using Homebrew:
# brew install git

uv --version
# should print something like:
#uv 0.11.8 (0e961dd9a 2026-04-27 aarch64-apple-darwin)

git --version
# should print something like:
# git version 2.50.1 (Apple Git-155)

```
- Clone and install mztabm2mtbls locally:

```bash

# You may choose to work in a different directory for this tutorial.
# In that case, change the directory (or cd) command accordingly
# (Linux or Mac)
cd ~/tutorials/hupo-psi-2026

git clone https://github.com/EBI-Metabolights/mztabm2mtbls.git
cd mztabm2mtbls
uv python pin 3.13
uv sync
source .venv/bin/activate

# On Windows, you may need to run:
# .venv\Scripts\Activate.ps1

mztabm2mtbls-cli
# Usage: mztabm2mtbls-cli [OPTIONS] COMMAND [ARGS]...

# Options:
#   --version   Show the version and exit.
#   -h, --help  Show this message and exit.

# Commands:
#   convert-to-isatab         Convert mzTab-M file to MetaboLights ISATAB...
```

## 3. Create a provisional study in MetaboLights

Before uploading any data, you need to create a provisional study entry in MetaboLights. This reserves a unique study identifier (e.g. `REQ20260505219305`) that acts as a placeholder for your submission. The provisional ID is used in all subsequent steps — converting metadata, uploading files, and triggering validation — so make sure to save it as an environment variable (MTBLS_PROVISIONAL_STUDY_ID).

After creating a provisional study, you will receive an email from MetaboLights with the subject "MetaboLights Temporary Submission initiated". You can find the provisional study ID and FTP upload details in the email.

Notes:

1- Only 2 provisional studies allowed per user. If you already have 2 provisional studies, you may use it.
2- Only one provisional study can be submitted in five minutes interval.

```bash
mztabm2mtbls-cli create-provisional-study --user-api-token $MTBLS_API_TOKEN
# Example output:
# Studies created: REQ20260505219305

export MTBLS_PROVISIONAL_STUDY_ID=<CREATED_PROVISIONAL_STUDY_ID>
echo $MTBLS_PROVISIONAL_STUDY_ID
# Example output
#REQ20260505219305
```

## 4. Prepare local mzTab-M file and raw data files for the tutorial
Some study level metadata is required while submitting a new study to MetaboLights:

- Contact: `mztabm2mtbls` converts mzTab-M contacts to ISA-TAB investigation file contacts. First contact is set as Principal Investigator, others as Authors. If needed you can update this information in mzTab-M file before conversion.
- Study Variable Groups: At least one study variable group (with study variable values) must be defined in the mzTab-M file.
- Protocols and protocol parameters: Following protocols and protocol parameters must be defined in the mzTab-M file for MS-based studies:
    - Sample collection protocol: No specific parameter required.
    - Extraction: Post Extraction, Derivatization
    - Mass spectrometry: Scan polarity, Scan m/z range, Instrument, Ion source, Mass analyzer
    - Data transformation: No specific parameter required.
    - Metabolite identification: No specific parameter required.

If there is no specific paramter values for protocol parameters, you can leave the protocol parameter value empty.

Example mzTab-M file `test/data/LCS-00001-1/LCS-00001-1.mztabm` contains these required metadata fields.


- Create a test data directory

```bash
mkdir my-test-data
cp test/data/LCS-00001-1/LCS-00001-1.mztabm my-test-data/
cp -r test/data/LCS-00001-1/files my-test-data/
```

- Open `my-test-data/LCS-00001-1.mztabm` with your text editor and update the contact information with your information. Replace the placeholder values shown below with your own:

```bash
# Placeholder contact information in the original file:
MTD	contact[1]-name	Test contact
MTD	contact[1]-email	test@email.addess
MTD	contact[1]-affiliation	Test affiliation

# Replace with your contact information.
# It is tsv file, so make sure to keep the tab separated format.
# For example:
MTD	contact[1]-name	Ozgur Yurekten
MTD	contact[1]-email	ozgury@ebi.ac.uk
MTD	contact[1]-affiliation	EMBL European Bioinformatics Institute

```

## 5. Convert mzTab-M to ISA-TAB format with mztabm2mtbls-cli

- Use `convert-to-isatab` command to create the ISA-TAB files from your mzTab-M file and data files.

```bash
mztabm2mtbls-cli convert-to-isatab \
    --mtbls-provisional-study-id $MTBLS_PROVISIONAL_STUDY_ID \
    --mztabm-file-path my-test-data/LCS-00001-1.mztabm \
    --data-files-path my-test-data/files \
    --target-metadata-files-path my-test-data/$MTBLS_PROVISIONAL_STUDY_ID \
    --temp-folder my-test-data/validation
```

- Review the generated ISA-TAB files.
```bash
ls my-test-data/$MTBLS_PROVISIONAL_STUDY_ID

```

- Review the generated validation report on `my-test-data/validation` folder. You can find the details of validation issues (errors and warnings) in the report. If there are any errors, you need to fix them in your mzTab-M file and regenerate the ISA-TAB files. Once you fix the issues, you can regenerate the ISA-TAB files by running the `convert-to-isatab` command again.

If there is no error in the validation report, you can upload the metadata and raw data files to MetaboLights.

## 6. Upload the Metadata & RawData files to MetaboLights

Once your ISA-Tab files and raw data are ready, they need to be uploaded to MetaboLights in two separate steps: first the metadata (ISA-Tab) files, then the raw data files via FTP. You can use any FTP client (e.g. FileZilla, Cyberduck, or the ftp client in your terminal) to upload the raw data files. The ftp upload details can be found in the email received after creating the provisional study.

After both uploads are complete, you can trigger a server-side remote validation to confirm that everything is consistent and meets MetaboLights submission requirements.

- Upload the ISA-TAB files to MetaboLights using the `upload-metadata-files` command.

```bash
uv run mztabm2mtbls-cli upload-metadata-files \
    --mtbls-api-token $MTBLS_API_TOKEN \
    --mtbls-provisional-study-id $MTBLS_PROVISIONAL_STUDY_ID \
    --metadata-files-path my-test-data/$MTBLS_PROVISIONAL_STUDY_ID
```

- Upload Raw data files to MetaboLights using the `upload-data-files` command. If your data file upload process fails, you can try again.

```bash
mztabm2mtbls-cli upload-data-files \
    --mtbls-api-token $MTBLS_API_TOKEN \
    --mtbls-provisional-study-id $MTBLS_PROVISIONAL_STUDY_ID \
    --data-files-path my-test-data/files

# If you did not receive an email with ftp credentials, 
# you can get them using the `get-ftp-credentials` command. 
# mztabm2mtbls-cli get-ftp-credentials \
#     --mtbls-api-token $MTBLS_API_TOKEN \
#     --mtbls-provisional-study-id $MTBLS_PROVISIONAL_STUDY_ID
# It will print the ftp server url, remote folder directory, ftp username and ftp password.

```

```bash
mztabm2mtbls-cli get-ftp-credentials \
    --mtbls-api-token $MTBLS_API_TOKEN \
    --mtbls-provisional-study-id $MTBLS_PROVISIONAL_STUDY_ID
```


- Run remote validation using the `remote-validation` command. Review the validation results.

```bash
mztabm2mtbls-cli remote-validation \
    --mtbls-api-token $MTBLS_API_TOKEN \
    --mtbls-provisional-study-id $MTBLS_PROVISIONAL_STUDY_ID \
    --validation-result-file-path my-test-data/validation/remote-validation.json
```

## 7. Review the submission in the MetaboLights web interface

- Open the MetaboLights [editor](https://www.ebi.ac.uk/metabolights/editor/console) in your browser (login if required)
- Click your provisional study by clicking 'Study overview' button.
- Review the study details, including the submitted metadata and raw data files.
