-- Source B: Cost and benefits information (PostgreSQL)

CREATE TABLE costs (
    PlanID VARCHAR(20) PRIMARY KEY,
    IndividualDeductible NUMERIC(10,2),
    FamilyDeductible NUMERIC(10,2),
    IndividualOutOfPocketMax NUMERIC(10,2),
    FamilyOutOfPocketMax NUMERIC(10,2),
    CopayPrimaryCare NUMERIC(10,2),
    CopaySpecialist NUMERIC(10,2),
    CopayER NUMERIC(10,2),
    CopayGenericDrug NUMERIC(10,2),
    CoinsuranceRate NUMERIC(5,2),
    HSAEligible INTEGER DEFAULT 0,
    BenefitCategory VARCHAR(100),
    BenefitCovered INTEGER DEFAULT 1,
    QuantitativeLimit VARCHAR(20),
    LimitUnit VARCHAR(50),
    Exclusions VARCHAR(200)
);

CREATE INDEX idx_costs_planid ON costs(PlanID);
