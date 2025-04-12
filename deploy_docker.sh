#!/bin/bash
echo "Starting deployment ..."
eval $(ssh-agent)
ssh-add $HOME/.ssh/cidc.key
cd $HOME/cloudy_movies
git pull
sudo docker-compose down && \
sudo docker-compose  up -d --build
echo "Deployment complete ..."
