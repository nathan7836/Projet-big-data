#!/usr/bin/env python3
"""Genere le PDF du livrable du projet Big Data."""

from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "Projet Big Data - US Health Insurance Marketplace", align="L")
            self.cell(0, 8, f"Page {self.page_no()}/{{nb}}", align="R", new_x="LMARGIN", new_y="NEXT")
            self.line(10, 16, 200, 16)
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "ESGI - Projet Big Data 2025-2026", align="C")

    def chapter_title(self, title, level=1):
        if level == 1:
            self.set_font("Helvetica", "B", 16)
            self.set_text_color(25, 60, 120)
            self.ln(6)
            self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(25, 60, 120)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)
        elif level == 2:
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(40, 80, 140)
            self.ln(4)
            self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
            self.ln(2)
        elif level == 3:
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(60, 60, 60)
            self.ln(2)
            self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
            self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.set_x(10)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def bullet(self, text, bold_prefix=""):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.set_x(10)
        if bold_prefix:
            full = "  - " + bold_prefix + text
        else:
            full = "  - " + text
        self.multi_cell(0, 5.5, full)

    def table(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [self.epw / len(headers)] * len(headers)
        # Header
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(25, 60, 120)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()
        # Rows
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        fill = False
        for row in rows:
            if self.get_y() > 265:
                self.add_page()
            if fill:
                self.set_fill_color(240, 245, 255)
            else:
                self.set_fill_color(255, 255, 255)
            for i, val in enumerate(row):
                self.cell(col_widths[i], 6, str(val), border=1, fill=True, align="C" if i > 0 else "L")
            self.ln()
            fill = not fill
        self.ln(2)

    def code_block(self, text):
        self.set_font("Courier", "", 8)
        self.set_fill_color(245, 245, 245)
        self.set_text_color(40, 40, 40)
        self.set_draw_color(200, 200, 200)
        x = self.get_x()
        y = self.get_y()
        lines = text.strip().split("\n")
        h = len(lines) * 4.5 + 4
        if y + h > 270:
            self.add_page()
            y = self.get_y()
        self.rect(x, y, self.epw, h)
        self.set_xy(x + 2, y + 2)
        for line in lines:
            self.cell(0, 4.5, line[:100], new_x="LMARGIN", new_y="NEXT")
            self.set_x(x + 2)
        self.set_xy(10, y + h + 2)
        self.set_font("Helvetica", "", 10)


pdf = PDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)

# ================================================================
# PAGE DE GARDE
# ================================================================
pdf.add_page()
pdf.ln(30)
pdf.set_font("Helvetica", "B", 28)
pdf.set_text_color(25, 60, 120)
pdf.cell(0, 15, "Projet Big Data", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(4)
pdf.set_font("Helvetica", "", 18)
pdf.set_text_color(60, 60, 60)
pdf.cell(0, 12, "US Health Insurance Marketplace", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(2)
pdf.set_font("Helvetica", "I", 14)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 10, "Pipeline Medallion (Bronze / Silver / Gold)", align="C", new_x="LMARGIN", new_y="NEXT")

pdf.ln(20)
pdf.set_draw_color(25, 60, 120)
pdf.line(60, pdf.get_y(), 150, pdf.get_y())
pdf.ln(20)

pdf.set_font("Helvetica", "", 12)
pdf.set_text_color(50, 50, 50)
info = [
    ("Realise par", "Nathan LAMTARA et Killian NGOG"),
    ("Matiere", "Big Data"),
    ("Annee", "2025 - 2026"),
    ("Technologies", "Spark, Docker, MinIO, PostgreSQL, FastAPI, Streamlit"),
    ("Volume de donnees", "250 000 lignes"),
]
for label, value in info:
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(55, 8, label + " :", align="R")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "  " + value, new_x="LMARGIN", new_y="NEXT")

pdf.ln(30)
pdf.set_font("Helvetica", "I", 10)
pdf.set_text_color(130, 130, 130)
pdf.cell(0, 8, "Document de livrable", align="C")

