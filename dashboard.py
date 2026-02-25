import os
import re
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from hermes_api import load_data_from_api, sync_csv_from_api

st.set_page_config(page_title="Pool Progression – Epitech", page_icon="📊", layout="wide")

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "datasets")
CACHE_FILE = os.path.join(os.path.dirname(__file__), ".api_cache.json")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), ".dashboard_config.json")

def save_config(data_source: str):
    """Sauvegarde la configuration (source selectionnee)."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"data_source": data_source}, f)

def load_config():
    """Charge la configuration."""
    if not os.path.exists(CONFIG_FILE):
        return "CSV"
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("data_source", "CSV")
    except Exception:
        return "CSV"

def clear_config():
    """Supprime la configuration."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

def save_api_cache(df: pd.DataFrame, year: str, unit: str, instance: str):
    """Sauvegarde les données API dans un fichier JSON."""
    if df.empty:
        return
    cache_data = {
        "year": year,
        "unit": unit,
        "instance": instance,
        "data": df.to_dict(orient="index"),
        "columns": list(df.columns)
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f)

def load_api_cache():
    """Charge les données API depuis le fichier JSON."""
    if not os.path.exists(CACHE_FILE):
        return pd.DataFrame(), None, None, None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        df = pd.DataFrame.from_dict(cache_data["data"], orient="index")
        df = df.reindex(columns=cache_data["columns"])
        df.index.name = "login"
        return df, cache_data.get("year"), cache_data.get("unit"), cache_data.get("instance")
    except Exception:
        return pd.DataFrame(), None, None, None

def clear_api_cache():
    """Supprime le fichier cache."""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)

@st.cache_data
def load_data(datasets_dir: str, use_api: bool = False) -> pd.DataFrame:
    if use_api:
        return load_data_from_api(datasets_dir)
    results = {}
    if not os.path.exists(datasets_dir):
        return pd.DataFrame()
    for filename in sorted(os.listdir(datasets_dir)):
        if not filename.endswith(".csv"):
            continue
        match = re.search(r"databootcampd(\d+)", filename)
        if not match:
            continue
        day_label = f"day{match.group(1)}"
        filepath = os.path.join(datasets_dir, filename)
        try:
            df_day = pd.read_csv(filepath, sep=";")
        except Exception:
            continue
        if "login" not in df_day.columns or "test %" not in df_day.columns:
            continue
        df_day = df_day[["login", "test %"]].copy()
        df_day["test %"] = pd.to_numeric(df_day["test %"], errors="coerce").fillna(0)
        for _, row in df_day.iterrows():
            login = str(row["login"]).strip()
            pct = float(row["test %"])
            results.setdefault(login, {})[day_label] = pct
    if not results:
        return pd.DataFrame()
    df = pd.DataFrame.from_dict(results, orient="index")
    df = df.reindex(sorted(df.columns), axis=1)
    df.index.name = "login"
    return df

# Init session state - charger depuis le fichier cache si disponible
if "df_raw" not in st.session_state:
    # Essayer de charger depuis le fichier cache
    cached_df, cached_year, cached_unit, cached_instance = load_api_cache()
    st.session_state.df_raw = cached_df
    st.session_state.api_year = cached_year or "2025"
    st.session_state.api_unit = cached_unit or "B-DAT-200"
    st.session_state.api_instance = cached_instance or ""
else:
    st.session_state.api_year = "2025"
    st.session_state.api_unit = "B-DAT-200"
    st.session_state.api_instance = ""

if "data_source" not in st.session_state:
    # Charger depuis le fichier config
    st.session_state.data_source = load_config()

st.sidebar.title("Source de donnees")

# Radio avec callback pour persister la selection
data_source = st.sidebar.radio(
    "Choisir la source",
    options=["CSV", "API", "Sync"],
    index=["CSV", "API", "Sync"].index(st.session_state.data_source),
    key="data_source_radio"
)

# Sauvegarder la selection
if data_source != st.session_state.data_source:
    st.session_state.data_source = data_source
    save_config(data_source)  # Persister dans le fichier
    st.rerun()

