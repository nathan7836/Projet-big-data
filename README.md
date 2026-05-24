# Projet Big Data - US Health Insurance Marketplace

Pipeline Big Data complet pour l'analyse du marche de l'assurance sante aux Etats-Unis, base sur l'architecture Medallion (Bronze / Silver / Gold).

## Architecture

```
 SOURCES                    BRONZE              SILVER                  GOLD               EXPOSITION
+-----------+          +------------+      +--------------+      +----------------+     +------------+
|  MySQL    |--JDBC--->|            |      |              |      |                |     |  FastAPI   |
| (plans)   |          |   MinIO    |      |  Hive/MinIO  |      |  PostgreSQL    |---->|  REST API  |
+-----------+   Spark  |  (Parquet) | Spark| (Parquet +   | Spark|  (Datamarts)   |     |  + JWT     |
                Feeder |            | Proc.|  Validation  | DM   |                |     +------------+
+-----------+          |  s3a://    |      |  + Window    |      | - Affordability|
| PostgreSQL|--JDBC--->| datalake/  |----->|    Funcs)    |----->| - Market Struct|     +------------+
| (costs)   |          |   raw/     |      |              |      | - Competitive  |---->| Streamlit  |
+-----------+          +------------+      +--------------+      +----------------+     | Dashboard  |
                                                                                        +------------+
  Orchestration: Apache Airflow (DAG quotidien)
```

## Stack technique

| Composant | Technologie | Port |
|-----------|-------------|------|
| Source A - Plans | MySQL 8.0 | 3306 |
| Source B - Couts | PostgreSQL 15 | 5432 |
| Stockage Data Lake | MinIO (S3-compatible) | 9000/9001 |
| Traitement distribue | Apache Spark 3.5 (Master + Worker) | 8080/7077 |
| Metastore | Apache Hive 3.1.3 + PostgreSQL | 9083 |
| Base Gold (Datamarts) | PostgreSQL 15 | 5433 |
| Orchestration | Apache Airflow 2.8.1 | 8082 |
| API REST | FastAPI + JWT | 8000 |
| Visualisation | Streamlit + Plotly | 8501 |
| Conteneurisation | Docker Compose (12 services) | - |

## Donnees

- **250 000+ lignes** generees avec `data/generate_data.py`
- **Source A (MySQL)** : informations sur les plans (assureur, reseau, etat, niveau metal)
- **Source B (PostgreSQL)** : couts et prestations (franchise, copay, OOP max, exclusions)

## Pipeline Medallion

### Bronze (Ingestion - `feeder.py`)
- Lecture JDBC depuis MySQL et PostgreSQL
- Ecriture en Parquet partitionne par date dans MinIO (`s3a://datalake/raw/`)

### Silver (Traitement - `processor.py`)
- **7 regles de validation** :
  1. PlanID unique et non-null
  2. StateCode valide (51 etats US)
  3. Franchise positive et <= OOP max
  4. NetworkType valide (HMO, PPO, EPO, POS)
  5. IssuerName non-vide
  6. MetalLevel valide (Bronze/Silver/Gold/Platinum/Catastrophic)
  7. PlanYear >= 2020
- **Jointure** plans + costs sur PlanID
- **Fonctions de fenetre** : rang par franchise, moyenne par etat, % par type de reseau, score d'accessibilite
- Ecriture partitionnee dans MinIO + enregistrement Hive

### Gold (Datamarts - `datamart.py`)
- **Datamart 1 - Accessibilite Financiere** : franchise moyenne, OOP max par etat et niveau metal
- **Datamart 2 - Structure de l'Offre** : repartition HMO/PPO, diversite par assureur et etat
- **Datamart 3 - Competitivite des Plans** : copays, taux de coassurance, exclusions, eligibilite HSA
- Ecriture JDBC vers PostgreSQL Gold

## API REST

