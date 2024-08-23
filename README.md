# Conversion of mzTab-m to ISA-Tab MetaboLights

This repository contains a Python library to convert mzTab-m files to ISA-Tab files for MetaboLights submission.
Due to the differences in the respective formats, the conversion is not straightforward. The library is designed to handle the conversion of mzTab-m files to ISA-Tab files for MetaboLights submission. Some information that is currently not supported by the ISA-Tab format is converted into comments, where possible. The library is designed to be extensible, so that additional information can be converted in the future.

## Installation

This library uses poetry for dependency management. Please check the [Poetry documentation](https://python-poetry.org/docs/) for installation instructions.
To install the dependencies, run the following command:

```bash
poetry install
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

### Run converter for example file

```bash
python3 mztabm2mtbls/converter.py
```

# outputs
Converted ISA tab files will bu on output folder.