import os
import re
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from hermes_api import load_data_from_api, sync_csv_from_api

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pool Progression – Epitech",
    page_icon="📊",
    layout="wide",
)

# ── Data loading ──────────────────────────────────────────────────────────────
DATASETS_DIR = os.path.join(os.path.dirname(__file__), "datasets")


@st.cache_data
def load_data(datasets_dir: str, use_api: bool = False) -> pd.DataFrame:
    """Load all CSVs and return a DataFrame indexed by student login."""
    if use_api:
        return load_data_from_api(datasets_dir)
    
    results: dict[str, dict[str, float]] = {}

    for filename in sorted(os.listdir(datasets_dir)):
        if not filename.endswith(".csv"):
            continue
        match = re.search(r"databootcampd(\d+)", filename)
        if not match:
            continue
        day_label = f"day{match.group(1)}"
        filepath = os.path.join(datasets_dir, filename)
        df_day = pd.read_csv(filepath, sep=";")

        if "login" not in df_day.columns or "test %" not in df_day.columns:
            continue

        df_day = df_day[["login", "test %"]].copy()
        df_day["test %"] = pd.to_numeric(df_day["test %"], errors="coerce").fillna(0)

        for _, row in df_day.iterrows():
            login = str(row["login"]).strip()
            pct = float(row["test %"])
            if login not in results:
                results[login] = {}
            results[login][day_label] = pct

    df = pd.DataFrame.from_dict(results, orient="index")
    df = df.reindex(sorted(df.columns), axis=1)
    df.index.name = "login"
    return df


# ── Data source selection ─────────────────────────────────────────────────────
st.sidebar.title("Source de données")

data_source = st.sidebar.radio(
    "Choisir la source",
    options=["Fichiers CSV locaux", "API Hermès (direct)", "Sync API → CSV"],
    index=0,
    help="Fichiers CSV: mode offline | API direct: temps réel | Sync: met à jour les CSV"
)

if data_source == "Fichiers CSV locaux":
    df_raw = load_data(DATASETS_DIR, use_api=False)
elif data_source == "API Hermès (direct)":
    # Configuration API
    st.sidebar.divider()
    st.sidebar.subheader("⚙️ Configuration API")
    
    api_year = st.sidebar.text_input("Année", value="2025", help="Ex: 2025")
    api_unit = st.sidebar.text_input("Unité", value="B-DAT-200", help="Ex: B-DAT-200")
    api_instance = st.sidebar.text_input("Instance (optionnel)", value="", help="Ex: MAR-2-1")
    
    if st.sidebar.button("🚀 Charger depuis l'API"):
        with st.spinner("Chargement depuis l'API Hermès..."):
            df_raw = load_data_from_api(DATASETS_DIR, instance=api_instance or None, year=api_year, unit=api_unit)
        st.sidebar.success(f"✅ {len(df_raw)} étudiants chargés")
    else:
        # Si pas encore chargé, essayer de charger depuis les fichiers existants
        df_raw = load_data(DATASETS_DIR, use_api=False)
        if df_raw.empty:
            st.info("👆 Configure les paramètres API et clique sur 'Charger'")
            st.stop()
elif data_source == "Sync API → CSV":
    if st.sidebar.button("🔄 Lancer la synchronisation"):
        with st.spinner("Synchronisation en cours..."):
            sync_csv_from_api(DATASETS_DIR)
        st.sidebar.success("✅ Synchronisation terminée")
        st.cache_data.clear()
        st.rerun()
    df_raw = load_data(DATASETS_DIR, use_api=False)

# ── Check if data exists ──────────────────────────────────────────────────────
if df_raw.empty:
    st.title("📊 Pool Progression – Epitech")
    st.info("👋 Bienvenue ! Aucun dataset n'est chargé.")
    
    st.markdown("""
    ### Pour commencer :
    1. **Upload tes datasets** ci-dessous ⬇️
    2. Ou **restaure les datasets de backup** :
       ```bash
       cp datasets_backup/* datasets/
       ```
    3. Puis **rafraîchis la page** (F5)
    
    Les fichiers doivent être au format `databootcampdXX.csv` exportés depuis Hermes.
    """)
    
    # Upload section in main page when empty
    st.divider()
    st.subheader("📁 Upload datasets")
    
    uploaded_files = st.file_uploader(
        "Déposer les fichiers CSV",
        type=["csv"],
        accept_multiple_files=True,
        help="Fichiers CSV exportés depuis Hermes (format: login;test %)",
    )
    
    if uploaded_files:
        saved_count = 0
        for uploaded_file in uploaded_files:
            if not re.search(r"databootcampd\d+", uploaded_file.name):
                st.warning(f"⚠️ {uploaded_file.name} : nom non reconnu (attendu: databootcampdX.csv)")
                continue
            
            save_path = os.path.join(DATASETS_DIR, uploaded_file.name)
            try:
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                saved_count += 1
            except Exception as e:
                st.error(f"❌ Erreur lors de la sauvegarde de {uploaded_file.name}: {e}")
        
        if saved_count > 0:
            st.success(f"✅ {saved_count} fichier(s) sauvegardé(s)")
            st.info("🔄 Rafraîchissez la page pour charger les données")
            if st.button("🔄 Rafraîchir maintenant"):
                st.cache_data.clear()
                st.rerun()
    
    st.sidebar.title("Paramètres")
    st.sidebar.warning("⚠️ Aucun dataset chargé")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
