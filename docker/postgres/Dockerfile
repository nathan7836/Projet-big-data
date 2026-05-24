FROM postgres:15
COPY init/01_schema.sql /docker-entrypoint-initdb.d/01_schema.sql
COPY init/02_load.sql /docker-entrypoint-initdb.d/02_load.sql
COPY init/costs.csv /var/lib/postgresql/costs.csv