# ================================================================
# TABLE DES MATIERES
# ================================================================
pdf.add_page()
pdf.chapter_title("Table des matieres")
pdf.set_font("Helvetica", "", 11)
pdf.set_text_color(30, 30, 30)
toc = [
    ("1.", "Presentation du projet", 3),
    ("2.", "Architecture technique", 4),
    ("3.", "Stack technique et services", 5),
    ("4.", "Donnees", 6),
    ("5.", "Pipeline Medallion", 7),
    ("  5.1", "Couche Bronze - Ingestion", 7),
    ("  5.2", "Couche Silver - Traitement", 8),
    ("  5.3", "Couche Gold - Datamarts", 9),
    ("6.", "API REST (FastAPI + JWT)", 11),
    ("7.", "Dashboard Streamlit", 12),
    ("8.", "Orchestration Airflow", 13),
    ("9.", "Deploiement Docker", 14),
    ("10.", "Guide d'execution", 15),
]
for num, title, page in toc:
    pdf.cell(12, 7, num)
    pdf.cell(140, 7, title)
    pdf.cell(0, 7, str(page), align="R", new_x="LMARGIN", new_y="NEXT")
pdf.ln(4)

# ================================================================
# 1. PRESENTATION
# ================================================================
pdf.add_page()
pdf.chapter_title("1. Presentation du projet")
pdf.body_text(
    "Ce projet implemente un pipeline Big Data complet pour l'analyse du marche "
    "de l'assurance sante aux Etats-Unis. Il s'appuie sur l'architecture Medallion "
    "(Bronze / Silver / Gold) pour structurer le flux de donnees depuis les sources "
    "brutes jusqu'aux datamarts analytiques."
)
pdf.body_text(
    "L'objectif est de repondre a trois questions metier fondamentales :"
)
pdf.bullet("Comment varie l'accessibilite financiere des plans selon les etats et niveaux ?", "Question 1 : ")
pdf.bullet("Quelle est la structure du marche en termes de reseaux de soins et d'assureurs ?", "Question 2 : ")
pdf.bullet("Comment se comparent les plans en termes de copays, exclusions et couverture ?", "Question 3 : ")
pdf.ln(2)
pdf.body_text(
    "Le pipeline traite 250 000 lignes de donnees a travers 12 services Docker, "
    "avec un traitement distribue via Apache Spark, un stockage intermediaire dans MinIO "
    "(compatible S3), et une exposition via une API REST securisee et un dashboard interactif."
)

# ================================================================
# 2. ARCHITECTURE
# ================================================================
pdf.add_page()
pdf.chapter_title("2. Architecture technique")
pdf.body_text(
    "L'architecture suit le modele Medallion, organise en trois couches de qualite "
    "croissante des donnees :"
)
pdf.code_block(
    " SOURCES                BRONZE             SILVER                GOLD              EXPOSITION\n"
    "+-----------+      +------------+     +--------------+    +----------------+    +------------+\n"
    "| MySQL     |----->|            |     |              |    |                |    |  FastAPI   |\n"
    "| (plans)   | JDBC |   MinIO    |     | MinIO/Hive   |    |  PostgreSQL    |--->|  REST+JWT  |\n"
    "+-----------+      |  (Parquet) | Spark| (Validation  | DM |  (Datamarts)   |    +------------+\n"
    "+-----------+      |  s3a://    |---->|  + Jointures  |--->|                |    +------------+\n"
    "| PostgreSQL|----->| datalake/  |     |  + Window)    |    | - Affordability|    | Streamlit  |\n"
    "| (costs)   | JDBC |   raw/     |     |              |    | - Market Struct|--->| Dashboard  |\n"
    "+-----------+      +------------+     +--------------+    | - Competitive  |    +------------+\n"
    "                                                          +----------------+\n"
    "   Orchestration : Apache Airflow (DAG quotidien)"
)

pdf.body_text(
    "Le flux de donnees est le suivant :"
)
pdf.bullet("Les sources MySQL et PostgreSQL sont lues via JDBC par Spark (Feeder).", "Bronze : ")
pdf.bullet("Les donnees brutes sont validees, jointes et enrichies (Processor).", "Silver : ")
pdf.bullet("Trois datamarts sont construits et ecrits dans PostgreSQL Gold (Datamart).", "Gold : ")
pdf.bullet("Les datamarts sont exposes via une API REST FastAPI avec JWT et un dashboard Streamlit.", "Exposition : ")

