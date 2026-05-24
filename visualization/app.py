"""
Streamlit dashboard - US Health Insurance Marketplace Analysis
================================================================
Visualizes the 3 datamarts with interactive charts using Plotly.
Connects directly to PostgreSQL Gold database.
"""

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://api:apipass@localhost:5433/datamarts"
)

st.set_page_config(
    page_title="US Health Insurance Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    [data-testid="stMetricValue"] { font-size: 1.4rem; }
    [data-testid="stMetricLabel"] { font-size: 0.9rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 20px;
        border-radius: 8px 8px 0 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL, pool_pre_ping=True)


@st.cache_data(ttl=300)
def load_table(table: str) -> pd.DataFrame:
    try:
        return pd.read_sql_table(table, get_engine())
    except Exception as e:
        st.error(f"Could not load {table}: {e}")
        return pd.DataFrame()


# ── Header ───────────────────────────────────────────────────────────
st.markdown("# 🏥 US Health Insurance Marketplace")
st.markdown(
    "Pipeline Big Data **Medallion** (Bronze → Silver → Gold) — "
    "Analyse de **250 000 plans** d'assurance sante aux Etats-Unis"
)

# ── Load data ────────────────────────────────────────────────────────
dm1 = load_table("datamart_affordability")
dm2 = load_table("datamart_market_structure")
dm3 = load_table("datamart_competitiveness")

if dm1.empty or dm2.empty or dm3.empty:
    st.warning(
        "Aucune donnee disponible. "
        "Lancez le pipeline Spark pour peupler les datamarts."
    )
    st.stop()

# Normalize column case
for df in (dm1, dm2, dm3):
    df.columns = [c.lower() for c in df.columns]

# Convert numeric columns
for col in ["avg_individual_deductible", "avg_family_deductible",
            "avg_individual_oop_max", "avg_family_oop_max",
            "min_deductible", "max_deductible"]:
    if col in dm1.columns:
        dm1[col] = pd.to_numeric(dm1[col], errors="coerce")

if "avg_deductible" in dm2.columns:
    dm2["avg_deductible"] = pd.to_numeric(dm2["avg_deductible"], errors="coerce")

for col in ["avg_copay_primary", "avg_copay_specialist", "avg_copay_er",
            "avg_copay_generic", "avg_coinsurance_rate"]:
    if col in dm3.columns:
        dm3[col] = pd.to_numeric(dm3[col], errors="coerce")

# ── Sidebar filters ──────────────────────────────────────────────────
st.sidebar.markdown("## Filtres")

states = sorted(dm1["statecode"].unique().tolist())
selected_states = st.sidebar.multiselect(
    "Etats", states, default=states[:10],
    help="Selectionnez les etats a analyser"
)

metal_order = ["Catastrophic", "Bronze", "Silver", "Gold", "Platinum"]
metals = [m for m in metal_order if m in dm1["metallevel"].unique()]
selected_metals = st.sidebar.multiselect(
    "Niveau (Metal Level)", metals, default=metals
)

network_types = sorted(dm2["networktype"].unique().tolist())
selected_networks = st.sidebar.multiselect(
    "Type de reseau", network_types, default=network_types
)

# Apply filters
dm1_f = dm1[dm1["statecode"].isin(selected_states) & dm1["metallevel"].isin(selected_metals)]
dm2_f = dm2[dm2["statecode"].isin(selected_states) & dm2["networktype"].isin(selected_networks)]
dm3_f = dm3[dm3["statecode"].isin(selected_states) & dm3["metallevel"].isin(selected_metals)]

# ── KPI row ──────────────────────────────────────────────────────────
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)

total_plans = int(dm2_f["num_plans"].sum())
n_states = dm1_f["statecode"].nunique()
n_issuers = dm2_f["issuername"].nunique()
avg_deductible = dm1_f["avg_individual_deductible"].mean()
avg_oop = dm1_f["avg_individual_oop_max"].mean()

col1.metric("Plans totaux", f"{total_plans:,}")
col2.metric("Etats couverts", n_states)
col3.metric("Assureurs", n_issuers)
col4.metric("Franchise moy.", f"${avg_deductible:,.0f}")
col5.metric("OOP Max moy.", f"${avg_oop:,.0f}")

st.markdown("---")

