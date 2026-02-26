"""Page de détection des comportements suspects."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math

from src.core.detection import DetectionEngine, detect_copieurs, detect_pics_isoles, detect_montagnes_russes
from src.ui.components.tables import SuspicionTable
from src.core.models import DetectionConfig


class SuspiciousPage:
    """Page de détection des comportements suspects."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.engine = DetectionEngine(df)
    
    def render(self):
        """Affiche la page complète."""
        st.header("🕵️ Détection des rendus suspects")
        st.caption("Heuristiques optimisées pour détecter les vrais cas suspects")
        
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
        
        # Calculer les scores avec la config
        config = DetectionConfig(
            copieur_tolerance=tolerance,
            copieur_min_days=min_days,
            copieur_min_ratio=min_ratio
        )
        
        self.engine = DetectionEngine(self.df, config)
        suspicion_df = self.engine.calculate_suspicion_scores()
        
        if suspicion_df.empty:
            st.success("✅ Aucun comportement suspect détecté avec les paramètres actuels")
            return
        
        # Score global avec radar chart
        st.subheader("🏆 Top des étudiants suspects")
        st.caption("Score basé sur les 4 indicateurs de triche")
        
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
            # Graphique en barres des scores
            fig_scores = px.bar(
                x=suspicion_display.head(8).index,
                y=suspicion_display.head(8)['score'],
                color=suspicion_display.head(8)['score'],
                color_continuous_scale='Reds',
                labels={'x': 'Étudiant', 'y': 'Score de suspicion'},
                title="Scores de suspicion"
            )
            fig_scores.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_scores, use_container_width=True)
        
        # Radar chart comparatif du top 5
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
        
        # Timeline des suspects
        st.subheader("⏱️ Timeline des scores (Top 5 suspects)")
        fig_timeline = go.Figure()
        top5_students = suspicion_df.head(5).index.tolist()
        
        for i, student in enumerate(top5_students):
            scores = self.df.loc[student]
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
        st.caption("Détecte les élèves côte-à-côte avec mêmes scores (±1%)")
        copieurs = detect_copieurs(self.df, tolerance=tolerance, min_days=min_days, min_ratio=min_ratio)
        
        if copieurs.empty:
            st.info("Aucune paire suspecte détectée")
        else:
            st.write(f"{len(copieurs)} paire(s) suspecte(s)")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Heatmap des différences
                involved_students = list(set(copieurs['etudiant_1'].tolist() + copieurs['etudiant_2'].tolist()))
                if len(involved_students) > 1:
                    diff_matrix = pd.DataFrame(index=involved_students, columns=involved_students)
                    for s1 in involved_students:
                        for s2 in involved_students:
                            if s1 == s2:
                                diff_matrix.loc[s1, s2] = 0
                            else:
                                diff_matrix.loc[s1, s2] = (self.df.loc[s1] - self.df.loc[s2]).abs().mean()
                    
                    diff_matrix.index = [s.split('@')[0] for s in diff_matrix.index]
                    diff_matrix.columns = [s.split('@')[0] for s in diff_matrix.columns]
                    
                    fig_heat = px.imshow(
                        diff_matrix.astype(float),
                        color_continuous_scale='RdYlGn_r',
                        range_color=[0, 10],
                        title="Heatmap des différences moyennes (%)"
                    )
                    fig_heat.update_layout(height=400)
                    st.plotly_chart(fig_heat, use_container_width=True)
            
            with col2:
                # Graphe de réseau des connexions
                if len(copieurs) > 0:
                    fig_network = go.Figure()
                    
                    # Position circulaire
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
                        
                        # Épaisseur selon le nombre de jours similaires
                        width = min(row['jours_similaires'] / 2, 4)
                        
                        fig_network.add_trace(go.Scatter(
                            x=[x0, x1, None], y=[y0, y1, None],
                            mode='lines',
                            line=dict(color='rgba(255,0,0,0.4)', width=width),
                            hoverinfo='skip',
                            showlegend=False
                        ))
                    
                    # Points des élèves
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
                        title="Réseau des connexions suspectes",
                        showlegend=False,
                        height=400,
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_network, use_container_width=True)
            
            # Tableau détaillé
            cop_display = copieurs.copy()
            cop_display['etudiant_1'] = cop_display['etudiant_1'].str.split('@').str[0]
            cop_display['etudiant_2'] = cop_display['etudiant_2'].str.split('@').str[0]
            cop_display['ratio'] = cop_display['ratio'].apply(lambda x: f"{x*100:.0f}%")
            st.dataframe(cop_display[['etudiant_1', 'etudiant_2', 'jours_similaires', 'jours_consecutifs', 'ratio', 'liste_jours']], use_container_width=True)
        
        st.divider()
        
        # Section 2: Pics isolés
        st.subheader("📍 Pics isolés (aide ponctuelle)")
        st.caption("Détecte les jours >70% entourés de jours <30%")
        pics = detect_pics_isoles(self.df)
        
        if pics.empty:
            st.info("Aucun pic isolé détecté")
        else:
            st.write(f"{len(pics)} pic(s) isolé(s) détecté(s)")
            
            # Nettoyer les NaN pour le graphique
            pics_clean = pics.copy()
            pics_clean = pics_clean.fillna(0)
            
            # Bubble chart des pics
            fig_bubble = px.scatter(
                pics_clean,
                x='jour',
                y='score',
                size='score',
                color='moyenne_avant',
                hover_data=['etudiant', 'moyenne_apres'],
                labels={'score': 'Score du pic (%)', 'jour': 'Jour', 'moyenne_avant': 'Moyenne avant'},
                title="Carte des pics suspects (taille = intensité)",
                color_continuous_scale='RdYlBu_r',
                range_color=[0, 50]
            )
            fig_bubble.update_yaxes(range=[0, 105], ticksuffix="%")
            fig_bubble.add_hline(y=70, line_dash="dash", line_color="green", annotation_text="Seuil 70%")
            st.plotly_chart(fig_bubble, use_container_width=True)
            
            # Graphique d'évolution individuelle
            fig_pics = go.Figure()
            colors = px.colors.qualitative.Set1
            for i, (_, row) in enumerate(pics.iterrows()):
                fig_pics.add_trace(go.Scatter(
                    x=['Avant', 'Jour suspect', 'Après'],
                    y=[row['moyenne_avant'], row['score'], row['moyenne_apres']],
                    mode='lines+markers',
                    name=row['etudiant'].split('@')[0],
                    line=dict(color=colors[i % len(colors)], width=3),
                    marker=dict(size=10)
                ))
            
            fig_pics.update_layout(
                title="Évolution des scores avant/après les pics",
                yaxis=dict(range=[0, 105], ticksuffix="%"),
                height=400
            )
            st.plotly_chart(fig_pics, use_container_width=True)
            
            # Tableau des pics
            pics_display = pics.copy()
            pics_display['etudiant'] = pics_display['etudiant'].str.split('@').str[0]
            st.dataframe(pics_display[['etudiant', 'jour', 'score', 'contexte']], use_container_width=True)
        
        st.divider()
        
        # Section 3: Montagnes russes
        st.subheader("🎢 Montagnes russes (irrégularité artificielle)")
        st.caption("Détecte les alternances rapides >30% (triche sélective)")
        montagnes = detect_montagnes_russes(self.df)
        
        if montagnes.empty:
            st.info("Aucun pattern de montagnes russes détecté")
        else:
            st.write(f"{len(montagnes)} étudiant(s) avec pattern suspect")
            
            # Graphique des alternances
            fig_mont = px.bar(
                montagnes,
                x='etudiant',
                y='alternances',
                color='alternances',
                color_continuous_scale='Reds',
                labels={'alternances': 'Nombre d\'alternances', 'etudiant': 'Étudiant'},
                title="Étudiants avec alternances rapides de score"
            )
            fig_mont.update_layout(height=400)
            st.plotly_chart(fig_mont, use_container_width=True)
            
            mont_display = montagnes.copy()
            mont_display['etudiant'] = mont_display['etudiant'].str.split('@').str[0]
            st.dataframe(mont_display[['etudiant', 'alternances', 'pattern']], use_container_width=True)
