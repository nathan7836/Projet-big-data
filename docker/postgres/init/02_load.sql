\COPY costs FROM '/var/lib/postgresql/costs.csv' WITH (FORMAT csv, HEADER true);

SELECT COUNT(*) AS total_costs FROM costs;
