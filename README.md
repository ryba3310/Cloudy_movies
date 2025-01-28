![cloudy_movies drawio (1)](https://github.com/user-attachments/assets/0cdb44bf-616c-4ba5-a04e-e4f862b582a4)

# Cloudy movies

Cloudy movies is a 3-tier application consiting of frontend page hosted inside flask, API as serverless cloud function and data tier using MongoDB and cloud bucket storage.

Fronted page is used for interactions with API.

Serverless API fetches data from themoviedb.org and stores document data in MongoDB and image data in stoarge bucket.

MongoDB and storage bucket are used for persistent storage to avoid excessive remote API calls and build movie list.

This reposiroy stores backend and API logic, fronted is build on top of Minimal-flask repository and avialable at site.justalab.xyz


# TODO


- ✅ Outline of purpose

- ✅️  Create basic API funtionality

- ✅️  Setup MongoDB and storage bucket

- ✅️  Query TMDB if no results store in DB

- ✅️  Store movie thumbnail in S3 storage

- ✅️  Find workaround to avoid using AWS NAT Gateway And AWS Elastic IP

- ✅️  Integrate API layer with storage layer

- ✅️  Setup flask frontend

- ✅️  Finish results pagination

- ⚠️  Improve search/query code

- ✅️  Retrive data from S3

- ✅️  Setup serverless funtion

- ⚠️  Setup Terraform IaC

- ⚠️  Setup CI/CD pipeline

- ⚠️  Switch to AWS DocumentDB