# Paramètres (le titre est déjà défini dans la section source de données)

# ── Upload section ────────────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.subheader("📁 Upload datasets")

uploaded_files = st.sidebar.file_uploader(
    "Déposer les fichiers CSV",
    type=["csv"],
    accept_multiple_files=True,
    help="Fichiers CSV exportés depuis Hermes (format: login;test %)",
)

if uploaded_files:
    saved_count = 0
    for uploaded_file in uploaded_files:
        # Validate filename pattern
        if not re.search(r"databootcampd\d+", uploaded_file.name):
            st.sidebar.warning(f"⚠️ {uploaded_file.name} : nom non reconnu (attendu: databootcampdX.csv)")
            continue

        save_path = os.path.join(DATASETS_DIR, uploaded_file.name)
        try:
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            saved_count += 1
        except Exception as e:
            st.sidebar.error(f"❌ Erreur lors de la sauvegarde de {uploaded_file.name}: {e}")

    if saved_count > 0:
        st.sidebar.success(f"✅ {saved_count} fichier(s) sauvegardé(s)")
        st.sidebar.info("🔄 Rafraîchissez la page pour charger les nouveaux datasets")

# ── Clear section ─────────────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.subheader("🗑️ Clear data")

if st.sidebar.button("🗑️ Supprimer tous les datasets", type="secondary", help="Supprime tous les fichiers CSV du dossier datasets"):
    deleted_count = 0
    for filename in os.listdir(DATASETS_DIR):
        if filename.endswith(".csv"):
            filepath = os.path.join(DATASETS_DIR, filename)
            try:
                os.remove(filepath)
                deleted_count += 1
            except Exception as e:
                st.sidebar.error(f"Erreur suppression {filename}: {e}")
    
    if deleted_count > 0:
        st.sidebar.success(f"✅ {deleted_count} fichier(s) supprimé(s)")
        st.cache_data.clear()
        st.sidebar.info("🔄 Rafraîchissez la page pour mettre à jour l'affichage")
    else:
        st.sidebar.info("ℹ️ Aucun dataset à supprimer")

st.sidebar.divider()

n_days = len(df_raw.columns)
st.sidebar.metric("Jours chargés", n_days)

n_hardest = st.sidebar.slider(
    "Nombre de jours difficiles à afficher", min_value=1, max_value=n_days, value=min(3, n_days)
)

all_students = sorted(df_raw.index.tolist())
selected_students = st.sidebar.multiselect(
    "Filtrer les étudiants",
    options=all_students,
    default=all_students,
    help="Sélectionne les étudiants à inclure dans les analyses.",
)

# Apply student filter
df = df_raw.loc[selected_students] if selected_students else df_raw

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("Pool Progression – Epitech")
st.caption(f"Analyse de {len(df)} étudiants sur {n_days} jours · B-DAT-200 Data Bootcamp")

# ── KPIs ──────────────────────────────────────────────────────────────────────
day_means = df.mean(axis=0)
student_means = df.mean(axis=1)
overall_avg = student_means.mean()
best_student = student_means.idxmax()
hardest_day = day_means.idxmin()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Étudiants actifs", len(df))
col2.metric("Moyenne globale", f"{overall_avg:.1f}%")
col3.metric("Meilleur étudiant", best_student.split("@")[0], f"{student_means[best_student]:.1f}%")
col4.metric("Jour le + difficile", hardest_day, f"{day_means[hardest_day]:.1f}%", delta_color="inverse")

st.divider()

# ── Section 1 – Class average progression ────────────────────────────────────
st.subheader("Progression moyenne de la promotion")

fig_avg = px.line(
    x=day_means.index,
    y=day_means.values,
    markers=True,
    labels={"x": "Jour", "y": "Moyenne (%)"},
    title="Score moyen par jour",
)
fig_avg.update_traces(line_color="#4C8BF5", line_width=3, marker_size=8)
fig_avg.update_yaxes(range=[0, 105], ticksuffix="%")
fig_avg.update_layout(hovermode="x unified")
st.plotly_chart(fig_avg, use_container_width=True)

