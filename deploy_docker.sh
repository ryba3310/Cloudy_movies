#!/bin/bash
echo "Starting deployment ..."
eval $(ssh-agent)
ssh-add /home/admin/.ssh/cidc.key
cd /home/admin/cloudy_movies
git pull
sudo docker-compose down && \
sudo docker-compose  up -d --build
echo "Deployment complete ..."
