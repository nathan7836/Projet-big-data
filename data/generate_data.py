"""
Generate realistic US Health Insurance Marketplace data.
Produces 2 CSV files:
  - plans.csv (Source A - MySQL): Plan info, issuers, network types, states
  - costs.csv (Source B - PostgreSQL): Deductibles, copays, out-of-pocket, benefits
Total: 250,000+ rows
"""

import csv
import random
import uuid
import os

random.seed(42)

US_STATES = [
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
    'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
    'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
    'VA','WA','WV','WI','WY','DC'
]

NETWORK_TYPES = ['HMO', 'PPO', 'EPO', 'POS']
METAL_LEVELS = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Catastrophic']
METAL_WEIGHTS = [30, 35, 20, 10, 5]

ISSUERS = [
    'Blue Cross Blue Shield', 'UnitedHealthcare', 'Aetna', 'Cigna', 'Humana',
    'Kaiser Permanente', 'Molina Healthcare', 'Centene', 'Anthem', 'WellCare',
    'Oscar Health', 'Ambetter', 'CareSource', 'Priority Health', 'Medica',
    'HealthMarkets', 'Friday Health Plans', 'Bright Health', 'Clover Health',
    'Devoted Health', 'Alignment Healthcare', 'Meridian Health Plan',
    'Community Health Plan', 'SelectHealth', 'UPMC Health Plan',
    'Highmark', 'Geisinger Health Plan', 'MVP Health Care', 'EmblemHealth',
    'Oxford Health Plans', 'ConnectiCare', 'HealthFirst', 'MetroPlus',
    'Fidelis Care', 'Excellus BlueCross', 'Capital District Physicians',
    'BlueCross BlueShield of Tennessee', 'Florida Blue', 'Premera Blue Cross',
    'Regence BlueCross BlueShield'
]

PLAN_TYPES = ['Individual', 'Family', 'Small Group']
BENEFIT_CATEGORIES = [
    'Emergency Services', 'Hospitalization', 'Maternity and Newborn Care',
    'Mental Health Services', 'Prescription Drugs', 'Rehabilitative Services',
    'Laboratory Services', 'Preventive Services', 'Pediatric Services',
    'Ambulatory Patient Services'
]

NUM_PLANS = 250000

output_dir = os.path.dirname(os.path.abspath(__file__)) + '/csv'
os.makedirs(output_dir, exist_ok=True)

print(f"Generating {NUM_PLANS} insurance plans...")

plans_file = os.path.join(output_dir, 'plans.csv')
costs_file = os.path.join(output_dir, 'costs.csv')

with open(plans_file, 'w', newline='') as pf, open(costs_file, 'w', newline='') as cf:
    plans_writer = csv.writer(pf)
    costs_writer = csv.writer(cf)

    # Headers
    plans_writer.writerow([
        'PlanID', 'IssuerName', 'IssuerID', 'PlanName', 'PlanType',
        'NetworkType', 'MetalLevel', 'StateCode', 'CountyName',
        'MarketCoverage', 'IsActive', 'PlanYear'
    ])

    costs_writer.writerow([
        'PlanID', 'IndividualDeductible', 'FamilyDeductible',
        'IndividualOutOfPocketMax', 'FamilyOutOfPocketMax',
        'CopayPrimaryCare', 'CopaySpecialist', 'CopayER',
        'CopayGenericDrug', 'CoinsuranceRate', 'HSAEligible',
        'BenefitCategory', 'BenefitCovered', 'QuantitativeLimit',
        'LimitUnit', 'Exclusions'
    ])

    counties_by_state = {}
    for st in US_STATES:
        counties_by_state[st] = [f"{st}_County_{i}" for i in range(1, random.randint(5, 20))]

    for i in range(NUM_PLANS):
        plan_id = f"PL{i+1:08d}"
        state = random.choice(US_STATES)
        county = random.choice(counties_by_state[state])
        issuer = random.choice(ISSUERS)
        issuer_id = f"ISS{abs(hash(issuer + state)) % 100000:05d}"
        network = random.choice(NETWORK_TYPES)
        metal = random.choices(METAL_LEVELS, weights=METAL_WEIGHTS, k=1)[0]
        plan_type = random.choice(PLAN_TYPES)
        plan_year = random.choice([2022, 2023, 2024])
        plan_name = f"{issuer} {metal} {network} {plan_type} {state}"
        market = random.choice(['Individual', 'SHOP'])
        is_active = random.choices([1, 0], weights=[90, 10], k=1)[0]

        plans_writer.writerow([
            plan_id, issuer, issuer_id, plan_name, plan_type,
            network, metal, state, county, market, is_active, plan_year
        ])

        # Cost parameters based on metal level
        base_deductible = {
            'Catastrophic': random.randint(7000, 9000),
            'Bronze': random.randint(4000, 7000),
            'Silver': random.randint(2000, 4500),
            'Gold': random.randint(500, 2000),
            'Platinum': random.randint(0, 500)
        }[metal]

        ind_deductible = base_deductible
        fam_deductible = ind_deductible * 2
        ind_oop_max = ind_deductible + random.randint(1000, 4000)
        fam_oop_max = fam_deductible + random.randint(2000, 6000)

        copay_primary = {
            'Catastrophic': 0, 'Bronze': random.randint(35, 60),
            'Silver': random.randint(25, 45), 'Gold': random.randint(15, 30),
            'Platinum': random.randint(5, 15)
        }[metal]

        copay_specialist = copay_primary + random.randint(10, 30)
        copay_er = random.randint(150, 500)
        copay_generic = random.randint(5, 30)
        coinsurance = round(random.uniform(0.10, 0.50), 2)
        hsa = random.choices([1, 0], weights=[30, 70], k=1)[0]

        benefit = random.choice(BENEFIT_CATEGORIES)
        covered = random.choices([1, 0], weights=[85, 15], k=1)[0]
        quant_limit = random.choice([0, 10, 20, 30, 50, 60, 'Unlimited'])
        limit_unit = random.choice(['Visits', 'Days', 'Treatments', 'N/A'])
        exclusions = random.choice([
            'None', 'Cosmetic Surgery', 'Experimental Treatments',
            'Weight Loss Surgery', 'Infertility Treatment',
            'Long-term Care', 'None', 'None'
        ])

        costs_writer.writerow([
            plan_id, ind_deductible, fam_deductible,
            ind_oop_max, fam_oop_max,
            copay_primary, copay_specialist, copay_er,
            copay_generic, coinsurance, hsa,
            benefit, covered, quant_limit, limit_unit, exclusions
        ])

        if (i + 1) % 50000 == 0:
            print(f"  Generated {i + 1}/{NUM_PLANS} records...")

print(f"Done! Files created:")
print(f"  {plans_file}")
print(f"  {costs_file}")

# Count lines
with open(plans_file) as f:
    plans_count = sum(1 for _ in f) - 1
with open(costs_file) as f:
    costs_count = sum(1 for _ in f) - 1
print(f"  plans.csv: {plans_count} rows")
print(f"  costs.csv: {costs_count} rows")