# ── Tabs per datamart ────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Accessibilite Financiere",
    "🏢 Structure du Marche",
    "⚡ Competitivite des Plans",
    "📋 Vue d'ensemble"
])

# Color palettes
METAL_COLORS = {
    "Catastrophic": "#95a5a6",
    "Bronze": "#cd7f32",
    "Silver": "#c0c0c0",
    "Gold": "#ffd700",
    "Platinum": "#e5e4e2",
}

# ─── DM1: Accessibilite Financiere ──────────────────────────────────
with tab1:
    st.subheader("Accessibilite financiere par etat et niveau de plan")

    # Chart 1: Carte choroplethe
    state_avg = (
        dm1_f.groupby("statecode")["avg_individual_deductible"]
        .mean().reset_index()
    )
    fig_map = px.choropleth(
        state_avg,
        locations="statecode",
        locationmode="USA-states",
        color="avg_individual_deductible",
        scope="usa",
        color_continuous_scale="RdYlGn_r",
        title="Franchise individuelle moyenne par etat (USD)",
        labels={"avg_individual_deductible": "Franchise (USD)", "statecode": "Etat"},
    )
    fig_map.update_layout(
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=40, b=0),
        height=450,
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # Chart 2: Franchise vs OOP Max par Metal Level
    c1, c2 = st.columns(2)

    with c1:
        metal_summary = (
            dm1_f.groupby("metallevel")[
                ["avg_individual_deductible", "avg_individual_oop_max"]
            ].mean().reindex(metal_order).dropna().reset_index()
        )
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Franchise moyenne",
            x=metal_summary["metallevel"],
            y=metal_summary["avg_individual_deductible"],
            marker_color="#3498db",
        ))
        fig_bar.add_trace(go.Bar(
            name="OOP Max moyen",
            x=metal_summary["metallevel"],
            y=metal_summary["avg_individual_oop_max"],
            marker_color="#e74c3c",
        ))
        fig_bar.update_layout(
            barmode="group",
            title="Franchise vs OOP Max par niveau de plan",
            yaxis_title="USD",
            height=400,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        # Chart 3: Score d'accessibilite par etat (box plot)
        fig_afford = px.box(
            dm1_f, x="metallevel", y="avg_affordability_score",
            color="metallevel",
            color_discrete_map=METAL_COLORS,
            title="Distribution du score d'accessibilite par niveau",
            labels={"avg_affordability_score": "Score", "metallevel": "Niveau"},
            category_orders={"metallevel": metal_order},
        )
        fig_afford.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_afford, use_container_width=True)

    # Chart 4: Top 10 etats les plus chers vs moins chers
    state_deduct = (
        dm1_f.groupby("statecode")["avg_individual_deductible"]
        .mean().sort_values()
    )
    cheapest = state_deduct.head(10).reset_index()
    cheapest["category"] = "Moins chers"
    expensive = state_deduct.tail(10).reset_index()
    expensive["category"] = "Plus chers"
    compare = pd.concat([cheapest, expensive])

    fig_compare = px.bar(
        compare, x="avg_individual_deductible", y="statecode",
        color="category", orientation="h",
        color_discrete_map={"Moins chers": "#2ecc71", "Plus chers": "#e74c3c"},
        title="Top 10 etats les plus/moins chers (franchise moyenne)",
        labels={"avg_individual_deductible": "Franchise (USD)", "statecode": "Etat"},
    )
    fig_compare.update_layout(height=500, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_compare, use_container_width=True)

    with st.expander("Donnees brutes - Accessibilite"):
        st.dataframe(dm1_f, use_container_width=True, height=300)


