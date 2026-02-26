"""Transformateurs de données."""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class DataTransformer:
    """Transformations communes sur les DataFrames de résultats."""
    
    @staticmethod
    def normalize_scores(df: pd.DataFrame, method: str = "minmax") -> pd.DataFrame:
        """
        Normalise les scores selon une méthode.
        
        Args:
            df: DataFrame avec les scores
            method: "minmax" ou "zscore"
        """
        if method == "minmax":
            return (df - df.min()) / (df.max() - df.min()) * 100
        elif method == "zscore":
            return (df - df.mean()) / df.std()
        else:
            raise ValueError(f"Méthode inconnue: {method}")
    
    @staticmethod
    def fill_missing(df: pd.DataFrame, method: str = "interpolate") -> pd.DataFrame:
        """
        Remplit les valeurs manquantes.
        
        Args:
            df: DataFrame avec potentiellement des NaN
            method: "interpolate", "mean", "zero", "forward"
        """
        if method == "interpolate":
            return df.interpolate(axis=1).fillna(method='bfill', axis=1).fillna(0)
        elif method == "mean":
            return df.fillna(df.mean(axis=1), axis=0)
        elif method == "zero":
            return df.fillna(0)
        elif method == "forward":
            return df.fillna(method='ffill', axis=1).fillna(0)
        else:
            raise ValueError(f"Méthode inconnue: {method}")
    
    @staticmethod
    def calculate_rolling_average(df: pd.DataFrame, window: int = 3) -> pd.DataFrame:
        """Calcule la moyenne glissante par étudiant."""
        return df.rolling(window=window, axis=1, min_periods=1).mean()
    
    @staticmethod
    def detect_outliers(df: pd.DataFrame, threshold: float = 2.0) -> pd.DataFrame:
        """
        Détecte les outliers (scores anormaux) par Z-score.
        
        Returns:
            DataFrame booléen des outliers
        """
        z_scores = np.abs((df - df.mean()) / df.std())
        return z_scores > threshold
    
    @staticmethod
    def add_rank_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Ajoute des colonnes de classement par jour."""
        df_ranked = df.copy()
        for col in df.columns:
            df_ranked[f"{col}_rank"] = df[col].rank(ascending=False, method='min')
        return df_ranked
    
    @staticmethod
    def export_for_ml(df: pd.DataFrame) -> pd.DataFrame:
        """
        Prépare les données pour le machine learning.
        Features: moyenne, std, min, max, tendance
        """
        features = pd.DataFrame(index=df.index)
        features['mean'] = df.mean(axis=1)
        features['std'] = df.std(axis=1)
        features['min'] = df.min(axis=1)
        features['max'] = df.max(axis=1)
        
        # Tendance (pente de la régression linéaire)
        x = np.arange(df.shape[1])
        features['trend'] = df.apply(
            lambda row: np.polyfit(x, row.values, 1)[0] if not row.isna().all() else 0,
            axis=1
        )
        
        # Régularité (1 - coefficient de variation)
        features['regularity'] = 1 - (features['std'] / features['mean'])
        features['regularity'] = features['regularity'].fillna(0)
        
        return features