# ================================================================
# 3. STACK
# ================================================================
pdf.add_page()
pdf.chapter_title("3. Stack technique et services")
pdf.table(
    ["Composant", "Technologie", "Port"],
    [
        ["Source A - Plans", "MySQL 8.0", "3306"],
        ["Source B - Couts", "PostgreSQL 15", "5432"],
        ["Data Lake", "MinIO (S3-compatible)", "9000/9001"],
        ["Traitement distribue", "Apache Spark 3.5", "8080/7077"],
        ["Metastore", "Apache Hive 3.1.3", "9083"],
        ["Base Gold (Datamarts)", "PostgreSQL 15", "5433"],
        ["Orchestration", "Apache Airflow 2.8.1", "8082"],
        ["API REST", "FastAPI + JWT", "8000"],
        ["Visualisation", "Streamlit + Plotly", "8501"],
        ["Conteneurisation", "Docker Compose (12 services)", "-"],
    ],
    col_widths=[55, 80, 55],
)

pdf.chapter_title("Justification des choix", level=2)
pdf.bullet("Choisi pour le traitement distribue, les jointures complexes et les fonctions de fenetre sur de gros volumes.", "Spark : ")
pdf.bullet("Compatible S3, leger, auto-heberge. Remplace HDFS dans un contexte conteneurise.", "MinIO : ")
pdf.bullet("Stockage colonnes, compression, partitionnement natif. Ideal pour le data lake.", "Parquet : ")
pdf.bullet("Base relationnelle performante pour les datamarts finaux et les requetes analytiques.", "PostgreSQL : ")
pdf.bullet("Framework Python asynchrone, documentation Swagger automatique, validation Pydantic.", "FastAPI : ")
pdf.bullet("Token stateless, pas de session serveur, standard industriel pour les API REST.", "JWT : ")
pdf.bullet("Prototypage rapide de dashboards interactifs en Python.", "Streamlit : ")

# ================================================================
# 4. DONNEES
# ================================================================
pdf.add_page()
pdf.chapter_title("4. Donnees")
pdf.body_text(
    "Les donnees sont generees par le script data/generate_data.py qui produit "
    "250 000 lignes reparties sur deux fichiers CSV :"
)
pdf.chapter_title("Source A - Plans (MySQL)", level=2)
pdf.table(
    ["Colonne", "Type", "Description"],
    [
        ["PlanID", "VARCHAR", "Identifiant unique du plan"],
        ["IssuerName", "VARCHAR", "Nom de l'assureur"],
        ["IssuerID", "VARCHAR", "Identifiant de l'assureur"],
        ["PlanName", "VARCHAR", "Nom commercial du plan"],
        ["PlanType", "VARCHAR", "Type de plan"],
        ["NetworkType", "VARCHAR", "HMO, PPO, EPO ou POS"],
        ["MetalLevel", "VARCHAR", "Bronze, Silver, Gold, Platinum, Catastrophic"],
        ["StateCode", "CHAR(2)", "Code etat US (51 etats + DC)"],
        ["CountyName", "VARCHAR", "Nom du comte"],
        ["MarketCoverage", "VARCHAR", "Type de marche"],
        ["IsActive", "BOOLEAN", "Plan actif ou non"],
        ["PlanYear", "INT", "Annee du plan"],
    ],
    col_widths=[40, 30, 120],
)

pdf.chapter_title("Source B - Couts (PostgreSQL)", level=2)
pdf.table(
    ["Colonne", "Type", "Description"],
    [
        ["PlanID", "VARCHAR", "Cle de jointure avec Source A"],
        ["IndividualDeductible", "DECIMAL", "Franchise individuelle ($)"],
        ["FamilyDeductible", "DECIMAL", "Franchise familiale ($)"],
        ["IndividualOutOfPocketMax", "DECIMAL", "Maximum a charge individuel ($)"],
        ["FamilyOutOfPocketMax", "DECIMAL", "Maximum a charge familial ($)"],
        ["CopayPrimaryCare", "DECIMAL", "Copay soins primaires ($)"],
        ["CopaySpecialist", "DECIMAL", "Copay specialiste ($)"],
        ["CopayER", "DECIMAL", "Copay urgences ($)"],
        ["CopayGenericDrug", "DECIMAL", "Copay medicament generique ($)"],
        ["CoinsuranceRate", "DECIMAL", "Taux de coassurance (0-1)"],
        ["HSAEligible", "BOOLEAN", "Eligible HSA"],
        ["BenefitCategory", "VARCHAR", "Categorie de prestation"],
        ["BenefitCovered", "BOOLEAN", "Prestation couverte"],
        ["Exclusions", "VARCHAR", "Exclusions de couverture"],
    ],
    col_widths=[50, 25, 115],
)

