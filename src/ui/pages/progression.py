"""Page d'affichage de la progression."""

import streamlit as st
import pandas as pd
from typing import Optional

from src.ui.components.charts import LineChart, HeatmapChart


class ProgressionPage:
    """Page d'affichage de la progression des étudiants."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.day_means = df.mean(axis=0)
        self.student_means = df.mean(axis=1)
    
    def render(self):
        """Affiche la page complète."""
        st.subheader("Progression moyenne de la promotion")
        
        # Graphique de la moyenne
        chart = LineChart(
            data=self.day_means,
            title="Score moyen par jour",
            x_label="Jour",
            y_label="Moyenne (%)"
        )
        chart.render()
        
        st.divider()
        
        # Progression individuelle
        st.subheader("Progression individuelle")
        all_students = sorted(self.df.index.tolist())
        selected_student = st.selectbox(
            "Choisir un étudiant",
            options=all_students,
            format_func=lambda x: x.split("@")[0],
            key="progression_student_select"
        )
        
        student_row = self.df.loc[selected_student]
        
        chart_indiv = LineChart(
            data=student_row,
            title=f"Progression de {selected_student.split('@')[0]}",
            x_label="Jour",
            y_label="Score (%)",
            color="#F04E37",
            secondary_line=self.day_means
        )
        chart_indiv.render()
        
        # Carte de chaleur
        st.divider()
        st.subheader("Vue d'ensemble (heatmap)")
        heatmap = HeatmapChart(
            data=self.df,
            title="Scores par étudiant et par jour"
        )
        heatmap.render()