- `POST /auth/login` : authentification JWT (admin/admin123 ou analyst/analyst123)
- `GET /datamarts/affordability` : DM1 pagine avec filtres (state, metal_level)
- `GET /datamarts/market-structure` : DM2 pagine avec filtres
- `GET /datamarts/competitiveness` : DM3 pagine avec filtres
- `GET /datamarts/affordability/stats` : statistiques agregees
- `GET /health` : verification de sante
- Documentation Swagger : http://localhost:8000/docs

## Dashboard (6 graphiques interactifs)

1. **Carte** : franchise individuelle moyenne par etat (choroplethe)
2. **Barres groupees** : franchise vs OOP max par niveau metal
3. **Donut** : repartition des plans par type de reseau
4. **Barres horizontales** : top 15 assureurs par nombre de plans
5. **Barres groupees** : copays moyens par niveau metal
6. **Heatmap** : exclusions par etat et categorie de prestation

## Lancement rapide

```bash
# 1. Lancer le script de demo complet
./run_demo.sh
```

Le script automatise :
- Generation des donnees (250k lignes)
- Telechargement des JARs JDBC
- Demarrage de tous les conteneurs Docker
- Attente de la disponibilite des services
- Execution du pipeline Spark (Bronze -> Silver -> Gold)
- Verification des resultats

## Lancement manuel

```bash
# 1. Generer les donnees
python3 data/generate_data.py

# 2. Telecharger les JARs JDBC
bash spark/download_jars.sh

# 3. Demarrer l'infrastructure
docker compose up -d --build

# 4. Executer le pipeline Spark manuellement
JARS="/opt/spark-jars/mysql-connector-j.jar,/opt/spark-jars/postgresql.jar,/opt/spark-jars/hadoop-aws-3.3.4.jar,/opt/spark-jars/aws-java-sdk-bundle-1.12.262.jar"

# Bronze
docker exec spark-master /opt/spark/bin/spark-submit \
  --jars $JARS --master spark://spark-master:7077 \
  /opt/spark-jobs/feeder.py \
  --mysql-host mysql-source --mysql-port 3306 --mysql-db insurance_plans \
  --pg-host postgres-source --pg-port 5432 --pg-db insurance_costs \
  --output s3a://datalake/raw --date $(date +%Y-%m-%d)

# Silver
docker exec spark-master /opt/spark/bin/spark-submit \
  --jars $JARS --master spark://spark-master:7077 \
  /opt/spark-jobs/processor.py \
  --input s3a://datalake/raw --output s3a://datalake/silver --date $(date +%Y-%m-%d)

# Gold
docker exec spark-master /opt/spark/bin/spark-submit \
  --jars $JARS --master spark://spark-master:7077 \
  /opt/spark-jobs/datamart.py \
  --input s3a://datalake/silver \
  --pg-host postgres-gold --pg-port 5432 --pg-db datamarts \
  --pg-user api --pg-password apipass --date $(date +%Y-%m-%d)
```

## Arret

```bash
docker compose down -v
```

## Structure du projet

```
.
├── README.md
├── docker-compose.yml          # 12 services Docker
├── run_demo.sh                 # Script de demo automatise
├── data/
│   ├── generate_data.py        # Generateur de donnees (250k lignes)
│   └── csv/                    # Fichiers CSV generes
├── docker/
│   ├── mysql/init/             # Schema + chargement MySQL
│   ├── postgres/init/          # Schema + chargement PostgreSQL
│   └── hive/                   # Configuration Hive Metastore
├── spark/
│   ├── download_jars.sh        # Telechargement JARs JDBC
│   ├── jars/                   # JARs JDBC (MySQL, PostgreSQL, Hadoop-AWS)
│   └── jobs/
│       ├── feeder.py           # Bronze: Sources -> MinIO (Parquet)
│       ├── processor.py        # Silver: Validation + Jointures + Window
│       └── datamart.py         # Gold: 3 Datamarts -> PostgreSQL
├── airflow/
│   └── dags/
│       └── insurance_pipeline.py  # DAG: Feeder >> Processor >> Datamart
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py                 # FastAPI + JWT + pagination
└── visualization/
    ├── Dockerfile
    ├── requirements.txt
    └── app.py                  # Streamlit + 6 graphiques Plotly
```
