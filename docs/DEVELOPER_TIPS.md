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

# Setting up isolated environment to run app

Ensure you have Python installed from your system's package manager first. Minimum version 3.11, recommended 3.14 or later.
It will come with its own built-in "python package manager" ("pip")

Then create a "local Python virtual environment" to avoid any impact elsewhere on your system.
`python -m venv .venv` ("Python, please create from within current folder, a subfolder representing a local environment, named .env ")/
And activate it with `source .venv/bin/activate`
Now you can install all prerequisites for Python app to run if you want to try it "locally" (`ipp install -r requirements`)

# Used ports

## Internal ports (listening ports inside service containers)
Backoffice (API + UI): 8000
Product MCP Server: 8001
Internal API: 8002
AI Service: 8003
Client web: 8080
