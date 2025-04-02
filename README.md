# Conversion of mzTab-m to ISA-Tab MetaboLights

This repository contains a Python library to convert mzTab-m files to ISA-Tab files for MetaboLights submission.
Due to the differences in the respective formats, the conversion is not straightforward. The library is designed to handle the conversion of mzTab-m files to ISA-Tab files for MetaboLights submission. Some information that is currently not supported by the ISA-Tab format is converted into comments, where possible. The library is designed to be extensible, so that additional information can be converted in the future.

## Installation

This library uses poetry for dependency management. Please check the [Poetry documentation](https://python-poetry.org/docs/) for installation instructions.
To install the dependencies, run the following command:

```bash
poetry install
```

To activate the virtual environment, run the following command:

```bash
poetry shell
```

## Usage

At the moment, this library uses the JSON representation of the mzTab-m file. The JSON representation can be generated using the jmztab-m tool. The easiest way to generate the JSON representation is to use the Docker container provided by BioContainers.

### Create mztab2-m json file from mztab file

Please ensure that mzTab-m files exist in the working directory:

```bash
docker pull quay.io/biocontainers/jmztab-m:1.0.6--hdfd78af_1
# Example of how to run the container to convert lipidomics-example.mzTab file on current working directory to lipidomics-example.mzTab.json file
docker run --rm -v "${PWD}":/home/data:rw --workdir /home/data quay.io/biocontainers/jmztab-m:1.0.6--hdfd78af_1 jmztab-m -c "/home/data/lipidomics-example.mzTab" --toJson -o "/home/data/validation.txt"
```

The container will accept an mzTab-M file with the `-c` flag and output a JSON file with the `--toJson` flag. The JSON file will be created in the same directory as the input file. The `-o` flag can be used to specify the output file name for the validation results. This will run a default validation on the mzTab-M file, without semantic validation. 

You can also run the conversion with semantic validation of the mzTab-M file activated as follows, supplying a mapping xml file with the `-s` flag:

```bash
docker run --rm -v "${PWD}":/home/data:rw --workdir /home/data quay.io/biocontainers/jmztab-m:1.0.6--hdfd78af_1 jmztab-m -c "/home/data/lipidomics-example.mzTab" --toJson -o "/home/data/validation.txt" -s /home/data/mappingFile.xml
```

Mapping file examples can be found in the mztab-m repository: https://github.com/HUPO-PSI/mzTab/blob/master/specification_document-releases/2_0-Metabolomics-Release 

Please note that for submission to MetaboLights, the mzTab-M file must comply with the minimal profile for MetaboLights. The semantic validation mapping file for the minimal profile can be found in the mztab-m repository.

TODO: Add link to the minimal profile mapping file.

### Workflow overview

1. Create an mzTab-m file with your tool / library of choice.
2. Convert the mzTab-m file to a JSON file using the jmztab-m tool or the docker container.
3. Use the converter.py script to convert the JSON file to an ISA-Tab file (mztabm2mtbls).
4. Validate the ISA-Tab file using the metabolights_utils package.
5. Submit the ISA-Tab files to MetaboLights as a new study.
6. Sync and validate the submission.
7. Success!

```mermaid
    
graph TD
    A[Create mzTab-m file]
    B[mzTab-M Tab Separated File]
    C[mzTab-M JSON]
    D[MetaboLights ISA-Tab]
    E[Submission]
    G[RAW Files]
    H[DERIVED Files]
    I[Study]
    J[Study in Curation]
    A --> B
    B -- validate --> B
    B -- convert with jmzTab-M --> C
    C -- convert with mztabm2mtbls --> D
    D -- validate (local) --> D
    D -- Create Study (MetaboLights Utils) --> I
    E -- Sync and validate --> E 
    E -- Refine --> E
    I -- Prepare --> E
    G -- Prepare --> E
    H -- Prepare --> E
    E -- Check file integrity & Update Study Status--> J

```

### Run converter for example file

```bash
python3 mztabm2mtbls/converter.py --input-file submission_validation_test/MTBLS263/MTBLS263.mztab --mtbls_accession_number MTBLS100001
```

### Run converter without remote validation

Install following requirements before running local validation

- Download the latest version of MetaboLights validation bundle on local folders from https://github.com/EBI-Metabolights/mtbls-validation/raw/main/bundle/bundle.tar.gz
- Download OPA agent https://www.openpolicyagent.org/docs/latest/#1-download-opa

```bash
python3 commands/validate_study.py --mtbls_provisional_study_id MTBLS263 --base_study_path submission_validation_test/ --mtbls_remote_validation False --mztabm_mapping_file submission_validation_test/MTBLS263/mzTab_2_0-M_mapping.xml --mztabm_validation_level Error --mtbls_validation_bundle_path bundle.tar.gz --opa_executable_path opa
```

### Run converter with remote validation

```bash
python3 commands/validate_study.py --mtbls_api_token MTBLS_API_TOKEN_FROM_YOUR_PROFILE --mtbls_provisional_study_id MTBLS263 --base_study_path submission_validation_test/ --mtbls_remote_validation True
```

### Run converter with mapping file

```bash
python3 commands/validate_study.py --mtbls_api_token MTBLS_API_TOKEN_FROM_YOUR_PROFILE --mtbls_provisional_study_id MTBLS263 --base_study_path submission_validation_test/ --mtbls_remote_validation False --mztabm_mapping_file submission_validation_test/mzTab_2_0-M_mapping.xml
```

### Setting the validation level for the mzTab-M validation

Use the `--mztabm_validation_level` parameter to set the validation level for the mzTab-M validation. The default value is `Info`, if the argument is not provided. The possible values are `Error`, `Warning`, and `Info`. If set to `Info`, any info, warning or error level validation messages will lead to a failure of the validation. If set to `Warning`, only warning and error level validation messages will lead to a failure of the validation. If set to `Error`, only error level validation messages will lead to a failure of the validation. Generally, it is recommended to set the validation level to `Warning` to ensure that the mzTab-M file is at least compliant with the MetaboLights minimal profile. However, using `Info` will provide more detailed information about potential improvements of the mzTab-M file metadata. Please note that these levels apply to both the basic validation performed by the jmztab-m tool and the semantic validation performed when an [Mapping file](https://github.com/HUPO-PSI/mzTab/blob/master/specification_document-releases/2_0-Metabolomics-Release/mzTab_2_0-M_mapping.xml) is provided with the `--mztabm_mapping_file` parameter.

```bash
python3 commands/validate_study.py --mtbls_api_token d5487ecf-3c13-438f-ba10-a21daa0baea3 --mtbls_provisional_study_id MTBLS263 --base_study_path submission_validation_test/ --mtbls_remote_validation True --mztabm_mapping_file submission_validation_test/MTBLS263/mzTab_2_0-M_mapping.xml --mztabm_validation_level Error
```

# Conversion, Validation and Upload Process

Converted ISA tab files will be in the output folder.
The script will generate different validation files in the output folder. 
The first validation file will be the validation of the mzTab-m JSON file. If this validation stage passes without warnings or errors, the script will proceed to the conversion of the JSON file to ISA-Tab. The second validation file will be the validation of the ISA-Tab file against the MetaboLights validation REST API. If this validation stage passes without warnings or errors, the script will proceed to the submission of the ISA-Tab files to MetaboLights.
In a final step, raw and derived files will be uploaded to the MetaboLights FTP server.

## Structuring mzTab-M files for conversion

MetaboLights requires a specific structure for mzTab-M files to be converted correctly. This requires specific metadata to be present in the mzTab-M file. In contrast to MetaboLights study, that can have multiple assays, mzTab-M files are expected to contain only one assay, corresponding to the application of one analytical method to a set of samples. Please note that the term "assay" is used differently in the context of mzTab-M files, where it refers to the material derived from a sample used for measurement with a mass spectrometry workflow. The MS workflow may contain multiple steps, e.g. chromatography.