# ─── DM2: Structure du Marche ───────────────────────────────────────
with tab2:
    st.subheader("Structure de l'offre et repartition du marche")

    c1, c2 = st.columns(2)

    with c1:
        # Chart 5: Donut - Repartition par type de reseau
        network_dist = dm2_f.groupby("networktype")["num_plans"].sum().reset_index()
        fig_pie = px.pie(
            network_dist, names="networktype", values="num_plans",
            title="Repartition des plans par type de reseau",
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.45,
        )
        fig_pie.update_traces(textinfo="percent+label")
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        # Chart 6: Diversite des niveaux metal par reseau
        diversity = (
            dm2_f.groupby("networktype")
            .agg(
                total_plans=("num_plans", "sum"),
                avg_diversity=("metal_diversity", "mean"),
                avg_counties=("county_coverage", "mean"),
            ).reset_index()
        )
        fig_diversity = px.bar(
            diversity, x="networktype", y="avg_diversity",
            color="total_plans",
            title="Diversite moyenne des niveaux metal par type de reseau",
            labels={
                "avg_diversity": "Metal diversity",
                "networktype": "Reseau",
                "total_plans": "Plans",
            },
            color_continuous_scale="Viridis",
        )
        fig_diversity.update_layout(height=400)
        st.plotly_chart(fig_diversity, use_container_width=True)

    # Chart 7: Top 15 assureurs
    top_issuers = (
        dm2_f.groupby("issuername")["num_plans"].sum()
        .sort_values(ascending=False).head(15).reset_index()
    )
    fig_issuer = px.bar(
        top_issuers, x="num_plans", y="issuername", orientation="h",
        title="Top 15 assureurs par nombre de plans",
        labels={"num_plans": "Nombre de plans", "issuername": "Assureur"},
        color="num_plans", color_continuous_scale="Blues",
    )
    fig_issuer.update_layout(
        yaxis={"categoryorder": "total ascending"},
        height=500,
    )
    st.plotly_chart(fig_issuer, use_container_width=True)

    # Chart 8: Franchise moyenne par reseau et etat (heatmap)
    net_state = (
        dm2_f.groupby(["statecode", "networktype"])["avg_deductible"]
        .mean().reset_index()
    )
    pivot_net = net_state.pivot(
        index="statecode", columns="networktype", values="avg_deductible"
    ).fillna(0)

    if not pivot_net.empty:
        fig_heat_net = px.imshow(
            pivot_net, title="Franchise moyenne par etat et type de reseau",
            color_continuous_scale="YlOrRd", aspect="auto",
            labels={"color": "Franchise (USD)"},
        )
        fig_heat_net.update_layout(height=600)
        st.plotly_chart(fig_heat_net, use_container_width=True)

    with st.expander("Donnees brutes - Structure du marche"):
        st.dataframe(dm2_f, use_container_width=True, height=300)


# ─── DM3: Competitivite ─────────────────────────────────────────────
with tab3:
    st.subheader("Competitivite et couverture des plans")

    # Chart 9: Co-paiements par niveau de plan
    copay_cols = ["avg_copay_primary", "avg_copay_specialist",
                  "avg_copay_er", "avg_copay_generic"]
    copay_labels = {
        "avg_copay_primary": "Soins primaires",
        "avg_copay_specialist": "Specialiste",
        "avg_copay_er": "Urgences",
        "avg_copay_generic": "Medicament generique",
    }

    copay_summary = (
        dm3_f.groupby("metallevel")[copay_cols]
        .mean().reindex(metal_order).dropna().reset_index()
    )

    fig_copay = go.Figure()
    colors = ["#3498db", "#e67e22", "#e74c3c", "#2ecc71"]
    for i, col in enumerate(copay_cols):
        fig_copay.add_trace(go.Bar(
            name=copay_labels[col],
            x=copay_summary["metallevel"],
            y=copay_summary[col],
            marker_color=colors[i],
        ))
    fig_copay.update_layout(
        barmode="group",
        title="Co-paiements moyens (USD) par niveau de plan",
        yaxis_title="USD",
        height=450,
    )
    st.plotly_chart(fig_copay, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        # Chart 10: Taux de coassurance par niveau et reseau
        coinsurance = (
            dm3_f.groupby(["metallevel", "networktype"])["avg_coinsurance_rate"]
            .mean().reset_index()
        )
        fig_coins = px.bar(
            coinsurance, x="metallevel", y="avg_coinsurance_rate",
            color="networktype", barmode="group",
            title="Taux de coassurance moyen par niveau et reseau",
            labels={
                "avg_coinsurance_rate": "Taux",
                "metallevel": "Niveau",
                "networktype": "Reseau",
            },
            category_orders={"metallevel": metal_order},
        )
        fig_coins.update_layout(height=400)
        st.plotly_chart(fig_coins, use_container_width=True)

    with c2:
        # Chart 11: HSA Eligibilite par niveau
        hsa = (
            dm3_f.groupby("metallevel")
            .agg(
                total=("num_plans", "sum"),
                hsa=("num_hsa_eligible", "sum"),
            ).reset_index()
        )
        hsa["pct_hsa"] = (hsa["hsa"] / hsa["total"] * 100).round(1)
        hsa = hsa.set_index("metallevel").reindex(metal_order).dropna().reset_index()

        fig_hsa = px.bar(
            hsa, x="metallevel", y="pct_hsa",
            color="metallevel", color_discrete_map=METAL_COLORS,
            title="% de plans eligibles HSA par niveau",
            labels={"pct_hsa": "% HSA", "metallevel": "Niveau"},
        )
        fig_hsa.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_hsa, use_container_width=True)

    # Chart 12: Heatmap exclusions par etat et categorie
    heat = (
        dm3_f.groupby(["statecode", "benefitcategory"])["num_excluded"]
        .sum().reset_index()
    )
    pivot = heat.pivot(
        index="statecode", columns="benefitcategory", values="num_excluded"
    ).fillna(0)

    if not pivot.empty:
        fig_heat = px.imshow(
            pivot,
            title="Exclusions de couverture par etat et categorie de prestation",
            color_continuous_scale="Reds",
            aspect="auto",
            labels={"color": "Nb exclusions"},
        )
        fig_heat.update_layout(height=600)
        st.plotly_chart(fig_heat, use_container_width=True)

    with st.expander("Donnees brutes - Competitivite"):
        st.dataframe(dm3_f, use_container_width=True, height=300)


