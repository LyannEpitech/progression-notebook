"""Composants graphiques avec Plotly."""

from abc import ABC, abstractmethod
from typing import Optional, List
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


class ChartComponent(ABC):
    """Classe de base pour les graphiques."""
    
    @abstractmethod
    def render(self):
        pass


class LineChart(ChartComponent):
    """Graphique linéaire."""
    
    def __init__(
        self,
        data: pd.DataFrame,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        color: str = "#4C8BF5",
        secondary_line: Optional[pd.Series] = None
    ):
        self.data = data
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.color = color
        self.secondary_line = secondary_line
    
    def render(self):
        fig = go.Figure()
        
        # Ligne principale
        fig.add_trace(go.Scatter(
            x=self.data.index,
            y=self.data.values,
            mode="lines+markers",
            name="Score",
            line=dict(color=self.color, width=3),
            marker=dict(size=8)
        ))
        
        # Ligne secondaire (ex: moyenne promo)
        if self.secondary_line is not None:
            fig.add_trace(go.Scatter(
                x=self.secondary_line.index,
                y=self.secondary_line.values,
                mode="lines",
                name="Moyenne",
                line=dict(color="#4C8BF5", width=2, dash="dot")
            ))
        
        fig.update_layout(
            title=self.title,
            xaxis_title=self.x_label,
            yaxis_title=self.y_label,
            hovermode="x unified",
            yaxis=dict(range=[0, 105], ticksuffix="%")
        )
        
        st.plotly_chart(fig, use_container_width=True)


class BarChart(ChartComponent):
    """Graphique en barres."""
    
    def __init__(
        self,
        data: pd.Series,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        color: str = "#4C8BF5",
        horizontal: bool = False
    ):
        self.data = data
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.color = color
        self.horizontal = horizontal
    
    def render(self):
        if self.horizontal:
            fig = px.bar(
                x=self.data.values,
                y=self.data.index,
                orientation='h',
                title=self.title,
                labels={'x': self.x_label, 'y': self.y_label}
            )
        else:
            fig = px.bar(
                x=self.data.index,
                y=self.data.values,
                title=self.title,
                labels={'x': self.x_label, 'y': self.y_label}
            )
        
        fig.update_traces(marker_color=self.color)
        st.plotly_chart(fig, use_container_width=True)


class HeatmapChart(ChartComponent):
    """Carte de chaleur."""
    
    def __init__(self, data: pd.DataFrame, title: str = ""):
        self.data = data
        self.title = title
    
    def render(self):
        fig = px.imshow(
            self.data,
            title=self.title,
            color_continuous_scale="RdYlGn",
            aspect="auto"
        )
        st.plotly_chart(fig, use_container_width=True)


class RadarChart(ChartComponent):
    """Graphique radar pour comparaison multi-dimensionnelle."""
    
    def __init__(
        self,
        categories: List[str],
        values: List[float],
        title: str = "",
        fill: bool = True
    ):
        self.categories = categories
        self.values = values
        self.title = title
        self.fill = fill
    
    def render(self):
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=self.values + [self.values[0]],  # Fermer le polygone
            theta=self.categories + [self.categories[0]],
            fill='toself' if self.fill else None,
            name='Score'
        ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            title=self.title
        )
        
        st.plotly_chart(fig, use_container_width=True)
