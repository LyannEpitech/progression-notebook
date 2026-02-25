import os
import re
import json
import math
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from hermes_api import load_data_from_api, sync_csv_from_api

st.set_page_config(page_title="Pool Progression – Epitech", page_icon="📊", layout="wide")

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "datasets")
CACHE_FILE = os.path.join(os.path.dirname(__file__), ".api_cache.json")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), ".dashboard_config.json")

# ============ NOUVELLES FONCTIONS DE DETECTION ============

def detect_copieurs(df, tolerance=1, min_days=4, min_ratio=0.4):
    """
    Detecte les paires d'etudiants avec des scores tres similaires sur plusieurs jours.
    Suspect si ≥3 jours avec |score_A - score_B| ≤ 2%, surtout si jours consecutifs.
    """
    if len(df) < 2:
        return pd.DataFrame()
    
    pairs = []
    students = df.index.tolist()
    
    for i in range(len(students)):
        for j in range(i+1, len(students)):
            s1, s2 = students[i], students[j]
            scores1, scores2 = df.loc[s1], df.loc[s2]
            
            # Jours avec scores similaires
            similar_days = []
            consecutive_streak = 0
            max_consecutive = 0
            last_similar = -1
            
            for idx, day in enumerate(df.columns):
                if abs(scores1[day] - scores2[day]) <= tolerance:
                    similar_days.append(day)
                    if last_similar == idx - 1:
                        consecutive_streak += 1
                    else:
                        consecutive_streak = 1
                    max_consecutive = max(max_consecutive, consecutive_streak)
                    last_similar = idx
            
            ratio = len(similar_days) / len(df.columns)
            
            if len(similar_days) >= min_days and ratio >= min_ratio:
                pairs.append({
                    'etudiant_1': s1,
                    'etudiant_2': s2,
                    'jours_similaires': len(similar_days),
                    'jours_consecutifs': max_consecutive,
                    'ratio': ratio,
                    'liste_jours': ', '.join(similar_days[:5]) + ('...' if len(similar_days) > 5 else '')
                })
    
    return pd.DataFrame(pairs)

def detect_pics_isoles(df, seuil_haut=70, seuil_bas=30, fenetre=2):
    """
    Detecte les pics isolés - un jour >70% entoure de jours <30%.
    Signe d'une aide ponctuelle exterieure.
    """
    suspects = []
    
    for student in df.index:
        scores = df.loc[student]
        
        for i, day in enumerate(df.columns):
            score = scores[day]
            
            # Verifier si c'est un pic haut
            if score < seuil_haut:
                continue
            
            # Calculer moyenne avant et apres
            avant = scores[max(0, i-fenetre):i]
            apres = scores[i+1:min(len(scores), i+1+fenetre)]
            
            moyenne_avant = avant.mean() if len(avant) > 0 else 100
            moyenne_apres = apres.mean() if len(apres) > 0 else 100
            
            # Suspect si entoure de mauvais scores
            if moyenne_avant < seuil_bas and moyenne_apres < seuil_bas:
                suspects.append({
                    'etudiant': student,
                    'jour': day,
                    'score': score,
                    'moyenne_avant': moyenne_avant,
                    'moyenne_apres': moyenne_apres,
                    'contexte': f"{moyenne_avant:.0f}% → **{score:.0f}%** → {moyenne_apres:.0f}%"
                })
    
    return pd.DataFrame(suspects)

def detect_montagnes_russes(df, seuil_variation=30):
    """
    Detecte les alternances rapides hausse/baisse >30%.
    Signe d'irrégularite artificielle (triche selective).
    """
    suspects = []
    
    for student in df.index:
        scores = df.loc[student].values
        alternances = 0
        details = []
        
        for i in range(1, len(scores)):
            diff = scores[i] - scores[i-1]
            
            if abs(diff) >= seuil_variation:
                # Compter comme alternance si direction change
                if i > 1:
                    prev_diff = scores[i-1] - scores[i-2]
                    if (diff > 0 and prev_diff < 0) or (diff < 0 and prev_diff > 0):
                        alternances += 1
                        details.append(f"{df.columns[i-2]}→{df.columns[i-1]}→{df.columns[i]}")
        
        if alternances >= 3:
            suspects.append({
                'etudiant': student,
                'alternances': alternances,
                'pattern': 'Montagnes russes',
                'details': details[:3]
            })
    
    return pd.DataFrame(suspects)

