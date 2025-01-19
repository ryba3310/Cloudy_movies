# Cloudy movies

Cloudy movies is a 3-tier application consiting of frontend page hosted inside flask, API as serverless cloud function and data tier using MongoDB and cloud bucket storage.

Fronted page is used for interactions with API.

Serverless API fetches data from themoviedb.org and stores document data in MongoDB and image data in stoarge bucket.

MongoDB and storage bucket are used for persistent storage to avoid excessive remote API calls and build movie list.

This reposiroy stores backend and API logic, fronted is build on Minimal-flask repository and avialable at site.justalab.xyz


# TODO


- ✅ Outline of purpose

- ✅️  Create basic API funtionality

- ✅️  Setup MongoDB and storage bucket

- ⚠️  Integrate API layer with storage layer

- ✅️  Find workaround to avoid using AWS NAT Gateway And AWS Elastic IP

- ⚠️  Integrate API layer with storage layer

- ✅️  Setup flask frontend

- ✅️  Setup serverless funtion

- ⚠️  Setup Terraform IaC

- ⚠️  Setup CI/CD pipeline