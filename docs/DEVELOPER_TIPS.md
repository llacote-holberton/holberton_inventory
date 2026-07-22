# Developer Tips

Here you will find small sections related to ways of trying out specific parts of the app.

# MariaDB container

To run, go to `backoffice` folder then run `docker compose -f hbntory_bo_docker-compose.yml up -d`
Then you can use `docker exec -it hbntory-stock-db-service mariadb -u root -p` with relevant password (default `H0lb3rt0n`)
Once inside the mariadb CLI tool...
- type `USE holberton_inventory;` to "plug" into the database
- then type `SHOW TABLES;` to list all tables.
- and/or type `SELECT * FROM <tablename>` (replace <tablename> with desired table name) to see all content of a specific table.

To just stop the service run `docker compose -f hbntory_bo_docker-compose.yml down`
If you want to stop AND remove containers (including database data!) add option `-v` (`down -v`)
