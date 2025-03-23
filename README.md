![cloudy_movies drawio (1)](https://github.com/user-attachments/assets/0cdb44bf-616c-4ba5-a04e-e4f862b582a4)

# Cloudy movies

Cloudy movies is a 3-tier application consiting of frontend page hosted inside flask, API as serverless cloud function and data tier using MongoDB and cloud bucket storage.

Fronted page is used for interactions with API.

Serverless API fetches data from themoviedb.org and stores document data in MongoDB and image data in stoarge bucket.

MongoDB and storage bucket are used for persistent storage to avoid excessive remote API calls and build movie list.

This reposiroy stores backend and API logic, fronted is build on top of Minimal-flask repository and avialable at site.justalab.xyz


# How to run it

Copy this repository and cd to it

```git clone https://github.com/ryba3310/Cloudy_movies.git && cd cloudy_movies```

Run proxy and NoQL containers

```docker-compose up -d --build```

Create funtion zip wth libraries to upload to AWS Lambda

```mkdir func && pip install -r lambda/requirements.txt -t func && cp lambda/cloudy_movie.py func/lambda_function.py && zip -r func.zip func/*```



# TODO


- ✅ Outline of purpose

- ✅️  Create basic API funtionality

- ✅️  Setup MongoDB and storage bucket

- ✅️  Query TMDB if no results are stored in DB

- ✅️  Store movie thumbnail in S3 storage

- ✅️  Find workaround to avoid using AWS NAT Gateway And AWS Elastic IP

- ✅️  Integrate API layer with storage layer

- ✅️  Setup flask frontend

- ✅️  Finish results pagination

- ⚠️  Update README with instructions

- ✅️  Create AWS lambda deployment script

- ⚠️  Improve search/query code

- ✅️  Fix timeouts on longer/bigger searches

- ✅️  Retrive data from S3

- ✅️  Setup serverless funtion

- ✅️  Refactor the code

- ⚠️  Switch from flask proxy to AWS NAT Gateway and VPC Endpoints

- ⚠️  Setup Terraform IaC

- ⚠️  Setup CI/CD pipeline

- ⚠️  Switch to AWS DocumentDB
