"""Chargeurs de données (CSV et API)."""

import os
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd

from src.api.client import HermesClient
from src.api.activities import ActivitiesAPI


class DataLoader(ABC):
    """Classe de base pour les chargeurs de données."""
    
    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Charge les données et retourne un DataFrame."""
        pass


class CSVLoader(DataLoader):
    """Chargeur de fichiers CSV."""
    
    def __init__(self, datasets_dir: str):
        """Initialise avec le répertoire des datasets."""
        self.datasets_dir = datasets_dir
    
    def _parse_filename(self, filename: str) -> Optional[Dict[str, str]]:
        """
        Parse un nom de fichier CSV pour extraire les métadonnées.
        Format: hermes_2025_B-DAT-200_databootcampd01_delivery.csv
        """
        pattern = r'hermes_(\d+)_(.+?)_(.+?\d+)_(delivery|git)\.csv'
        match = re.match(pattern, filename)
        
        if not match:
            return None
        
        return {
            'year': match.group(1),
            'unit': match.group(2),
            'day_slug': match.group(3),
            'test_type': match.group(4)
        }
    
    def load(self) -> pd.DataFrame:
        """Charge tous les CSV et agrège les résultats."""
        csv_files = [f for f in os.listdir(self.datasets_dir) if f.endswith('.csv')]
        
        if not csv_files:
            return pd.DataFrame()
        
        all_results: Dict[str, Dict[str, float]] = {}
        
        for csv_file in sorted(csv_files):
            meta = self._parse_filename(csv_file)
            if not meta:
                continue
            
            # Extraire le numéro de jour
            day_match = re.search(r'd(\d+)$', meta['day_slug'])
            if day_match:
                day_label = f"day{day_match.group(1).zfill(2)}"
            else:
                day_label = meta['day_slug']
            
            # Charger le CSV
            filepath = os.path.join(self.datasets_dir, csv_file)
            try:
                df_day = pd.read_csv(filepath, sep=';')
                
                for _, row in df_day.iterrows():
                    login = row.get('login', row.iloc[0])
                    pct = row.get('test %', row.iloc[1])
                    
                    if login not in all_results:
                        all_results[login] = {}
                    all_results[login][day_label] = float(pct)
            
            except Exception as e:
                print(f"⚠️ Erreur chargement {csv_file}: {e}")
                continue
        
        # Convertir en DataFrame
        if not all_results:
            return pd.DataFrame()
        
        df = pd.DataFrame.from_dict(all_results, orient='index')
        df = df.reindex(sorted(df.columns), axis=1)
        df.index.name = 'login'
        
        return df


class APILoader(DataLoader):
    """Chargeur de données depuis l'API Hermès."""
    
    def __init__(
        self,
        client: Optional[HermesClient] = None,
        year: str = "2025",
        unit: str = "B-DAT-200",
        instance: Optional[str] = None
    ):
        """Initialise le chargeur API."""
        self.client = client or HermesClient()
        self.year = year
        self.unit = unit
        self.instance = instance
        self.activities_api = ActivitiesAPI(self.client)
    
    def load(self) -> pd.DataFrame:
        """Charge les données depuis l'API."""
        print(f"Chargement API: year={self.year}, unit={self.unit}, instance={self.instance}")
        
        # Récupérer les activités
        activities = self.activities_api.list_activities(
            self.year, self.unit, self.instance
        )
        
        print(f"Activités trouvées: {len(activities)}")
        
        # Construire le mapping des résultats
        all_results: Dict[str, Dict[str, float]] = {}
        
        for activity in sorted(activities, key=lambda x: x.get('projectTemplate', {}).get('slug', '')):
            slug = activity.get('projectTemplate', {}).get('slug', '')
            activity_id = activity.get('id')
            day_label = self.activities_api.parse_day_label(slug)
            
            try:
                df_day = self.activities_api.get_activity_results(activity_id, 'delivery')
                
                for _, row in df_day.iterrows():
                    login = row['login']
                    pct = row['test %']
                    
                    if login not in all_results:
                        all_results[login] = {}
                    all_results[login][day_label] = pct
                
            except Exception as e:
                print(f"⚠️ Erreur récupération {slug}: {e}")
                continue
        
        # Convertir en DataFrame
        if not all_results:
            return pd.DataFrame()
        
        df = pd.DataFrame.from_dict(all_results, orient='index')
        df = df.reindex(sorted(df.columns), axis=1)
        df.index.name = 'login'
        
        return df
