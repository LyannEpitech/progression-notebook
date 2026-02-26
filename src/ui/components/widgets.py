"""Widgets réutilisables pour l'interface."""

import streamlit as st
from typing import Optional


class MetricCard:
    """Carte de métrique avec valeur et description."""
    
    def __init__(
        self,
        label: str,
        value: str,
        delta: Optional[str] = None,
        help_text: Optional[str] = None
    ):
        self.label = label
        self.value = value
        self.delta = delta
        self.help_text = help_text
    
    def render(self):
        if self.delta:
            st.metric(
                label=self.label,
                value=self.value,
                delta=self.delta,
                help=self.help_text
            )
        else:
            st.metric(
                label=self.label,
                value=self.value,
                help=self.help_text
            )


class SuspicionBadge:
    """Badge d'indication de suspicion."""
    
    LEVELS = {
        'low': {'color': '🟢', 'label': 'Faible'},
        'medium': {'color': '🟡', 'label': 'Moyen'},
        'high': {'color': '🔴', 'label': 'Élevé'},
        'critical': {'color': '⚫', 'label': 'Critique'}
    }
    
    def __init__(self, score: float):
        self.score = score
        self.level = self._get_level()
    
    def _get_level(self) -> str:
        if self.score >= 70:
            return 'critical'
        elif self.score >= 40:
            return 'high'
        elif self.score >= 20:
            return 'medium'
        return 'low'
    
    def render(self):
        level = self.LEVELS[self.level]
        return f"{level['color']} {level['label']} ({self.score:.0f})"
