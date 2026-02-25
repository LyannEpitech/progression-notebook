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

# ... (fonctions de detection et utilitaires identiques)

# ============ NOUVELLES VISUALISATIONS ============

def create_similarity_heatmap(df, copieurs_df):
    """Heatmap des similarities entre eleves."""
    if copieurs_df.empty or len(copieurs_df) < 2:
        return None
    
    involved = list(set(copieurs_df['etudiant_1'].tolist() + copieurs_df['etudiant_2'].tolist()))
    if len(involved) < 2:
        return None
    
    diff_matrix = pd.DataFrame(index=involved, columns=involved)
    for s1 in involved:
        for s2 in involved:
            if s1 == s2:
                diff_matrix.loc[s1, s2] = 0
            else:
                diff_matrix.loc[s1, s2] = (df.loc[s1] - df.loc[s2]).abs().mean()
    
    diff_matrix.index = [s.split('@')[0] for s in diff_matrix.index]
    diff_matrix.columns = [s.split('@')[0] for s in diff_matrix.columns]
    
    fig = px.imshow(diff_matrix.astype(float), color_continuous_scale='RdYlGn_r',
                    range_color=[0, 10], title="🔥 Heatmap des differences")
    fig.update_layout(height=500)
    return fig

def create_network_graph(copieurs_df):
    """Graphe reseau des connexions."""
    if copieurs_df.empty:
        return None
    
    students = list(set(copieurs_df['etudiant_1'].tolist() + copieurs_df['etudiant_2'].tolist()))
    if len(students) < 2:
        return None
    
    fig = go.Figure()
    positions = {s: (math.cos(2*math.pi*i/len(students))*2, 
                     math.sin(2*math.pi*i/len(students))*2) 
                 for i, s in enumerate(students)}
    
    for _, row in copieurs_df.iterrows():
        x0, y0 = positions[row['etudiant_1']]
        x1, y1 = positions[row['etudiant_2']]
        width = min(row['jours_similaires'] / 2, 4)
        fig.add_trace(go.Scatter(x=[x0, x1, None], y=[y0, y1, None], mode='lines',
                                 line=dict(color='rgba(255,0,0,0.4)', width=width),
                                 hoverinfo='skip', showlegend=False))
    
    fig.add_trace(go.Scatter(
        x=[positions[s][0] for s in students],
        y=[positions[s][1] for s in students],
        mode='markers+text',
        marker=dict(size=25, color='darkred', line=dict(color='white', width=2)),
        text=[s.split('@')[0] for s in students],
        textposition='top center'
    ))
    
    fig.update_layout(title="🕸️ Reseau des connexions", height=500,
                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      plot_bgcolor='rgba(0,0,0,0)')
    return fig

def create_radar_chart(suspicion_df, student_name):
    """Radar chart d'un eleve."""
    if student_name not in suspicion_df.index:
        return None
    
    row = suspicion_df.loc[student_name]
    categories = ['Copieurs', 'Pics', 'Montagnes', 'Collectif']
    values = [row.get('copieurs', 0), row.get('pics', 0), 
              row.get('montagnes', 0), row.get('collectif', 0)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]],
                                   fill='toself', fillcolor='rgba(255,0,0,0.3)',
                                   line=dict(color='red', width=2)))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(values)*1.2 or 10])),
                      title=f"🎯 Profil - {student_name.split('@')[0]}", height=400)
    return fig

def create_comparison_radar(suspicion_df, top_n=5):
    """Radar chart comparatif."""
    if suspicion_df.empty or len(suspicion_df) < 2:
        return None
    
    top = suspicion_df.head(top_n)
    categories = ['Copieurs', 'Pics', 'Montagnes', 'Collectif']
    colors = px.colors.qualitative.Set1
    
    fig = go.Figure()
    for i, (student, row) in enumerate(top.iterrows()):
        values = [row.get('copieurs', 0), row.get('pics', 0),
                  row.get('montagnes', 0), row.get('collectif', 0)]
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]], theta=categories + [categories[0]],
            fill='toself', name=student.split('@')[0],
            line=dict(color=colors[i % len(colors)])))
    
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)),
                      title="🎯 Comparaison Top 5", height=500,
                      legend=dict(orientation="h", y=-0.2))
    return fig

def create_bubble_chart_pics(pics_df):
    """Bubble chart des pics."""
    if pics_df.empty:
        return None
    
    pics_clean = pics_df.copy().fillna(0)
    fig = px.scatter(pics_clean, x='jour', y='score', size='score', color='moyenne_avant',
                     hover_data=['etudiant'], title="📍 Carte des pics",
                     color_continuous_scale='RdYlBu_r', range_color=[0, 50])
    fig.update_yaxes(range=[0, 105], ticksuffix="%")
    fig.add_hline(y=70, line_dash="dash", line_color="green")
    return fig

def create_timeline_suspects(df, suspicion_df):
    """Timeline des suspects."""
    if suspicion_df.empty:
        return None
    
    top = suspicion_df.head(5).index.tolist()
    fig = go.Figure()
    
    for i, student in enumerate(top):
        scores = df.loc[student]
        fig.add_trace(go.Scatter(
            x=scores.index, y=[i]*len(scores), mode='markers',
            marker=dict(size=scores.values/3, color=scores.values, colorscale='RdYlGn',
                       showscale=(i==0), colorbar=dict(title="Score") if i==0 else None),
            name=student.split('@')[0]))
    
    fig.update_layout(title="⏱️ Timeline des scores", xaxis_title="Jour",
                      yaxis=dict(tickvals=list(range(len(top))),
                                ticktext=[s.split('@')[0] for s in top]),
                      height=400)
    return fig

def create_treemap_clusters(copies_df):
    """Treemap des clusters."""
    if copies_df.empty:
        return None
    
    fig = px.treemap(copies_df, path=[px.Constant("Tous"), 'jour', 'score'],
                     values='nb_eleves', color='nb_eleves',
                     color_continuous_scale='Reds',
                     title="👥 Clusters de copies")
    fig.update_layout(height=400)
    return fig
