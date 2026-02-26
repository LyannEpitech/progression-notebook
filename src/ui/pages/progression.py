"""Page d'affichage de la progression."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

from src.ui.components.charts import LineChart, HeatmapChart


class ProgressionPage:
    """Page d'affichage de la progression des étudiants."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.day_means = df.mean(axis=0)
        self.student_means = df.mean(axis=1)
        self.n_days = len(df.columns)
    
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
        
        # Détail du tableau
        detail_df = pd.DataFrame({
            "Jour": student_row.index,
            "Score (%)": student_row.values
        }).set_index("Jour")
        detail_df["Score (%)"] = detail_df["Score (%)"].map(lambda v: f"{v:.1f}%")
        st.dataframe(detail_df.T, use_container_width=True)
        
        st.divider()
        
        # Top 3 jours les plus difficiles
        st.subheader("Top 3 jours les plus difficiles")
        n_hardest = min(3, self.n_days)
        hardest = self.day_means.nsmallest(n_hardest).sort_values()
        fig_hard = px.bar(
            x=hardest.index, y=hardest.values,
            labels={"x": "Jour", "y": "Moyenne (%)"},
            title=f"{n_hardest} jours avec les scores les plus bas",
            color=hardest.values, color_continuous_scale="Reds_r"
        )
        fig_hard.update_yaxes(range=[0, 105], ticksuffix="%")
        fig_hard.update_coloraxes(showscale=False)
        fig_hard.update_traces(text=[f"{v:.1f}%" for v in hardest.values], textposition="outside")
        st.plotly_chart(fig_hard, use_container_width=True)
        
        st.divider()
        
        # Étudiants en difficulté
        st.subheader("Étudiants en difficulté (moyenne < 20%)")
        at_risk = self.student_means[self.student_means < 20].sort_values()
        
        if at_risk.empty:
            st.success("Aucun étudiant en dessous de 20% de moyenne.")
        else:
            st.warning(f"{len(at_risk)} étudiant(s) sous la barre des 20%")
            
            fig_risk = px.bar(
                x=at_risk.index.str.split("@").str[0], y=at_risk.values,
                labels={"x": "Étudiant", "y": "Moyenne (%)"},
                title="Étudiants avec une moyenne générale < 20%",
                color=at_risk.values, color_continuous_scale="Reds_r"
            )
            fig_risk.add_hline(y=20, line_dash="dash", line_color="orange", annotation_text="20%")
            fig_risk.update_yaxes(range=[0, 105], ticksuffix="%")
            fig_risk.update_coloraxes(showscale=False)
            fig_risk.update_traces(text=[f"{v:.1f}%" for v in at_risk.values], textposition="outside")
            st.plotly_chart(fig_risk, use_container_width=True)
            
            at_risk_df = self.df.loc[at_risk.index].copy()
            at_risk_df["Moyenne"] = at_risk
            at_risk_df = at_risk_df.sort_values("Moyenne")
            at_risk_df.index = at_risk_df.index.str.split("@").str[0]
            fmt_risk = {col: "{:.1f}%" for col in at_risk_df.columns}
            st.dataframe(
                at_risk_df.style.format(fmt_risk).background_gradient(cmap="Reds_r", subset=at_risk_df.columns),
                use_container_width=True
            )
        
        st.divider()
        
        # Carte de chaleur
        st.subheader("Vue d'ensemble (heatmap)")
        heatmap = HeatmapChart(
            data=self.df,
            title="Scores par étudiant et par jour"
        )
        heatmap.render()