def detect_copies_collectives(df, tolerance=0, min_eleves=3, min_jours=2):
    """
    Detecte les clusters d'eleves avec exactement le meme score sur plusieurs jours.
    Signe d'une copie organisee a plusieurs.
    """
    clusters = []
    
    for day in df.columns:
        day_scores = df[day]
        
        # Grouper par score (arrondi a tolerance pres)
        rounded = day_scores.round(1) if tolerance == 0 else day_scores.round(0)
        value_counts = rounded.value_counts()
        
        for score, count in value_counts.items():
            if count >= min_eleves:
                eleves = day_scores[rounded == score].index.tolist()
                clusters.append({
                    'jour': day,
                    'score': score,
                    'nb_eleves': count,
                    'eleves': ', '.join([e.split('@')[0] for e in eleves[:5]]) + ('...' if len(eleves) > 5 else '')
                })
    
    df_clusters = pd.DataFrame(clusters)
    if df_clusters.empty:
        return df_clusters
    
    return df_clusters

def calculate_suspicion_score_v2(df):
    """
    Calcule un score global de suspicion avec les nouvelles heuristiques.
    """
    scores = {}
    
    # 1. Copieurs (plagiat de voisin) - pondere fort
    copieurs = detect_copieurs(df)
    for _, row in copieurs.iterrows():
        for student in [row['etudiant_1'], row['etudiant_2']]:
            scores[student] = scores.get(student, {'score': 0, 'raisons': []})
            bonus_consec = 2 if row['jours_consecutifs'] >= 2 else 0
            points = 4 + min(row['jours_similaires'] - 3, 3) + bonus_consec
            scores[student]['score'] += points
            other = row['etudiant_2'] if student == row['etudiant_1'] else row['etudiant_1']
            scores[student]['raisons'].append(
                f"Copieur: {row['jours_similaires']} jours similaires avec {other.split('@')[0]} "
                f"(dont {row['jours_consecutifs']} consecutifs)"
            )
    
    # 2. Pics isoles - pondere moyen
    pics = detect_pics_isoles(df)
    for _, row in pics.iterrows():
        student = row['etudiant']
        scores[student] = scores.get(student, {'score': 0, 'raisons': []})
        scores[student]['score'] += 6
        scores[student]['raisons'].append(f"Pic isole: {row['contexte']} sur {row['jour']}")
    
    # 3. Montagnes russes
    montagnes = detect_montagnes_russes(df)
    for _, row in montagnes.iterrows():
        student = row['etudiant']
        scores[student] = scores.get(student, {'score': 0, 'raisons': []})
        scores[student]['score'] += min(row['alternances'] * 1.5, 7)
        scores[student]['raisons'].append(f"Montagnes russes: {row['alternances']} alternances")
    
    # 4. Copies collectives - bonus si recidiviste
    copies = detect_copies_collectives(df)
    eleves_comptes = set()
    for _, row in copies.iterrows():
        # Extraire les logins complets
        for eleve_short in row['eleves'].replace('...', '').split(', '):
            eleve_short = eleve_short.strip()
            if not eleve_short:
                continue
            # Trouver le login complet
            for full_login in df.index:
                if full_login.startswith(eleve_short):
                    if full_login not in eleves_comptes:
                        scores[full_login] = scores.get(full_login, {'score': 0, 'raisons': []})
                        scores[full_login]['score'] += 2
                        scores[full_login]['raisons'].append(
                            f"Copie collective: meme score {row['score']:.0f}% sur {row['jour']} "
                            f"avec {row['nb_eleves']-1} autres"
                        )
                        eleves_comptes.add(full_login)
                    break
    
    if not scores:
        return pd.DataFrame()
    
    result = pd.DataFrame.from_dict(scores, orient='index')
    result = result.sort_values('score', ascending=False)
    return result

