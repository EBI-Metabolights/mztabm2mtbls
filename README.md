

```
docker run --rm -v "${PWD}":/home/data:rw quay.io/biocontainers/jmztab-m:1.0.6--hdfd78af_1 jmztab-m -c "/home/data/lipidomics-example.mzTab" --toJson -o "/home/data/validation.txt"
```