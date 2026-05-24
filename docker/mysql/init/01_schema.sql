-- Source A: Plan information (MySQL)
CREATE DATABASE IF NOT EXISTS insurance_plans;
USE insurance_plans;

CREATE TABLE plans (
    PlanID VARCHAR(20) PRIMARY KEY,
    IssuerName VARCHAR(200) NOT NULL,
    IssuerID VARCHAR(20) NOT NULL,
    PlanName VARCHAR(500),
    PlanType VARCHAR(50),
    NetworkType VARCHAR(10),
    MetalLevel VARCHAR(20),
    StateCode VARCHAR(5),
    CountyName VARCHAR(100),
    MarketCoverage VARCHAR(50),
    IsActive TINYINT DEFAULT 1,
    PlanYear INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Index for performance
CREATE INDEX idx_plans_state ON plans(StateCode);
CREATE INDEX idx_plans_issuer ON plans(IssuerName);
CREATE INDEX idx_plans_network ON plans(NetworkType);
CREATE INDEX idx_plans_metal ON plans(MetalLevel);
