#!/bin/bash

source .renv/bin/activate
source .env

# check that MTBLS_STUDY is set
if [ -z "$MTBLS_STUDY" ]; then
  echo -e "MTBLS_STUDY is not set. Please set it in the .env file"
  exit 1
fi

echo -e "Using MTBLS Study ID: $MTBLS_STUDY"
echo -e "Storing output in: $MTBLS_OUTPUT_DIR"
mkdir $MTBLS_OUTPUT_DIR
mkdir -p "$MTBLS_CREDENTIALS_DIR"
mtbls submission login --api_token $MTBLS_API_TOKEN --ftp_user $MTBLS_FTP_USER --ftp_user_password $MTBLS_FTP_PASSWORD --ftp_server_url $MTBLS_FTP_URL --credentials_file_path $MTBLS_CREDENTIALS_DIR/$MTBLS_CREDENTIALS_FILE
if [ $? -eq 0 ]; then
  echo -e "Login successful"
else
  echo -e "Login failed"
  exit 1
fi

mtbls submission download $MTBLS_STUDY -p $MTBLS_OUTPUT_DIR

if [ $? -eq 0 ]; then
  echo -e "Download successful"
else
  echo -e "Download failed"
  exit 1
fi

# Test conversion and validation of mzTab to MTBLS format
# array of mzTab files in test/data
mztab_files=(test/data/MTBLS263.mztab.json)
# test/data/singaporean-plasma-site2.mzTab test/data/lipidomics-example.mzTab.json)

# loop through the array of mzTab files
for mztab_file in "${mztab_files[@]}"; do
    echo "Testing conversion and validation of mzTab to MTBLS format for file: $mztab_file"
    python3 mztabm2mtbls/converter.py --input-file "$mztab_file" --output_dir "$MTBLS_OUTPUT_DIR" --mtbls_accession_number $MTBLS_STUDY
    if [ $? -eq 0 ]; then
      echo -e "Conversion successful"
    else
      echo -e "Conversion failed"
      exit 1
    fi
    echo "Validating the converted file with the MTBLS API"
    mtbls submission validate -c "$MTBLS_CREDENTIALS_DIR/$MTBLS_CREDENTIALS_FILE" -v "$MTBLS_OUTPUT_DIR/mtbls-validation.txt" $MTBLS_STUDY
done

