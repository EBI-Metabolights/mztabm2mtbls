

## Create mztab2-m json file from mztab file
mzTab files should exist on working directory

```bash
docker pull quay.io/biocontainers/jmztab-m:1.0.6--hdfd78af_1
# Example of how to run the container to convert lipidomics-example.mzTab file on current working directory to lipidomics-example.mzTab.json file
docker run --rm -v "${PWD}":/home/data:rw --workdir /home/data quay.io/biocontainers/jmztab-m:1.0.6--hdfd78af_1 jmztab-m -c "/home/data/lipidomics-example.mzTab" --toJson -o "/home/data/validation.txt"
```

## Run convertor for example file

```bash
python3 mztabm2mtbls/converter.py
```

# outputs
Converted ISA tab files will bu on output folder.