"""Endpoints liés aux activités."""

import os
import re
from typing import List, Dict, Optional
import yaml
import pandas as pd

from src.api.client import HermesClient


class ActivitiesAPI:
    """API pour la gestion des activités et résultats."""
    
    # Activités à exclure
    EXCLUDED_SLUGS = {'tardis'}
    
    def __init__(self, client: HermesClient = None):
        """Initialise l'API avec un client configuré."""
        self.client = client or HermesClient()
        self._config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Charge la configuration depuis le fichier YAML."""
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'units.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback si le fichier n'existe pas
            return {
                'KNOWN_BACHELOR_UNITS': [
                    "B-DAT-200", "B-WEB-100", "B-CPP-100", "B-MUL-100",
                    "B-MAT-100", "B-COM-100", "B-ANG-100", "B-PRO-100",
                    "B-SYS-100", "B-SEC-100", "B-AIA-100", "B-PSU-100",
                ],
                'AVAILABLE_YEARS': ["2024", "2025", "2026", "2027", "2028"]
            }
    
    @property
    def known_units(self) -> List[str]:
        """Retourne la liste des units connus."""
        return self._config.get('KNOWN_BACHELOR_UNITS', [])
    
    @property
    def available_years(self) -> List[str]:
        """Retourne la liste des années disponibles."""
        return self._config.get('AVAILABLE_YEARS', ["2024", "2025", "2026", "2027", "2028"])
    
    def list_available_units(self, year: str, timeout_per_request: int = 3) -> List[str]:
        """
        Retourne la liste des units disponibles pour une année donnée.
        
        Args:
            year: Année scolaire (ex: "2025")
            timeout_per_request: Timeout par requête en secondes
        
        Returns:
            Liste des codes units disponibles
        """
        available = []
        
        for unit in self.known_units:
            try:
                result = self.client.get_activities(year, unit)
                activities = result.get('activities', [])
                if len(activities) > 0:
                    available.append(unit)
            except Exception:
                pass  # Ignorer silencieusement
        
        return available
    
    def validate_unit(self, year: str, unit: str) -> bool:
        """Vérifie si un unit existe pour une année donnée."""
        try:
            result = self.client.get_activities(year, unit)
            activities = result.get('activities', [])
            return len(activities) > 0
        except Exception:
            return False
    
    def list_activities(self, year: str, unit: str, instance: Optional[str] = None) -> List[Dict]:
        """
        Liste les activités d'un unit, filtrées des exclusions.
        
        Returns:
            Liste des activités (dicts)
        """
        result = self.client.get_activities(year, unit, instance)
        activities = result.get('activities', [])
        
        # Filtrer les activités exclues
        filtered = []
        for activity in activities:
            slug = activity.get('projectTemplate', {}).get('slug', '').lower()
            if slug and slug not in self.EXCLUDED_SLUGS:
                filtered.append(activity)
        
        return filtered
    
    def get_activity_results(
        self,
        activity_id: int,
        test_type: str = "delivery"
    ) -> pd.DataFrame:
        """
        Récupère les résultats d'une activité au format DataFrame.
        
        Returns:
            DataFrame avec colonnes: login, test %
        """
        data = self.client.get_test_results(activity_id, test_type)
        results = data.get('results', [])
        
        students = []
        for result in results:
            # Extraire le login
            members = result.get('properties', {}).get('group', {}).get('members', [])
            login = members[0] if members else 'N/A'
            
            # Calculer le % de tests réussis
            skill_breakdowns = result.get('skillBreakdowns', {})
            total_tests = 0
            passed_tests = 0
            
            for skill_data in skill_breakdowns.values():
                if isinstance(skill_data, list) and len(skill_data) > 0:
                    counts = skill_data[0]
                    if isinstance(counts, dict):
                        total_tests += counts.get('count', 0)
                        passed_tests += counts.get('passed', 0)
            
            test_pct = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            students.append({
                'login': login,
                'test %': round(test_pct, 1)
            })
        
        return pd.DataFrame(students)
    
    def parse_day_label(self, slug: str) -> str:
        """Extrait le label du jour depuis un slug (ex: databootcampd01 -> day01)."""
        match = re.search(r'd(\d+)$', slug)
        if match:
            return f"day{match.group(1).zfill(2)}"
        return slug
    
    def find_activity_id(self, activities: List[Dict], day_slug: str) -> Optional[int]:
        """Trouve l'ID d'une activité à partir de son slug."""
        for activity in activities:
            slug = activity.get('projectTemplate', {}).get('slug', '')
            if slug == day_slug:
                return activity.get('id')
        return None
