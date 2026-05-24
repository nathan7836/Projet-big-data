-- ============================================================
-- REQUETES SQL POUR LA VIDEO DE DEMO
-- ============================================================
-- Connexion PostgreSQL Gold :
--   docker exec -it postgres-gold psql -U api -d datamarts
-- ============================================================


-- ============================================================
-- PARTIE 1 : VERIFIER LES SOURCES (dans le terminal Docker)
-- ============================================================

-- 1a) MySQL Source - Plans d'assurance
-- Commande : docker exec mysql-source mysql -u root -prootpass insurance_plans

-- SELECT COUNT(*) AS total_plans FROM plans;
-- SELECT MetalLevel, COUNT(*) AS nb FROM plans GROUP BY MetalLevel ORDER BY nb DESC;
-- SELECT * FROM plans LIMIT 5;

-- 1b) PostgreSQL Source - Couts
-- Commande : docker exec postgres-source psql -U spark -d insurance_costs

-- SELECT COUNT(*) AS total_costs FROM costs;
-- SELECT BenefitCategory, COUNT(*) AS nb FROM costs GROUP BY BenefitCategory ORDER BY nb DESC LIMIT 5;


-- ============================================================
-- PARTIE 2 : COUCHE GOLD - DATAMARTS
-- Connexion : psql -U api -d datamarts -h localhost -p 5433
-- ============================================================

-- Vue d'ensemble des 3 datamarts
SELECT 'datamart_affordability' AS datamart, COUNT(*) AS lignes FROM datamart_affordability
UNION ALL
SELECT 'datamart_market_structure', COUNT(*) FROM datamart_market_structure
UNION ALL
SELECT 'datamart_competitiveness', COUNT(*) FROM datamart_competitiveness;


-- ─── DATAMART 1 : Accessibilite Financiere ──────────────────

-- Q1 : Franchise moyenne par niveau de plan (la question cle du projet)
SELECT
    "MetalLevel",
    COUNT(*) AS nb_etats,
    ROUND(AVG(avg_individual_deductible), 2) AS franchise_moy,
    ROUND(AVG(avg_individual_oop_max), 2) AS oop_max_moy,
    ROUND(AVG(avg_affordability_score)::numeric, 2) AS score_accessibilite
FROM datamart_affordability
GROUP BY "MetalLevel"
ORDER BY franchise_moy DESC;

-- Q2 : Top 5 etats les PLUS chers
SELECT
    "StateCode",
    ROUND(AVG(avg_individual_deductible), 2) AS franchise_moy,
    ROUND(AVG(avg_individual_oop_max), 2) AS oop_max_moy,
    SUM(num_plans) AS total_plans
FROM datamart_affordability
GROUP BY "StateCode"
ORDER BY franchise_moy DESC
LIMIT 5;

-- Q3 : Top 5 etats les MOINS chers
SELECT
    "StateCode",
    ROUND(AVG(avg_individual_deductible), 2) AS franchise_moy,
    ROUND(AVG(avg_individual_oop_max), 2) AS oop_max_moy,
    SUM(num_plans) AS total_plans
FROM datamart_affordability
GROUP BY "StateCode"
ORDER BY franchise_moy ASC
LIMIT 5;

-- Q4 : Ecart entre deductible min et max par metal level
SELECT
    "MetalLevel",
    ROUND(MIN(min_deductible), 2) AS deductible_min,
    ROUND(MAX(max_deductible), 2) AS deductible_max,
    ROUND(MAX(max_deductible) - MIN(min_deductible), 2) AS ecart
FROM datamart_affordability
GROUP BY "MetalLevel"
ORDER BY ecart DESC;


-- ─── DATAMART 2 : Structure du Marche ───────────────────────

-- Q5 : Repartition des plans par type de reseau (avec %)
SELECT
    "NetworkType",
    SUM(num_plans) AS total_plans,
    ROUND(SUM(num_plans) * 100.0 / (SELECT SUM(num_plans) FROM datamart_market_structure), 2) AS pourcentage
FROM datamart_market_structure
GROUP BY "NetworkType"
ORDER BY total_plans DESC;

-- Q6 : Top 10 assureurs
SELECT
    "IssuerName",
    SUM(num_plans) AS total_plans,
    COUNT(DISTINCT "StateCode") AS nb_etats,
    ROUND(AVG(metal_diversity), 1) AS diversite_metal
FROM datamart_market_structure
GROUP BY "IssuerName"
ORDER BY total_plans DESC
LIMIT 10;

-- Q7 : Etats avec le plus d'assureurs (concurrence)
SELECT
    "StateCode",
    COUNT(DISTINCT "IssuerName") AS nb_assureurs,
    SUM(num_plans) AS total_plans,
    ROUND(AVG(avg_deductible), 2) AS franchise_moy
FROM datamart_market_structure
GROUP BY "StateCode"
ORDER BY nb_assureurs DESC
LIMIT 10;

-- Q8 : Couverture par type de reseau
SELECT
    "NetworkType",
    COUNT(DISTINCT "StateCode") AS nb_etats,
    SUM(county_coverage) AS total_counties,
    ROUND(AVG(avg_deductible), 2) AS franchise_moy
FROM datamart_market_structure
GROUP BY "NetworkType"
ORDER BY total_counties DESC;


-- ─── DATAMART 3 : Competitivite ─────────────────────────────

-- Q9 : Copays moyens par niveau de plan
SELECT
    "MetalLevel",
    ROUND(AVG(avg_copay_primary), 2) AS copay_generaliste,
    ROUND(AVG(avg_copay_specialist), 2) AS copay_specialiste,
    ROUND(AVG(avg_copay_er), 2) AS copay_urgences,
    ROUND(AVG(avg_copay_generic), 2) AS copay_medicament,
    ROUND(AVG(avg_coinsurance_rate), 4) AS taux_coassurance
FROM datamart_competitiveness
GROUP BY "MetalLevel"
ORDER BY copay_generaliste DESC;

-- Q10 : Categories les plus exclues
SELECT
    "BenefitCategory",
    SUM(num_excluded) AS total_exclusions,
    SUM(num_plans) AS total_plans,
    ROUND(SUM(num_excluded) * 100.0 / NULLIF(SUM(num_plans), 0), 2) AS taux_exclusion_pct
FROM datamart_competitiveness
GROUP BY "BenefitCategory"
ORDER BY total_exclusions DESC;

-- Q11 : Eligibilite HSA par metal et reseau
SELECT
    "MetalLevel",
    "NetworkType",
    SUM(num_hsa_eligible) AS hsa_eligible,
    SUM(num_plans) AS total,
    ROUND(SUM(num_hsa_eligible) * 100.0 / NULLIF(SUM(num_plans), 0), 2) AS pct_hsa
FROM datamart_competitiveness
GROUP BY "MetalLevel", "NetworkType"
ORDER BY pct_hsa DESC
LIMIT 10;

-- Q12 : LA question : HMO vs PPO
SELECT
    "NetworkType",
    ROUND(AVG(avg_copay_primary), 2) AS copay_generaliste,
    ROUND(AVG(avg_copay_specialist), 2) AS copay_specialiste,
    ROUND(AVG(avg_copay_er), 2) AS copay_urgences,
    ROUND(AVG(avg_coinsurance_rate), 4) AS taux_coassurance,
    SUM(num_excluded) AS total_exclusions
FROM datamart_competitiveness
WHERE "NetworkType" IN ('HMO', 'PPO')
GROUP BY "NetworkType";
