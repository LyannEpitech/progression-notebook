"""Page de classement des étudiants."""

import streamlit as st
import pandas as pd

from src.core.scoring import ScoringEngine


class RankingPage:
    """Page de classement et statistiques."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.engine = ScoringEngine(df)
    
    def render(self):
        """Affiche la page complète."""
        st.subheader("🏆 Classement des étudiants")
        
        # Classement complet
        leaderboard = self.engine.get_leaderboard()
        
        # Renommer les colonnes pour affichage
        display_cols = {
            'student_id': 'Email',
            'display_name': 'Nom',
            'global_score': 'Score global',
            'average': 'Moyenne',
            'trend': 'Tendance',
            'regularity': 'Régularité',
            'min': 'Min',
            'max': 'Max'
        }
        
        leaderboard_display = leaderboard.rename(columns=display_cols)
        
        # Sélectionner les colonnes à afficher
        cols_to_show = ['Nom', 'Score global', 'Moyenne', 'Tendance', 'Régularité']
        st.dataframe(
            leaderboard_display[cols_to_show],
            use_container_width=True,
            height=400
        )
        
        st.divider()
        
        # Statistiques de la classe
        st.subheader("📊 Statistiques de la classe")
        
        stats = self.engine.calculate_class_stats()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Moyenne de classe", f"{stats['class_average']:.1f}%")
            st.metric("Meilleur étudiant", stats['best_student'].split('@')[0])
        
        with col2:
            st.metric("Écart-type", f"{stats['class_std']:.1f}")
            st.metric("Meilleur score", f"{stats['best_score']:.1f}%")
        
        with col3:
            st.metric("Jour + difficile", stats['hardest_day'])
            st.metric("Score jour difficile", f"{stats['hardest_day_score']:.1f}%")
        
        # Export
        st.divider()
        st.subheader("📥 Export")
        
        csv = leaderboard.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Télécharger le classement (CSV)",
            data=csv,
            file_name='classement.csv',
            mime='text/csv'
        )
