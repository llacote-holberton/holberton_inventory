#!/bin/bash

CONTAINER_NAME="hb_inv__db_poc"
if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
    echo "Container already exists."
    docker start "$CONTAINER_NAME"
    exit 0
fi

docker run -d \
  --name hb_inv__db_poc \
  -e MARIADB_ROOT_PASSWORD='H0lb3rt0n' \
  -e MARIADB_DATABASE='holberton_inventory' \
  -p 3306:3306 \
  -v "$(pwd)/data/mariadb/:/var/lib/mysql" \
  -v "$(pwd)/init:/docker-entrypoint-initdb.d" \
  mariadb:lts

docker ps \
  --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}' \
  > logs__list-of-active-docker-containers_post_start.log
docker logs hb_inv__db_poc > logs__spawned-container-inner-logs.log

# COMMENTED VERSION
# docker run -d \
# "Custom name" for that container
#  --name hb_inv__db_poc \
# Environment variables*
# (FIXME how to read them from a .env?? OR HOW to trigger docker run from a Python script??)
# WARNING: MYSQL_* environment variables DEPRECATED, use MARIADB_* instead!!!
# -e MYSQL_ROOT_PASSWORD=H0lb3rt0n \
#  -e MYSQL_DATABASE=holberton_inventory \
# Port redirection (host:container)
#  -p 3306:3306 \
# Persistant volume: path on host:path_in_container
#  -v ./data/mariadb/:/var/lib/mysql \
# Name of the "base container" to use (usually grabbed from community repository if not local copy already)
#  mariadb:lts