# ================================================================
# 5. PIPELINE MEDALLION
# ================================================================
pdf.add_page()
pdf.chapter_title("5. Pipeline Medallion")

# 5.1 Bronze
pdf.chapter_title("5.1 Couche Bronze - Ingestion (feeder.py)", level=2)
pdf.body_text(
    "Le Feeder lit les deux sources via JDBC (Spark DataFrame API) et ecrit "
    "les donnees brutes en format Parquet dans MinIO, partitionnees par date d'ingestion."
)
pdf.chapter_title("Processus", level=3)
pdf.bullet("Lecture de la table plans depuis MySQL via le driver com.mysql.cj.jdbc.Driver")
pdf.bullet("Lecture de la table costs depuis PostgreSQL via org.postgresql.Driver")
pdf.bullet("Ecriture en Parquet dans s3a://datalake/raw/plans/year=YYYY/month=MM/day=DD")
pdf.bullet("Ecriture en Parquet dans s3a://datalake/raw/costs/year=YYYY/month=MM/day=DD")
pdf.ln(2)
pdf.body_text("Resultat : 250 000 plans + 250 000 costs ecrits dans MinIO.")

# 5.2 Silver
pdf.add_page()
pdf.chapter_title("5.2 Couche Silver - Traitement (processor.py)", level=2)
pdf.body_text(
    "Le Processor applique 7 regles de validation, effectue la jointure entre "
    "plans et costs, et enrichit les donnees avec des fonctions de fenetre Spark SQL."
)

pdf.chapter_title("Regles de validation", level=3)
pdf.table(
    ["#", "Regle", "Description"],
    [
        ["1", "PlanID unique/non-null", "Suppression des doublons et valeurs nulles"],
        ["2", "StateCode valide", "Verification parmi les 51 codes US (50 etats + DC)"],
        ["3", "Franchise valide", "Deductible >= 0 et <= Out-of-Pocket Max"],
        ["4", "NetworkType valide", "Valeurs autorisees : HMO, PPO, EPO, POS"],
        ["5", "IssuerName non-vide", "Nom de l'assureur obligatoire"],
        ["6", "MetalLevel valide", "Bronze, Silver, Gold, Platinum ou Catastrophic"],
        ["7", "PlanYear >= 2020", "Exclusion des plans trop anciens"],
    ],
    col_widths=[10, 55, 125],
)

pdf.chapter_title("Jointure", level=3)
pdf.body_text("Inner join sur PlanID entre les tables plans (validees) et costs (validees).")

pdf.chapter_title("Fonctions de fenetre (Window Functions)", level=3)
pdf.table(
    ["Fonction", "Window", "Description"],
    [
        ["rank()", "StateCode / Deductible ASC", "Rang par franchise dans chaque etat"],
        ["avg()", "StateCode", "Franchise moyenne par etat"],
        ["count()", "StateCode", "Nombre de plans par etat"],
        ["count()", "StateCode, NetworkType", "Plans par etat et reseau"],
        ["pct_network", "Calcule", "% de chaque type reseau dans l'etat"],
        ["avg()", "StateCode, MetalLevel", "OOP max moyen par etat et metal"],
        ["score", "Formule", "Deductible + OOP_Max * 0.3"],
    ],
    col_widths=[35, 55, 100],
)

pdf.body_text("Resultat : 250 000 lignes enrichies ecrites dans s3a://datalake/silver/plans_enriched/")

# 5.3 Gold
pdf.add_page()
pdf.chapter_title("5.3 Couche Gold - Datamarts (datamart.py)", level=2)
pdf.body_text(
    "Le job Datamart lit les donnees Silver et construit 3 datamarts analytiques "
    "via Spark SQL, puis les ecrit dans PostgreSQL Gold via JDBC."
)

pdf.chapter_title("Datamart 1 : Accessibilite Financiere", level=3)
pdf.body_text("Repond a la question : comment varient les couts selon les etats et niveaux de plan ?")
pdf.table(
    ["Colonne", "Description"],
    [
        ["StateCode, MetalLevel", "Dimensions de regroupement"],
        ["num_plans", "Nombre de plans distincts"],
        ["avg_individual_deductible", "Franchise individuelle moyenne"],
        ["avg_individual_oop_max", "Maximum a charge moyen"],
        ["avg_affordability_score", "Score d'accessibilite (calcule en Silver)"],
        ["min/max_deductible", "Plage de franchise"],
    ],
    col_widths=[65, 125],
)
pdf.body_text("Volume : 255 lignes (51 etats x 5 niveaux metal).")

