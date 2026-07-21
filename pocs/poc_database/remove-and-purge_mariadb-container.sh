#!/bin/bash

CONTAINER_NAME="hb_inv__db_poc"
echo "Purging container $CONTAINER_NAME and related volumes"

docker stop $CONTAINER_NAME
docker rm -f $CONTAINER_NAME

docker volume rm hb_inv__db_data
sudo rm -rf $(pwd)/data/mariadb
