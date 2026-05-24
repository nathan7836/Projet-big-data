#!/bin/bash
# Load plans.csv into MySQL
echo "Loading plans data into MySQL..."
mysql -u root -prootpass insurance_plans -e "
LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/plans.csv'
INTO TABLE plans
FIELDS TERMINATED BY ','
ENCLOSED BY '\"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(PlanID, IssuerName, IssuerID, PlanName, PlanType, NetworkType, MetalLevel, StateCode, CountyName, MarketCoverage, IsActive, PlanYear);
"
echo "Plans loaded: $(mysql -u root -prootpass insurance_plans -N -e 'SELECT COUNT(*) FROM plans;') rows"