pdf.chapter_title("Datamart 2 : Structure du Marche", level=3)
pdf.body_text("Repond a la question : quelle est la repartition des reseaux et assureurs ?")
pdf.table(
    ["Colonne", "Description"],
    [
        ["StateCode, NetworkType, IssuerName", "Dimensions de regroupement"],
        ["num_plans", "Nombre de plans"],
        ["metal_diversity", "Nombre de niveaux metal couverts"],
        ["network_share_pct", "Part de marche du type reseau dans l'etat"],
        ["county_coverage", "Nombre de comtes couverts"],
    ],
    col_widths=[70, 120],
)
pdf.body_text("Volume : 8 160 lignes.")

pdf.chapter_title("Datamart 3 : Competitivite des Plans", level=3)
pdf.body_text("Repond a la question : comment se comparent les plans sur les copays et exclusions ?")
pdf.table(
    ["Colonne", "Description"],
    [
        ["StateCode, MetalLevel, NetworkType", "Dimensions de regroupement"],
        ["BenefitCategory", "Categorie de prestation"],
        ["avg_copay_primary/specialist/er/generic", "Copays moyens par type de soin"],
        ["avg_coinsurance_rate", "Taux de coassurance moyen"],
        ["num_excluded", "Nombre de prestations exclues"],
        ["num_hsa_eligible", "Nombre de plans eligibles HSA"],
    ],
    col_widths=[70, 120],
)
pdf.body_text("Volume : 10 192 lignes.")

# ================================================================
# 6. API REST
# ================================================================
pdf.add_page()
pdf.chapter_title("6. API REST (FastAPI + JWT)")
pdf.body_text(
    "L'API REST expose les 3 datamarts avec authentification JWT, pagination "
    "et filtres. Elle est documentee automatiquement via Swagger UI."
)

pdf.chapter_title("Authentification", level=2)
pdf.body_text(
    "L'API utilise OAuth2 avec des tokens JWT (JSON Web Token). Deux comptes de demo "
    "sont preconfigures : admin/admin123 (role admin) et analyst/analyst123 (role analyst). "
    "Le token expire apres 60 minutes."
)

pdf.chapter_title("Endpoints", level=2)
pdf.table(
    ["Methode", "Endpoint", "Description"],
    [
        ["POST", "/auth/login", "Authentification, retourne un token JWT"],
        ["GET", "/health", "Verification de l'etat de l'API et de la BDD"],
        ["GET", "/datamarts/affordability", "DM1 pagine avec filtres state, metal_level"],
        ["GET", "/datamarts/affordability/stats", "Statistiques agregees DM1"],
        ["GET", "/datamarts/market-structure", "DM2 pagine avec filtres state, network, issuer"],
        ["GET", "/datamarts/market-structure/by-network", "Repartition nationale par reseau"],
        ["GET", "/datamarts/competitiveness", "DM3 pagine avec filtres multiples"],
        ["GET", "/datamarts/competitiveness/copay-summary", "Resume copays par metal level"],
    ],
    col_widths=[20, 75, 95],
)

pdf.chapter_title("Securite", level=2)
pdf.bullet("Tous les endpoints /datamarts/* necessitent un token JWT valide (header Authorization: Bearer).")
pdf.bullet("Sans token ou avec un token invalide, l'API retourne une erreur 401 Unauthorized.")
pdf.bullet("CORS active pour permettre l'acces depuis le dashboard Streamlit.")

pdf.chapter_title("Pagination", level=2)
pdf.body_text(
    "Chaque endpoint de datamart supporte les parametres page et page_size. "
    "La reponse inclut le total de resultats, le nombre de pages, et les items de la page courante."
)

# ================================================================
# 7. DASHBOARD
# ================================================================
pdf.add_page()
pdf.chapter_title("7. Dashboard Streamlit")
pdf.body_text(
    "Le dashboard offre une visualisation interactive des 3 datamarts avec 12 graphiques "
    "Plotly, organises en 4 onglets. Il se connecte directement a PostgreSQL Gold."
)

