#!/bin/bash

S3_BUCKET='cloudy-movies'
FUNCTION_NAME='cloudy_movies'

#Create S3 bucket
aws s3api create-bucket --no-cli-pager --bucket "$S3_BUCKET"

# Create function zip to upload
[ -d func ] || mkdir func && pip install -r lambda/requirements.txt -t func && cp lambda/cloudy_movies.py func/lambda_function.py && (cd func && zip -r ../func.zip ./*)

#Upload function zip to AWS S3
aws s3api put-object --no-cli-pager --bucket "$S3_BUCKET" --key func.zip --body func.zip

#Pull func.zip from S3 to AWS Lambda
aws lambda update-function-code --no-cli-pager --function-name "$FUNCTION_NAME" --s3-bucket "$S3_BUCKET" --s3-key func.zip

#Start your own frontend or deploy Minimal-Flask repository:
#cd && git clone https://github.com/ryba3310/Minimal_flask.git && cd Minimal_flask && docker-compose up -d --build
