"""Moteur de scoring et calcul du niveau global des étudiants."""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from src.core.models import Student, ActivityResult


class ScoringEngine:
    """Calcule les scores et niveaux globaux des étudiants."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialise le moteur de scoring.
        
        Args:
            df: DataFrame avec index=student_id, columns=jours, values=scores
        """
        self.df = df
    
    def calculate_progression_score(self, student_id: str) -> Dict[str, float]:
        """
        Calcule un score de progression pour un étudiant.
        
        Returns:
            Dict avec moyenne, tendance, régularité, etc.
        """
        if student_id not in self.df.index:
            return {}
        
        scores = self.df.loc[student_id]
        
        # Métriques de base
        mean_score = scores.mean()
        std_score = scores.std()
        min_score = scores.min()
        max_score = scores.max()
        
        # Tendance (régression linéaire simple)
        x = np.arange(len(scores))
        trend = np.polyfit(x, scores.values, 1)[0]  # Pente
        
        # Régularité (inverse de l'écart-type normalisé)
        regularity = max(0, 100 - (std_score / mean_score * 100)) if mean_score > 0 else 0
        
        # Score global pondéré
        global_score = (
            mean_score * 0.4 +           # 40% - Moyenne
            min(100, max(0, 50 + trend * 10)) * 0.3 +  # 30% - Tendance
            regularity * 0.2 +           # 20% - Régularité
            (scores.iloc[-1] if len(scores) > 0 else 0) * 0.1  # 10% - Dernier score
        )
        
        return {
            "global_score": round(global_score, 2),
            "average": round(mean_score, 2),
            "trend": round(trend, 2),
            "regularity": round(regularity, 2),
            "min": round(min_score, 2),
            "max": round(max_score, 2),
            "std": round(std_score, 2),
        }
    
    def calculate_skill_score(self, student_id: str, skill_breakdowns: Dict) -> Dict[str, float]:
        """
        Calcule le score par compétence technique.
        
        Args:
            student_id: ID de l'étudiant
            skill_breakdowns: Dict des skillBreakdowns de l'API
        """
        if not skill_breakdowns:
            return {}
        
        skill_scores = {}
        
        for skill_name, skill_data in skill_breakdowns.items():
            if isinstance(skill_data, list) and len(skill_data) > 0:
                counts = skill_data[0]
                if isinstance(counts, dict):
                    total = counts.get('count', 0)
                    passed = counts.get('passed', 0)
                    if total > 0:
                        skill_scores[skill_name] = round((passed / total) * 100, 2)
        
        return skill_scores
    
    def get_leaderboard(self) -> pd.DataFrame:
        """
        Génère un classement complet de tous les étudiants.
        
        Returns:
            DataFrame avec scores détaillés par étudiant
        """
        data = []
        
        for student_id in self.df.index:
            scores = self.calculate_progression_score(student_id)
            data.append({
                'student_id': student_id,
                'display_name': student_id.split('@')[0],
                **scores
            })
        
        df = pd.DataFrame(data)
        return df.sort_values('global_score', ascending=False)
    
    def calculate_class_stats(self) -> Dict[str, float]:
        """Calcule les statistiques de la classe entière."""
        all_means = self.df.mean(axis=1)
        day_means = self.df.mean(axis=0)
        
        return {
            'class_average': round(all_means.mean(), 2),
            'class_std': round(all_means.std(), 2),
            'best_student': all_means.idxmax(),
            'best_score': round(all_means.max(), 2),
            'hardest_day': day_means.idxmin(),
            'hardest_day_score': round(day_means.min(), 2),
            'easiest_day': day_means.idxmax(),
            'easiest_day_score': round(day_means.max(), 2),
        }