st.divider()

# ── Section 2 – Individual student progression ────────────────────────────────
st.subheader("Progression individuelle")

selected_student = st.selectbox(
    "Choisir un étudiant",
    options=all_students,
    format_func=lambda x: x.split("@")[0],
)

student_row = df_raw.loc[selected_student]

fig_student = go.Figure()
fig_student.add_trace(
    go.Scatter(
        x=student_row.index,
        y=student_row.values,
        mode="lines+markers",
        name=selected_student.split("@")[0],
        line=dict(color="#F04E37", width=3),
        marker=dict(size=9),
    )
)
fig_student.add_trace(
    go.Scatter(
        x=day_means.index,
        y=day_means.values,
        mode="lines",
        name="Moyenne promo",
        line=dict(color="#4C8BF5", width=2, dash="dot"),
    )
)
fig_student.update_yaxes(range=[0, 105], ticksuffix="%")
fig_student.update_layout(
    title=f"Progression de {selected_student.split('@')[0]}",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_student, use_container_width=True)

# Mini-table of student scores
detail_df = pd.DataFrame({
    "Jour": student_row.index,
    "Score (%)": student_row.values,
}).set_index("Jour")
detail_df["Score (%)"] = detail_df["Score (%)"].map(lambda v: f"{v:.1f}%")
st.dataframe(detail_df.T, use_container_width=True)

st.divider()

# ── Section 3 – Hardest days ──────────────────────────────────────────────────
st.subheader(f"Top {n_hardest} jours les plus difficiles")

hardest = day_means.nsmallest(n_hardest).sort_values()
fig_hard = px.bar(
    x=hardest.index,
    y=hardest.values,
    labels={"x": "Jour", "y": "Moyenne (%)"},
    title=f"{n_hardest} jours avec les scores les plus bas",
    color=hardest.values,
    color_continuous_scale="Reds_r",
)
fig_hard.update_yaxes(range=[0, 105], ticksuffix="%")
fig_hard.update_coloraxes(showscale=False)
fig_hard.update_traces(text=[f"{v:.1f}%" for v in hardest.values], textposition="outside")
st.plotly_chart(fig_hard, use_container_width=True)

st.divider()

# ── Section 4 – Students below 50% average ───────────────────────────────────
st.subheader("Étudiants en difficulté (moyenne < 20%)")

at_risk = student_means[student_means < 20].sort_values()

if at_risk.empty:
    st.success("Aucun étudiant en dessous de 20% de moyenne.")
else:
    st.warning(f"{len(at_risk)} étudiant(s) sous la barre des 20%")

    fig_risk = px.bar(
        x=at_risk.index.str.split("@").str[0],
        y=at_risk.values,
        labels={"x": "Étudiant", "y": "Moyenne (%)"},
        title="Étudiants avec une moyenne générale < 20%",
        color=at_risk.values,
        color_continuous_scale="Reds_r",
    )
    fig_risk.add_hline(y=20, line_dash="dash", line_color="orange", annotation_text="20%")
    fig_risk.update_yaxes(range=[0, 105], ticksuffix="%")
    fig_risk.update_coloraxes(showscale=False)
    fig_risk.update_traces(text=[f"{v:.1f}%" for v in at_risk.values], textposition="outside")
    st.plotly_chart(fig_risk, use_container_width=True)

    # Detail table
    at_risk_df = df.loc[at_risk.index].copy()
    at_risk_df["Moyenne"] = at_risk
    at_risk_df = at_risk_df.sort_values("Moyenne")
    at_risk_df.index = at_risk_df.index.str.split("@").str[0]
    fmt_risk = {col: "{:.1f}%" for col in at_risk_df.columns}
    st.dataframe(
        at_risk_df.style.format(fmt_risk).background_gradient(cmap="Reds_r", subset=at_risk_df.columns),
        use_container_width=True,
    )

st.divider()

# ── Section 5 – Student leaderboard ──────────────────────────────────────────
st.subheader("Classement des étudiants")

leaderboard = df.copy()
leaderboard["Moyenne"] = leaderboard.mean(axis=1)
leaderboard = leaderboard.sort_values("Moyenne", ascending=False)
leaderboard.index = leaderboard.index.str.split("@").str[0]

# Format percentages
fmt = {col: "{:.1f}%" for col in leaderboard.columns}
st.dataframe(
    leaderboard.style.format(fmt).background_gradient(cmap="RdYlGn", subset=leaderboard.columns),
    use_container_width=True,
    height=600,
)