# ============ FONCTIONS UTILITAIRES ============

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
    """Sauvegarde les donnees API dans un fichier JSON."""
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
    """Charge les donnees API depuis le fichier JSON."""
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

# ============ INITIALISATION ============

if "df_raw" not in st.session_state:
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
    st.session_state.data_source = load_config()

st.sidebar.title("Source de donnees")

data_source = st.sidebar.radio(
    "Choisir la source",
    options=["CSV", "API", "Sync"],
    index=["CSV", "API", "Sync"].index(st.session_state.data_source),
    key="data_source_radio"
)

if data_source != st.session_state.data_source:
    st.session_state.data_source = data_source
    save_config(data_source)
    st.rerun()

# Mode API
if st.session_state.data_source == "API":
    st.sidebar.divider()
    st.sidebar.subheader("Config API")
    
    default_year = st.session_state.get("api_year", "2025")
    default_unit = st.session_state.get("api_unit", "B-DAT-200")
    default_instance = st.session_state.get("api_instance", "")
    
    api_year = st.sidebar.text_input("Annee", value=default_year)
    api_unit = st.sidebar.text_input("Unite", value=default_unit)
    api_instance = st.sidebar.text_input("Instance", value=default_instance)
    
    st.session_state.api_year = api_year
    st.session_state.api_unit = api_unit
    st.session_state.api_instance = api_instance
    
    if st.sidebar.button("Charger API", type="primary"):
        with st.spinner("Chargement..."):
            df = load_data_from_api(DATASETS_DIR, instance=api_instance or None, year=api_year, unit=api_unit)
        st.session_state.df_raw = df
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

