FROM mysql:8.0
COPY init/01_schema.sql /docker-entrypoint-initdb.d/01_schema.sql
COPY init/plans.csv /var/lib/mysql-files/plans.csv
