#!/bin/bash

#Create S3 bucket
aws s3api create-bucket --bucket cloudy_movies

# Create function zip to upload
mkdir func && pip install -r lambda/requirements.txt -t func && cp lambda/cloudy_movie.py func/lambda_function.py && zip -r func.zip func/*

#Upload function zip to AWS S3
aws s3api put-object --bucket cloudy-movies  --key func.zip --body func.zip

#Pull func.zip from S3 to AWS Lambda
aws lambda update-function-code --function-name cloudy_movies --s3-bucket cloudy-movies --s3-key func.zip

#Start your own frontend with query string in URL or deploy Minimal-Flask repository:
cd && git clone https://github.com/ryba3310/Minimal_flask.git && cd Minimal_flask && docker-compose up -d --build