# ============ AFFICHAGE PRINCIPAL ============

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
    unit_display = st.session_state.get('api_unit', 'B-DAT-200')
    st.caption(f"{unit_display} - Données Hermès API")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Etudiants", len(df_raw))
    col2.metric("Moyenne globale", f"{overall_avg:.1f}%")
    col3.metric("Meilleur", best_student.split("@")[0], f"{student_means[best_student]:.1f}%")
    col4.metric("Jour + difficile", hardest_day, f"{day_means[hardest_day]:.1f}%")
    
    st.divider()
    
    # Onglets pour organiser le contenu
    tab1, tab2, tab3 = st.tabs(["📈 Progression", "🕵️ Rendus suspects", "🏆 Classement"])
    
    # ============ ONGLET 1: PROGRESSION ============
    with tab1:
        # Progression moyenne
        st.subheader("Progression moyenne de la promotion")
        fig_avg = px.line(x=day_means.index, y=day_means.values, markers=True,
                          labels={"x": "Jour", "y": "Moyenne (%)"},
                          title="Score moyen par jour")
        fig_avg.update_traces(line_color="#4C8BF5", line_width=3, marker_size=8)
        fig_avg.update_yaxes(range=[0, 105], ticksuffix="%")
        fig_avg.update_layout(hovermode="x unified")
        st.plotly_chart(fig_avg, use_container_width=True)
        
        st.divider()
        
        # Progression individuelle
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
        
        detail_df = pd.DataFrame({"Jour": student_row.index, "Score (%)": student_row.values}).set_index("Jour")
        detail_df["Score (%)"] = detail_df["Score (%)"].map(lambda v: f"{v:.1f}%")
        st.dataframe(detail_df.T, use_container_width=True)
        
        st.divider()
        
        # Top 3 jours difficiles
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
        
        # Etudiants en difficulte
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
            
            at_risk_df = df_raw.loc[at_risk.index].copy()
            at_risk_df["Moyenne"] = at_risk
            at_risk_df = at_risk_df.sort_values("Moyenne")
            at_risk_df.index = at_risk_df.index.str.split("@").str[0]
            fmt_risk = {col: "{:.1f}%" for col in at_risk_df.columns}
            st.dataframe(at_risk_df.style.format(fmt_risk).background_gradient(cmap="Reds_r", subset=at_risk_df.columns),
                         use_container_width=True)
    
    # ============ ONGLET 2: RENDUS SUSPECTS (V2) ============
    with tab2:
        st.header("🕵️ Detection des rendus suspects")
        st.caption("Heuristiques optimisees pour detecter les vrais cas suspects")
        
        # Calculer les nouveaux scores
        suspicion_df = calculate_suspicion_score_v2(df_raw)
        
        if suspicion_df.empty:
            st.success("✅ Aucun comportement suspect detecte !")
        else:
            # Score global avec radar chart
            st.subheader("🏆 Top des etudiants suspects")
            st.caption("Score base sur les 4 indicateurs de triche")
            
            # Formatter le tableau des suspects
            suspicion_display = suspicion_df.copy()
            suspicion_display.index = suspicion_display.index.str.split("@").str[0]
            suspicion_display['badge'] = suspicion_display['score'].apply(
                lambda x: '🔴' if x >= 10 else ('🟠' if x >= 6 else '🟡')
            )
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Liste des suspects avec radar individuel
                for student, row in suspicion_display.head(8).iterrows():
                    with st.expander(f"{row['badge']} {student} – Score: {row['score']:.1f}"):
                        for raison in row['raisons']:
                            st.write(f"• {raison}")
                        
                        # Radar individuel
                        full_login = None
                        for login in suspicion_df.index:
                            if login.startswith(student):
                                full_login = login
                                break
                        
                        if full_login and full_login in suspicion_df.index:
                            s_row = suspicion_df.loc[full_login]
                            categories = ['Copieurs', 'Pics', 'Montagnes', 'Collectif']
                            values = [s_row.get('copieurs', 0), s_row.get('pics', 0),
                                     s_row.get('montagnes', 0), s_row.get('collectif', 0)]
                            
                            fig_indiv = go.Figure()
                            fig_indiv.add_trace(go.Scatterpolar(
                                r=values + [values[0]], theta=categories + [categories[0]],
                                fill='toself', fillcolor='rgba(255,0,0,0.3)',
                                line=dict(color='red', width=2)))
                            fig_indiv.update_layout(
                                polar=dict(radialaxis=dict(visible=True, range=[0, max(values) * 1.5 or 10])),
                                height=300, margin=dict(l=40, r=40, t=40, b=40)
                            )
                            st.plotly_chart(fig_indiv, use_container_width=True, key=f"radar_{student}")
            
            with col2:
                # 🎯 Graphique en barres des scores
                fig_scores = px.bar(
                    x=suspicion_display.head(8).index,
                    y=suspicion_display.head(8)['score'],
                    color=suspicion_display.head(8)['score'],
                    color_continuous_scale='Reds',
                    labels={'x': 'Etudiant', 'y': 'Score de suspicion'},
                    title="Scores de suspicion"
                )
                fig_scores.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_scores, use_container_width=True)
            
            # 🎯 Radar chart comparatif du top 5
            st.subheader("🎯 Profils comparés (Radar)")
            top5 = suspicion_df.head(5)
            categories = ['Copieurs', 'Pics', 'Montagnes', 'Collectif']
            colors = px.colors.qualitative.Set1
            
            fig_radar = go.Figure()
            for i, (student, row) in enumerate(top5.iterrows()):
                values = [row.get('copieurs', 0), row.get('pics', 0), 
                         row.get('montagnes', 0), row.get('collectif', 0)]
                fig_radar.add_trace(go.Scatterpolar(
                    r=values + [values[0]], theta=categories + [categories[0]],
                    fill='toself', name=student.split('@')[0],
                    line=dict(color=colors[i % len(colors)])))
            
            max_val = max([row.get('copieurs', 0) + row.get('pics', 0) + row.get('montagnes', 0) + row.get('collectif', 0) for _, row in top5.iterrows()]) or 10
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, max_val * 1.2])),
                height=500, legend=dict(orientation="h", y=-0.2)
            )
            st.plotly_chart(fig_radar, use_container_width=True)
            
            # ⏱️ Timeline des suspects
            st.subheader("⏱️ Timeline des scores (Top 5 suspects)")
            fig_timeline = go.Figure()
            top5_students = suspicion_df.head(5).index.tolist()
            
            for i, student in enumerate(top5_students):
                scores = df_raw.loc[student]
                fig_timeline.add_trace(go.Scatter(
                    x=scores.index, y=scores.values, mode='lines+markers',
                    name=student.split('@')[0],
                    line=dict(width=3), marker=dict(size=8)))
            
            fig_timeline.update_layout(
                yaxis=dict(range=[0, 105], ticksuffix="%"),
                hovermode="x unified", height=400
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            st.divider()
            
            # Section 1: Copieurs
            st.subheader("🔗 Copieurs (scores similaires sur plusieurs jours)")
            st.caption("Detecte les eleves cote-a-cote avec memes scores (±1%)")
            copieurs = detect_copieurs(df_raw)
            
            if copieurs.empty:
                st.info("Aucune paire suspecte detectee")
            else:
                st.write(f"{len(copieurs)} paire(s) suspecte(s)")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # 🔥 Heatmap des differences
                    involved_students = list(set(copieurs['etudiant_1'].tolist() + copieurs['etudiant_2'].tolist()))
                    if len(involved_students) > 1:
                        diff_matrix = pd.DataFrame(index=involved_students, columns=involved_students)
                        for s1 in involved_students:
                            for s2 in involved_students:
                                if s1 == s2:
                                    diff_matrix.loc[s1, s2] = 0
                                else:
                                    diff_matrix.loc[s1, s2] = (df_raw.loc[s1] - df_raw.loc[s2]).abs().mean()
                        
                        diff_matrix.index = [s.split('@')[0] for s in diff_matrix.index]
                        diff_matrix.columns = [s.split('@')[0] for s in diff_matrix.columns]
                        
                        fig_heat = px.imshow(
                            diff_matrix.astype(float),
                            color_continuous_scale='RdYlGn_r',
                            range_color=[0, 10],
                            title="Heatmap des differences moyennes (%)"
                        )
                        fig_heat.update_layout(height=400)
                        st.plotly_chart(fig_heat, use_container_width=True)
                
                with col2:
                    # 🕸️ Graphe de reseau des connexions
                    if len(copieurs) > 0:
                        fig_network = go.Figure()
                        
                        # Position circulaire
                        import math
                        students_unique = list(set(copieurs['etudiant_1'].tolist() + copieurs['etudiant_2'].tolist()))
                        n_students = len(students_unique)
                        
                        positions = {}
                        for i, student in enumerate(students_unique):
                            angle = 2 * math.pi * i / n_students
                            positions[student] = (math.cos(angle) * 2, math.sin(angle) * 2)
                        
                        # Lignes de connexion
                        for _, row in copieurs.iterrows():
                            s1, s2 = row['etudiant_1'], row['etudiant_2']
                            x0, y0 = positions[s1]
                            x1, y1 = positions[s2]
                            
                            # Epaisseur selon le nombre de jours similaires
                            width = min(row['jours_similaires'] / 2, 4)
                            
                            fig_network.add_trace(go.Scatter(
                                x=[x0, x1, None], y=[y0, y1, None],
                                mode='lines',
                                line=dict(color='rgba(255,0,0,0.4)', width=width),
                                hoverinfo='skip',
                                showlegend=False
                            ))
                        
                        # Points des eleves
                        x_nodes = [positions[s][0] for s in students_unique]
                        y_nodes = [positions[s][1] for s in students_unique]
                        labels = [s.split('@')[0] for s in students_unique]
                        
                        fig_network.add_trace(go.Scatter(
                            x=x_nodes, y=y_nodes,
                            mode='markers+text',
                            marker=dict(size=20, color='darkred', line=dict(color='white', width=2)),
                            text=labels,
                            textposition='top center',
                            hoverinfo='text'
                        ))
                        
                        fig_network.update_layout(
                            title="Reseau des connexions suspectes",
                            showlegend=False,
                            height=400,
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_network, use_container_width=True)
                
                # Tableau detaille
                cop_display = copieurs.copy()
                cop_display['etudiant_1'] = cop_display['etudiant_1'].str.split('@').str[0]
                cop_display['etudiant_2'] = cop_display['etudiant_2'].str.split('@').str[0]
                cop_display['ratio'] = cop_display['ratio'].apply(lambda x: f"{x*100:.0f}%")
                st.dataframe(cop_display[['etudiant_1', 'etudiant_2', 'jours_similaires', 'jours_consecutifs', 'ratio', 'liste_jours']], use_container_width=True)
            
            st.divider()
            
            st.divider()
            
            # Section 2: Pics isoles
            st.subheader("📍 Pics isoles (aide ponctuelle)")
            st.caption("Detecte les jours >70% entoures de jours <30%")
            pics = detect_pics_isoles(df_raw)
            
            if pics.empty:
                st.info("Aucun pic isole detecte")
            else:
                st.write(f"{len(pics)} pic(s) isole(s) detecte(s)")
                
                # Nettoyer les NaN pour le graphique
                pics_clean = pics.copy()
                pics_clean = pics_clean.fillna(0)
                
                # 📊 Bubble chart des pics
                fig_bubble = px.scatter(
                    pics_clean,
                    x='jour',
                    y='score',
                    size='score',
                    color='moyenne_avant',
                    hover_data=['etudiant', 'moyenne_apres'],
                    labels={'score': 'Score du pic (%)', 'jour': 'Jour', 'moyenne_avant': 'Moyenne avant'},
                    title="Carte des pics suspects (taille = intensite)",
                    color_continuous_scale='RdYlBu_r',
                    range_color=[0, 50]
                )
                fig_bubble.update_yaxes(range=[0, 105], ticksuffix="%")
                fig_bubble.add_hline(y=70, line_dash="dash", line_color="green", annotation_text="Seuil 70%")
                st.plotly_chart(fig_bubble, use_container_width=True)
                
                # Graphique d'evolution individuelle
                fig_pics = go.Figure()
                colors = px.colors.qualitative.Set1
                for i, (_, row) in enumerate(pics.iterrows()):
                    fig_pics.add_trace(go.Scatter(
                        x=['Avant', 'Jour suspect', 'Apres'],
                        y=[row['moyenne_avant'], row['score'], row['moyenne_apres']],
                        mode='lines+markers',
                        name=row['etudiant'].split('@')[0],
                        line=dict(width=3, color=colors[i % len(colors)]),
                        marker=dict(size=12),
                        text=f"{row['etudiant'].split('@')[0]} ({row['jour']})",
                        hoverinfo='text+y'
                    ))
                
                fig_pics.add_hline(y=70, line_dash="dash", line_color="green", opacity=0.5)
                fig_pics.add_hline(y=30, line_dash="dash", line_color="red", opacity=0.5)
                fig_pics.update_layout(
                    title="Evolution autour des pics suspects",
                    yaxis=dict(range=[0, 105], ticksuffix="%"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02)
                )
                st.plotly_chart(fig_pics, use_container_width=True)
                
                # Tableau
                pics_display = pics.copy()
                pics_display['etudiant'] = pics_display['etudiant'].str.split('@').str[0]
                pics_display['score'] = pics_display['score'].apply(lambda x: f"{x:.1f}%")
                st.dataframe(pics_display[['etudiant', 'jour', 'score', 'contexte']], use_container_width=True)
            
            st.divider()
            
            st.divider()
            
            # Section 3: Montagnes russes
            st.subheader("🎢 Montagnes russes (irrégularite artificielle)")
            st.caption("Detecte les alternances hausse/baisse >30%")
            montagnes = detect_montagnes_russes(df_raw)
            
            if montagnes.empty:
                st.info("Aucune montagne russe detectee")
            else:
                st.write(f"{len(montagnes)} etudiant(s) avec pattern suspect")
                
                # 📈 Graphique compare
                fig_mont = go.Figure()
                colors = px.colors.qualitative.Bold
                
                for i, (_, row) in enumerate(montagnes.head(5).iterrows()):
                    scores = df_raw.loc[row['etudiant']]
                    
                    fig_mont.add_trace(go.Scatter(
                        x=scores.index,
                        y=scores.values,
                        mode='lines+markers',
                        name=row['etudiant'].split('@')[0],
                        line=dict(width=2, color=colors[i % len(colors)]),
                        marker=dict(size=8)
                    ))
                    
                    # Marquer les alternances
                    scores_vals = scores.values
                    for j in range(2, len(scores_vals)):
                        diff1 = scores_vals[j-1] - scores_vals[j-2]
                        diff2 = scores_vals[j] - scores_vals[j-1]
                        if abs(diff1) >= 30 and abs(diff2) >= 30 and ((diff1 > 0 and diff2 < 0) or (diff1 < 0 and diff2 > 0)):
                            fig_mont.add_trace(go.Scatter(
                                x=[scores.index[j-1]],
                                y=[scores_vals[j-1]],
                                mode='markers',
                                marker=dict(size=15, color=colors[i % len(colors)], symbol='star'),
                                showlegend=False,
                                hoverinfo='skip'
                            ))
                
                fig_mont.update_layout(
                    title="Progressions avec alternances marquantes (★ = alternance)",
                    yaxis=dict(range=[0, 105], ticksuffix="%"),
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02)
                )
                st.plotly_chart(fig_mont, use_container_width=True)
                
                # Liste detaillee
                for _, row in montagnes.head(5).iterrows():
                    with st.expander(f"{row['etudiant'].split('@')[0]} – {row['alternances']} alternances"):
                        st.write("Patterns detectes:")
                        for detail in row['details']:
                            st.write(f"• {detail}")
            
            st.divider()
            
            st.divider()
            
            # Section 4: Copies collectives
            st.subheader("👥 Copies collectives (memes scores a plusieurs)")
            st.caption("Detecte les clusters d'eleves avec exactement le meme score")
            copies = detect_copies_collectives(df_raw)
            
            if copies.empty:
                st.info("Aucune copie collective detectee")
            else:
                st.write(f"{len(copies)} cluster(s) detecte(s)")
                
                # 📊 Bar chart des clusters par jour
                clusters_per_day = copies.groupby('jour').size().reset_index(name='nb_clusters')
                
                fig_clust = px.bar(
                    clusters_per_day,
                    x='jour',
                    y='nb_clusters',
                    color='nb_clusters',
                    color_continuous_scale='Reds',
                    labels={'jour': 'Jour', 'nb_clusters': 'Nombre de clusters'},
                    title="Clusters suspects par jour"
                )
                st.plotly_chart(fig_clust, use_container_width=True)
                
                # 🎯 Treemap des clusters (taille = nombre d'eleves)
                fig_tree = px.treemap(
                    copies,
                    path=['jour', 'score'],
                    values='nb_eleves',
                    color='nb_eleves',
                    color_continuous_scale='Reds',
                    title="Taille des clusters (eleves avec meme score)"
                )
                st.plotly_chart(fig_tree, use_container_width=True)
                
                # Afficher par jour
                for jour in copies['jour'].unique():
                    jour_data = copies[copies['jour'] == jour]
                    with st.expander(f"{jour} – {len(jour_data)} groupe(s)"):
                        for _, row in jour_data.iterrows():
                            st.write(f"**Score {row['score']:.1f}%**: {row['eleves']}")
                
                # Tableau complet
                copies_display = copies.copy()
                copies_display['score'] = copies_display['score'].apply(lambda x: f"{x:.1f}%")
                st.dataframe(copies_display[['jour', 'score', 'nb_eleves', 'eleves']], use_container_width=True)
    
    # ============ ONGLET 3: CLASSEMENT ============
    with tab3:
        st.subheader("Classement complet des etudiants")
        leaderboard = df_raw.copy()
        leaderboard["Moyenne"] = leaderboard.mean(axis=1)
        leaderboard = leaderboard.sort_values("Moyenne", ascending=False)
        leaderboard.index = leaderboard.index.str.split("@").str[0]
        
        fmt = {col: "{:.1f}%" for col in leaderboard.columns}
        st.dataframe(leaderboard.style.format(fmt).background_gradient(cmap="RdYlGn", subset=leaderboard.columns),
                     use_container_width=True, height=600)