pdf.chapter_title("Graphiques", level=2)
pdf.table(
    ["#", "Type", "Description"],
    [
        ["1", "Carte choroplethe", "Franchise individuelle moyenne par etat"],
        ["2", "Barres groupees", "Franchise vs OOP Max par niveau metal"],
        ["3", "Box plot", "Distribution du score d'accessibilite par niveau"],
        ["4", "Barres horizontales", "Top etats les plus/moins chers"],
        ["5", "Donut", "Repartition des plans par type de reseau"],
        ["6", "Barres", "Diversite des niveaux metal par reseau"],
        ["7", "Barres horizontales", "Top 15 assureurs par nombre de plans"],
        ["8", "Heatmap", "Franchise moyenne par etat et type de reseau"],
        ["9", "Barres groupees", "Copays moyens par niveau de plan"],
        ["10", "Barres groupees", "Taux de coassurance par niveau et reseau"],
        ["11", "Barres", "% de plans eligibles HSA par niveau"],
        ["12", "Heatmap", "Exclusions par etat et categorie de prestation"],
    ],
    col_widths=[10, 45, 135],
)

pdf.chapter_title("Filtres interactifs", level=2)
pdf.bullet("Selection des etats (multiselect)")
pdf.bullet("Selection des niveaux metal (Bronze, Silver, Gold, Platinum, Catastrophic)")
pdf.bullet("Selection des types de reseau (HMO, PPO, EPO, POS)")
pdf.body_text("Tous les graphiques se mettent a jour dynamiquement selon les filtres selectionnes.")

# ================================================================
# 8. AIRFLOW
# ================================================================
pdf.add_page()
pdf.chapter_title("8. Orchestration Airflow")
pdf.body_text(
    "Apache Airflow orchestre le pipeline via un DAG (Directed Acyclic Graph) "
    "qui enchaine les 3 etapes dans l'ordre, avec execution quotidienne a 6h UTC."
)

pdf.chapter_title("DAG insurance_pipeline", level=2)
pdf.code_block(
    "feeder_bronze  >>  processor_silver  >>  datamart_gold\n"
    "  (Bronze)            (Silver)              (Gold)\n"
    "\n"
    "Schedule : 0 6 * * * (quotidien a 6h UTC)\n"
    "Retries  : 1 (delai 5 min)\n"
    "Catchup  : False"
)
pdf.ln(2)

pdf.table(
    ["Tache", "Type", "Action"],
    [
        ["feeder_bronze", "BashOperator", "spark-submit feeder.py (MySQL+PG -> MinIO)"],
        ["processor_silver", "BashOperator", "spark-submit processor.py (Validation+Jointure)"],
        ["datamart_gold", "BashOperator", "spark-submit datamart.py (Datamarts -> PG Gold)"],
    ],
    col_widths=[45, 40, 105],
)

pdf.body_text(
    "Chaque tache lance un spark-submit dans le conteneur Spark Master. "
    "Les dependances garantissent que le Silver ne demarre qu'apres le Bronze, "
    "et le Gold qu'apres le Silver."
)

# ================================================================
# 9. DOCKER
# ================================================================
pdf.add_page()
pdf.chapter_title("9. Deploiement Docker")
pdf.body_text(
    "L'ensemble du projet est conteneurise avec Docker Compose. "
    "12 services sont definis dans docker-compose.yml :"
)

pdf.table(
    ["Service", "Image / Build", "Role"],
    [
        ["mysql", "Build ./docker/mysql", "Source A : plans d'assurance"],
        ["postgres-source", "Build ./docker/postgres", "Source B : couts"],
        ["minio", "minio/minio:latest", "Data lake S3-compatible"],
        ["minio-init", "minio/mc:latest", "Creation des buckets"],
        ["postgres-hive", "postgres:13", "Backend Hive Metastore"],
        ["hive-metastore", "Build ./docker/hive", "Catalogue des tables"],
        ["spark-master", "Build ./docker/spark", "Noeud maitre Spark"],
        ["spark-worker", "Build ./docker/spark", "Noeud worker Spark"],
        ["postgres-gold", "postgres:15", "Base des datamarts"],
        ["airflow", "apache/airflow:2.8.1", "Orchestration DAG"],
        ["api", "Build ./api", "API REST FastAPI"],
        ["visualization", "Build ./visualization", "Dashboard Streamlit"],
    ],
    col_widths=[40, 60, 90],
)

pdf.chapter_title("Reseau", level=2)
pdf.body_text(
    "Tous les services sont connectes au reseau Docker 'bigdata' (bridge), "
    "permettant la communication inter-conteneurs par nom de service."
)