# Mode API
if st.session_state.data_source == "API":
    st.sidebar.divider()
    st.sidebar.subheader("Config API")
    
    # Utiliser les valeurs du session_state si disponibles
    default_year = st.session_state.get("api_year", "2025")
    default_unit = st.session_state.get("api_unit", "B-DAT-200")
    default_instance = st.session_state.get("api_instance", "")
    
    api_year = st.sidebar.text_input("Annee", value=default_year)
    api_unit = st.sidebar.text_input("Unite", value=default_unit)
    api_instance = st.sidebar.text_input("Instance", value=default_instance)
    
    # Sauvegarder les valeurs dans session_state
    st.session_state.api_year = api_year
    st.session_state.api_unit = api_unit
    st.session_state.api_instance = api_instance
    
    if st.sidebar.button("Charger API", type="primary"):
        with st.spinner("Chargement..."):
            df = load_data_from_api(DATASETS_DIR, instance=api_instance or None, year=api_year, unit=api_unit)
        st.session_state.df_raw = df
        # Sauvegarder dans le fichier cache
        save_api_cache(df, api_year, api_unit, api_instance)
        st.rerun()
    
    if st.sidebar.button("Vider", type="secondary"):
        st.session_state.df_raw = pd.DataFrame()
        clear_api_cache()
        clear_config()
        st.cache_data.clear()
        st.rerun()
    
    if not st.session_state.df_raw.empty:
        st.sidebar.success(f"{len(st.session_state.df_raw)} etudiants (persiste apres refresh)")

# Mode CSV
elif st.session_state.data_source == "CSV":
    st.session_state.df_raw = load_data(DATASETS_DIR)
    # Vider le cache API quand on passe en mode CSV
    clear_api_cache()

# Mode Sync
elif st.session_state.data_source == "Sync":
    if st.sidebar.button("Synchroniser"):
        with st.spinner("Synchro..."):
            sync_csv_from_api(DATASETS_DIR)
        st.sidebar.success("Termine")
        clear_api_cache()
        st.cache_data.clear()
        st.rerun()
    st.session_state.df_raw = load_data(DATASETS_DIR)

df_raw = st.session_state.df_raw

# Affichage principal
if df_raw.empty:
    st.title("📊 Pool Progression")
    if st.session_state.data_source == "API":
        st.info("Mode API: Cliquez sur 'Charger API' dans la sidebar")
    else:
        st.info("Aucune donnee. Selectionnez CSV ou API dans la sidebar.")
