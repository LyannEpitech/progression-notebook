"""Page de détection des comportements suspects."""

import streamlit as st
import pandas as pd

from src.core.detection import DetectionEngine
from src.ui.components.tables import SuspicionTable


class SuspiciousPage:
    """Page de détection des comportements suspects."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.engine = DetectionEngine(df)
    
    def render(self):
        """Affiche la page complète."""
        st.subheader("🔍 Détection des comportements suspects")
        
        # Paramètres de détection
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tolerance = st.slider(
                "Tolérance copiage",
                min_value=0.0,
                max_value=5.0,
                value=1.0,
                step=0.5,
                key="suspicion_tolerance"
            )
        
        with col2:
            min_days = st.slider(
                "Min jours similaires",
                min_value=2,
                max_value=10,
                value=4,
                key="suspicion_min_days"
            )
        
        with col3:
            min_ratio = st.slider(
                "Min ratio",
                min_value=0.1,
                max_value=1.0,
                value=0.4,
                step=0.1,
                key="suspicion_min_ratio"
            )
        
        # Lancer les détections
        from src.core.models import DetectionConfig
        config = DetectionConfig(
            copieur_tolerance=tolerance,
            copieur_min_days=min_days,
            copieur_min_ratio=min_ratio
        )
        
        self.engine = DetectionEngine(self.df, config)
        results = self.engine.detect_all()
        
        if not results:
            st.success("✅ Aucun comportement suspect détecté avec les paramètres actuels")
            return
        
        # Afficher les résultats par type
        tabs = st.tabs(["Copieurs", "Pics isolés", "Montagnes russes", "Copies collectives"])
        
        with tabs[0]:
            copieurs = [r for r in results if r.suspicion_type.value == "copieur"]
            if copieurs:
                df_copieurs = pd.DataFrame([{
                    'étudiant': r.student_id.split('@')[0],
                    'partenaire': r.details.get('partner', '').split('@')[0],
                    'jours similaires': r.details.get('similar_days', 0),
                    'consécutifs': r.details.get('max_consecutive', 0),
                    'score': r.score
                } for r in copieurs])
                SuspicionTable(df_copieurs, "Paires suspectes").render()
            else:
                st.info("Aucune paire de copieurs détectée")
        
        with tabs[1]:
            pics = [r for r in results if r.suspicion_type.value == "pic_isole"]
            if pics:
                df_pics = pd.DataFrame([{
                    'étudiant': r.student_id.split('@')[0],
                    'jour': r.details.get('day', ''),
                    'score': r.details.get('score', 0),
                    'contexte': r.details.get('contexte', ''),
                    'suspicion': r.score
                } for r in pics])
                SuspicionTable(df_pics, "Pics isolés").render()
            else:
                st.info("Aucun pic isolé détecté")
        
        with tabs[2]:
            montagnes = [r for r in results if r.suspicion_type.value == "montagnes_russes"]
            if montagnes:
                df_mont = pd.DataFrame([{
                    'étudiant': r.student_id.split('@')[0],
                    'alternances': r.details.get('alternances', 0),
                    'description': r.description,
                    'score': r.score
                } for r in montagnes])
                SuspicionTable(df_mont, "Montagnes russes").render()
            else:
                st.info("Aucun pattern de montagnes russes détecté")
        
        with tabs[3]:
            collectives = [r for r in results if r.suspicion_type.value == "copie_collective"]
            if collectives:
                df_coll = pd.DataFrame([{
                    'étudiant': r.student_id.split('@')[0],
                    'jour': r.details.get('day', ''),
                    'cluster': r.details.get('cluster_size', 0),
                    'score': r.score
                } for r in collectives])
                SuspicionTable(df_coll, "Copies collectives").render()
            else:
                st.info("Aucune copie collective détectée")
        
        # Score global par étudiant
        st.divider()
        st.subheader("🏆 Top suspects")
        
        suspicion_df = self.engine.calculate_suspicion_scores()
        if not suspicion_df.empty:
            st.dataframe(
                suspicion_df.head(10).reset_index().rename(columns={'index': 'étudiant'}),
                use_container_width=True
            )
