"""Application principale Streamlit."""

import os
import sys
import json
import streamlit as st
import pandas as pd

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.data.loaders import CSVLoader, APILoader
from src.api.activities import ActivitiesAPI
from src.api.client import HermesClient

# Configuration de la page
st.set_page_config(
    page_title="Pool Progression – Epitech",
    page_icon="📊",
    layout="wide"
)

# Constantes
DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets")
CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".api_cache.json")


def load_cache():
    """Charge les données depuis le cache."""
    if not os.path.exists(CACHE_FILE):
        return pd.DataFrame(), None, None, None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        df = pd.DataFrame.from_dict(cache_data["data"], orient="index")
        df = df.reindex(columns=cache_data["columns"])
        df.index.name = "login"
        return (
            df,
            cache_data.get("year"),
            cache_data.get("unit"),
            cache_data.get("instance")
        )
    except Exception:
        return pd.DataFrame(), None, None, None


def save_cache(df: pd.DataFrame, year: str, unit: str, instance: str):
    """Sauvegarde les données dans le cache."""
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


def clear_cache():
    """Vide le cache."""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)


def sidebar():
    """Affiche la sidebar et retourne les paramètres."""
    st.sidebar.title("📊 Pool Progression")
    st.sidebar.divider()
    
    # Source de données
    st.sidebar.subheader("Source de données")
    
    data_source = st.sidebar.radio(
        "Choisir la source",
        options=["CSV", "API"],
        index=0,
        key="data_source_radio"
    )
    
    df = pd.DataFrame()
    
    if data_source == "CSV":
        loader = CSVLoader(DATASETS_DIR)
        df = loader.load()
        if not df.empty:
            st.sidebar.success(f"✅ {len(df)} étudiants chargés")
    
    elif data_source == "API":
        st.sidebar.divider()
        st.sidebar.subheader("Configuration API")
        
        # Configuration locale (sans besoin de PAT/PAT_ID)
        AVAILABLE_YEARS = ["2024", "2025", "2026", "2027", "2028"]
        KNOWN_UNITS = [
            "B-DAT-200", "B-WEB-100", "B-CPP-100", "B-MUL-100",
            "B-MAT-100", "B-COM-100", "B-ANG-100", "B-PRO-100",
            "B-SYS-100", "B-SEC-100", "B-AIA-100", "B-PSU-100",
            "B-DAT-201", "B-WEB-201", "B-CPP-201", "B-DAT-300",
        ]
        
        # Sélection de l'année
        api_year = st.sidebar.selectbox(
            "Année",
            options=AVAILABLE_YEARS,
            index=1,  # 2025 par défaut
            key="api_year_select"
        )
        
        # Récupérer les units disponibles (lazy - seulement si PAT/PAT_ID sont définis)
        @st.cache_data(ttl=300)
        def fetch_units(year):
            try:
                from src.api.activities import ActivitiesAPI
                activities_api = ActivitiesAPI()
                return activities_api.list_available_units(year)
            except Exception:
                return []
        
        # Vérifier si les credentials sont disponibles
        if os.getenv('PAT') and os.getenv('PAT_ID'):
            available_units = fetch_units(api_year)
            if not available_units:
                available_units = KNOWN_UNITS
                st.sidebar.caption("⚠️ Mode hors ligne - liste complète")
            else:
                st.sidebar.caption(f"✅ {len(available_units)} units disponibles")
        else:
            available_units = KNOWN_UNITS
            st.sidebar.caption("⚠️ Mode hors ligne - PAT/PAT_ID non définis")
        
        # Sélection de l'unit
        api_unit = st.sidebar.selectbox(
            "Unité",
            options=available_units,
            index=0 if available_units else None,
            key="api_unit_select"
        )
        
        # Instance optionnelle
        api_instance = st.sidebar.text_input(
            "Instance (optionnel)",
            placeholder="MPL-1-1, PAR-1-1...",
            key="api_instance_input"
        )
        
        # Charger ou utiliser le cache
        cached_df, cached_year, cached_unit, cached_instance = load_cache()
        
        # Vérifier si les credentials sont définis avant de permettre le chargement API
        has_credentials = os.getenv('PAT') and os.getenv('PAT_ID')
        
        if st.sidebar.button("🔄 Charger depuis l'API", type="primary", disabled=not has_credentials):
            if not has_credentials:
                st.sidebar.error("❌ PAT et PAT_ID doivent être définis dans .env")
            else:
                with st.spinner("Chargement..."):
                    try:
                        loader = APILoader(
                            year=api_year,
                            unit=api_unit,
                            instance=api_instance or None
                        )
                        df = loader.load()
                        if not df.empty:
                            save_cache(df, api_year, api_unit, api_instance)
                            st.sidebar.success(f"✅ {len(df)} étudiants chargés")
                            st.rerun()
                    except Exception as e:
                        st.sidebar.error(f"❌ Erreur: {str(e)}")
        elif not cached_df.empty:
            df = cached_df
            st.sidebar.info(f"💾 Cache: {len(df)} étudiants ({cached_unit})")
        
        if st.sidebar.button("🗑️ Vider le cache", type="secondary"):
            clear_cache()
            st.cache_data.clear()
            st.rerun()
    
    return df


def main():
    """Point d'entrée principal."""
    # Chargement des données
    df = sidebar()
    
    if df.empty:
        st.title("📊 Pool Progression – Epitech")
        st.info("👈 Sélectionnez une source de données dans la sidebar")
        return
    
    # KPIs
    n_days = len(df.columns)
    day_means = df.mean(axis=0)
    student_means = df.mean(axis=1)
    overall_avg = student_means.mean()
    best_student = student_means.idxmax()
    hardest_day = day_means.idxmin()
    
    st.title(f"📊 Pool Progression – {len(df)} étudiants sur {n_days} jours")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Étudiants", len(df))
    col2.metric("Moyenne globale", f"{overall_avg:.1f}%")
    col3.metric("Meilleur", best_student.split("@")[0], f"{student_means[best_student]:.1f}%")
    col4.metric("Jour + difficile", hardest_day, f"{day_means[hardest_day]:.1f}%")
    
    st.divider()
    
    # Onglets
    from src.ui.pages.progression import ProgressionPage
    from src.ui.pages.suspicious import SuspiciousPage
    from src.ui.pages.ranking import RankingPage
    
    tab1, tab2, tab3 = st.tabs(["📈 Progression", "🕵️ Rendus suspects", "🏆 Classement"])
    
    with tab1:
        ProgressionPage(df).render()
    
    with tab2:
        SuspiciousPage(df).render()
    
    with tab3:
        RankingPage(df).render()


if __name__ == "__main__":
    main()