else:
    n_days = len(df_raw.columns)
    day_means = df_raw.mean(axis=0)
    student_means = df_raw.mean(axis=1)
    overall_avg = student_means.mean()
    best_student = student_means.idxmax()
    hardest_day = day_means.idxmin()
    
    st.title(f"📊 Pool Progression – {len(df_raw)} etudiants sur {n_days} jours")
    st.caption(f"B-DAT-200 Data Bootcamp")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Etudiants", len(df_raw))
    col2.metric("Moyenne globale", f"{overall_avg:.1f}%")
    col3.metric("Meilleur", best_student.split("@")[0], f"{student_means[best_student]:.1f}%")
    col4.metric("Jour + difficile", hardest_day, f"{day_means[hardest_day]:.1f}%")
    
    st.divider()
    
    # Section 1 - Progression moyenne
    st.subheader("Progression moyenne de la promotion")
    fig_avg = px.line(x=day_means.index, y=day_means.values, markers=True,
                      labels={"x": "Jour", "y": "Moyenne (%)"},
                      title="Score moyen par jour")
    fig_avg.update_traces(line_color="#4C8BF5", line_width=3, marker_size=8)
    fig_avg.update_yaxes(range=[0, 105], ticksuffix="%")
    fig_avg.update_layout(hovermode="x unified")
    st.plotly_chart(fig_avg, use_container_width=True)
    
    st.divider()
    
    # Section 2 - Progression individuelle
    st.subheader("Progression individuelle")
    
    all_students = sorted(df_raw.index.tolist())
    selected_student = st.selectbox("Choisir un etudiant", options=all_students, 
                                    format_func=lambda x: x.split("@")[0])
    
    student_row = df_raw.loc[selected_student]
    
    fig_student = go.Figure()
    fig_student.add_trace(go.Scatter(
        x=student_row.index, y=student_row.values,
        mode="lines+markers", name=selected_student.split("@")[0],
        line=dict(color="#F04E37", width=3), marker=dict(size=9)))
    fig_student.add_trace(go.Scatter(
        x=day_means.index, y=day_means.values,
        mode="lines", name="Moyenne promo",
        line=dict(color="#4C8BF5", width=2, dash="dot")))
    fig_student.update_yaxes(range=[0, 105], ticksuffix="%")
    fig_student.update_layout(
        title=f"Progression de {selected_student.split('@')[0]}",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_student, use_container_width=True)
    
    # Mini-table
    detail_df = pd.DataFrame({"Jour": student_row.index, "Score (%)": student_row.values}).set_index("Jour")
    detail_df["Score (%)"] = detail_df["Score (%)"].map(lambda v: f"{v:.1f}%")
    st.dataframe(detail_df.T, use_container_width=True)
    
    st.divider()
    
    # Section 3 - Jours difficiles
    st.subheader("Top 3 jours les plus difficiles")
    n_hardest = min(3, n_days)
    hardest = day_means.nsmallest(n_hardest).sort_values()
    fig_hard = px.bar(x=hardest.index, y=hardest.values,
                      labels={"x": "Jour", "y": "Moyenne (%)"},
                      title=f"{n_hardest} jours avec les scores les plus bas",
                      color=hardest.values, color_continuous_scale="Reds_r")
    fig_hard.update_yaxes(range=[0, 105], ticksuffix="%")
    fig_hard.update_coloraxes(showscale=False)
    fig_hard.update_traces(text=[f"{v:.1f}%" for v in hardest.values], textposition="outside")
    st.plotly_chart(fig_hard, use_container_width=True)
    
    st.divider()
    
    # Section 4 - Etudiants en difficulte
    st.subheader("Etudiants en difficulte (moyenne < 20%)")
    at_risk = student_means[student_means < 20].sort_values()
    
    if at_risk.empty:
        st.success("Aucun etudiant en dessous de 20% de moyenne.")
    else:
        st.warning(f"{len(at_risk)} etudiant(s) sous la barre des 20%")
        
        fig_risk = px.bar(x=at_risk.index.str.split("@").str[0], y=at_risk.values,
                          labels={"x": "Etudiant", "y": "Moyenne (%)"},
                          title="Etudiants avec une moyenne generale < 20%",
                          color=at_risk.values, color_continuous_scale="Reds_r")
        fig_risk.add_hline(y=20, line_dash="dash", line_color="orange", annotation_text="20%")
        fig_risk.update_yaxes(range=[0, 105], ticksuffix="%")
        fig_risk.update_coloraxes(showscale=False)
        fig_risk.update_traces(text=[f"{v:.1f}%" for v in at_risk.values], textposition="outside")
        st.plotly_chart(fig_risk, use_container_width=True)
        
        # Detail table
        at_risk_df = df_raw.loc[at_risk.index].copy()
        at_risk_df["Moyenne"] = at_risk
        at_risk_df = at_risk_df.sort_values("Moyenne")
        at_risk_df.index = at_risk_df.index.str.split("@").str[0]
        fmt_risk = {col: "{:.1f}%" for col in at_risk_df.columns}
        st.dataframe(at_risk_df.style.format(fmt_risk).background_gradient(cmap="Reds_r", subset=at_risk_df.columns),
                     use_container_width=True)
    
    st.divider()
    
    # Section 5 - Classement
    st.subheader("Classement des etudiants")
    leaderboard = df_raw.copy()
    leaderboard["Moyenne"] = leaderboard.mean(axis=1)
    leaderboard = leaderboard.sort_values("Moyenne", ascending=False)
    leaderboard.index = leaderboard.index.str.split("@").str[0]
    
    fmt = {col: "{:.1f}%" for col in leaderboard.columns}
    st.dataframe(leaderboard.style.format(fmt).background_gradient(cmap="RdYlGn", subset=leaderboard.columns),
                 use_container_width=True, height=600)