# ================================================================
# 10. GUIDE EXECUTION
# ================================================================
pdf.add_page()
pdf.chapter_title("10. Guide d'execution")
pdf.body_text("Prerequis : Docker et Docker Compose installes.")

pdf.chapter_title("Lancement automatise", level=2)
pdf.code_block(
    "# 1. Cloner le projet\n"
    "git clone <repo_url>\n"
    "cd Projet-big-data\n"
    "\n"
    "# 2. Lancer le script de demo complet\n"
    "./run_demo.sh"
)

pdf.body_text("Le script automatise toutes les etapes :")
pdf.bullet("Generation des donnees (250 000 lignes)")
pdf.bullet("Telechargement des JARs JDBC pour Spark")
pdf.bullet("Demarrage des 12 conteneurs Docker")
pdf.bullet("Attente de la disponibilite des services")
pdf.bullet("Execution du pipeline Spark (Bronze, Silver, Gold)")
pdf.bullet("Verification des resultats dans PostgreSQL Gold")

pdf.chapter_title("Lancement manuel", level=2)
pdf.code_block(
    "# 1. Generer les donnees\n"
    "python3 data/generate_data.py\n"
    "\n"
    "# 2. Telecharger les JARs JDBC\n"
    "bash spark/download_jars.sh\n"
    "\n"
    "# 3. Demarrer l'infrastructure\n"
    "docker compose up -d --build\n"
    "\n"
    "# 4. Executer le pipeline Spark\n"
    "# Bronze\n"
    "docker exec spark-master spark-submit /opt/spark-jobs/feeder.py ...\n"
    "# Silver\n"
    "docker exec spark-master spark-submit /opt/spark-jobs/processor.py ...\n"
    "# Gold\n"
    "docker exec spark-master spark-submit /opt/spark-jobs/datamart.py ..."
)

pdf.chapter_title("Acces aux interfaces", level=2)
pdf.table(
    ["Interface", "URL", "Identifiants"],
    [
        ["Spark Master UI", "http://localhost:8080", "-"],
        ["MinIO Console", "http://localhost:9001", "minioadmin / minioadmin"],
        ["Airflow", "http://localhost:8082", "admin / admin"],
        ["API Swagger", "http://localhost:8000/docs", "-"],
        ["Dashboard", "http://localhost:8501", "-"],
    ],
    col_widths=[50, 75, 65],
)

pdf.chapter_title("Arret", level=2)
pdf.code_block("docker compose down -v")

# ================================================================
# STRUCTURE DU PROJET
# ================================================================
pdf.add_page()
pdf.chapter_title("Annexe : Structure du projet")
pdf.code_block(
    ".\n"
    "|-- README.md\n"
    "|-- docker-compose.yml            # 12 services Docker\n"
    "|-- run_demo.sh                   # Script de demo automatise\n"
    "|-- data/\n"
    "|   |-- generate_data.py          # Generateur (250k lignes)\n"
    "|   |-- csv/                      # Fichiers CSV generes\n"
    "|-- docker/\n"
    "|   |-- mysql/init/               # Schema + chargement MySQL\n"
    "|   |-- postgres/init/            # Schema + chargement PostgreSQL\n"
    "|   |-- hive/                     # Config Hive Metastore\n"
    "|   |-- spark/                    # Dockerfile Spark + JARs\n"
    "|-- spark/\n"
    "|   |-- download_jars.sh          # Telechargement JARs JDBC\n"
    "|   |-- jobs/\n"
    "|       |-- feeder.py             # Bronze : Sources -> MinIO\n"
    "|       |-- processor.py          # Silver : Validation + Jointures\n"
    "|       |-- datamart.py           # Gold : Datamarts -> PostgreSQL\n"
    "|-- airflow/\n"
    "|   |-- dags/\n"
    "|       |-- insurance_pipeline.py # DAG Airflow\n"
    "|-- api/\n"
    "|   |-- Dockerfile\n"
    "|   |-- main.py                   # FastAPI + JWT + pagination\n"
    "|   |-- requirements.txt\n"
    "|-- visualization/\n"
    "|   |-- Dockerfile\n"
    "|   |-- app.py                    # Streamlit + 12 graphiques\n"
    "|   |-- requirements.txt"
)

# ================================================================
# SAVE
# ================================================================
output_path = "/Users/nathanlamtara/Desktop/Projet-big-data/demo/Livrable_Projet_Big_Data.pdf"
pdf.output(output_path)
print(f"PDF genere : {output_path}")