# ─── Tab 4: Vue d'ensemble ──────────────────────────────────────────
with tab4:
    st.subheader("Vue d'ensemble du pipeline")

    # Pipeline summary
    st.markdown("""
    ### Architecture Medallion
    | Couche | Source | Destination | Volume |
    |--------|--------|-------------|--------|
    | **Bronze** | MySQL + PostgreSQL | MinIO (Parquet) | 250 000 lignes |
    | **Silver** | MinIO | MinIO + Hive | 250 000 lignes (7 regles de validation) |
    | **Gold** | MinIO Silver | PostgreSQL | 3 datamarts |
    """)

    st.markdown("### Volumes des datamarts")
    dm_sizes = pd.DataFrame({
        "Datamart": ["Accessibilite", "Structure du marche", "Competitivite"],
        "Lignes": [len(dm1), len(dm2), len(dm3)],
        "Description": [
            "Franchise et OOP par etat/metal",
            "Repartition reseau/assureur par etat",
            "Copays, coassurance, exclusions par etat/metal/reseau/categorie",
        ],
    })
    st.dataframe(dm_sizes, use_container_width=True, hide_index=True)

    # Global stats
    c1, c2 = st.columns(2)

    with c1:
        # Plans par metal level (global)
        plans_by_metal = dm1.groupby("metallevel")["num_plans"].sum().reset_index()
        plans_by_metal = plans_by_metal.set_index("metallevel").reindex(metal_order).dropna().reset_index()
        fig_global_metal = px.bar(
            plans_by_metal, x="metallevel", y="num_plans",
            color="metallevel", color_discrete_map=METAL_COLORS,
            title="Nombre total de plans par niveau metal",
            labels={"num_plans": "Plans", "metallevel": "Niveau"},
        )
        fig_global_metal.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_global_metal, use_container_width=True)

    with c2:
        # Scatter: franchise vs OOP par etat
        state_scatter = (
            dm1.groupby("statecode")
            .agg(
                deductible=("avg_individual_deductible", "mean"),
                oop=("avg_individual_oop_max", "mean"),
                plans=("num_plans", "sum"),
            ).reset_index()
        )
        fig_scatter = px.scatter(
            state_scatter, x="deductible", y="oop",
            size="plans", hover_name="statecode",
            title="Franchise vs OOP Max par etat (taille = nb plans)",
            labels={"deductible": "Franchise moy. (USD)", "oop": "OOP Max moy. (USD)"},
            color="deductible", color_continuous_scale="RdYlGn_r",
        )
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)


# ── Footer ───────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Source : US Health Insurance Marketplace (donnees generees) | "
    "Pipeline : MySQL/PostgreSQL → Spark → MinIO (Bronze) → Silver → PostgreSQL Gold | "
    "Dashboard : Streamlit + Plotly"
)
