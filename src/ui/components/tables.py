"""Composants de tableaux de données."""

import streamlit as st
import pandas as pd
from typing import Optional


class DataTable:
    """Tableau de données configurable."""
    
    def __init__(
        self,
        data: pd.DataFrame,
        title: Optional[str] = None,
        height: int = 400,
        use_container_width: bool = True
    ):
        self.data = data
        self.title = title
        self.height = height
        self.use_container_width = use_container_width
    
    def render(self):
        if self.title:
            st.subheader(self.title)
        
        st.dataframe(
            self.data,
            use_container_width=self.use_container_width,
            height=self.height
        )


class SuspicionTable:
    """Tableau spécialisé pour les résultats de détection."""
    
    def __init__(self, data: pd.DataFrame, title: str = "Résultats de détection"):
        self.data = data
        self.title = title
    
    def render(self):
        if self.data.empty:
            st.info("Aucun comportement suspect détecté")
            return
        
        st.subheader(self.title)
        
        # Colorer selon le score
        def color_score(val):
            if isinstance(val, (int, float)):
                if val >= 70:
                    return 'background-color: #ffcccc'
                elif val >= 40:
                    return 'background-color: #ffffcc'
            return ''
        
        styled = self.data.style.applymap(color_score)
        st.dataframe(styled, use_container_width=True)
