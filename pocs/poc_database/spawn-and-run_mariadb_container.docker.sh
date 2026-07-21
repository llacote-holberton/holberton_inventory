#!/bin/bash

CONTAINER_NAME="hb_inv__db_poc"
if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
    echo "Container already exists."
    docker start "$CONTAINER_NAME"
    exit 0
fi

# Creating a named volume to ease up cleanup
MARIADB_VOLUME_PATH="$(pwd)/data/mariadb"
mkdir -p $MARIADB_VOLUME_PATH
docker volume create \
  --driver local \
  --opt type=none \
  --opt o=bind \
  --opt device="$MARIADB_VOLUME_PATH" \
  hb_inv__db_data

docker run -d \
  --name hb_inv__db_poc \
  -e MARIADB_ROOT_PASSWORD='H0lb3rt0n' \
  -e MARIADB_DATABASE='holberton_inventory' \
  -p 3306:3306 \
  -v hb_inv__db_data:/var/lib/mysql \
  -v "$(pwd)/init:/docker-entrypoint-initdb.d" \
  mariadb:lts

docker ps \
  --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}' \
  > logs__list-of-active-docker-containers_post_start.log
docker logs hb_inv__db_poc > logs__spawned-container-inner-logs.log

# Small IA-generated script to have a confirmation when MariaDB is ready;
# using inner container utility mariadb-admin (which, without arguments, just displays health check)
echo "Waiting for MariaDB..."
until docker exec hb_inv__db_poc mariadb-admin \
    -uroot \
    -pH0lb3rt0n \
    ping --silent >/dev/null 2>&1
do
    sleep 1
done
echo "MariaDB is ready."






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
