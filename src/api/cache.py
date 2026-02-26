"""Gestion du cache API."""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class APICache:
    """Cache simple basé sur fichiers JSON pour les résultats API."""
    
    def __init__(self, cache_dir: str = ".cache"):
        """Initialise le cache."""
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> str:
        """Génère le chemin du fichier de cache."""
        # Remplacer les caractères problématiques
        safe_key = key.replace('/', '_').replace('\\', '_')
        return os.path.join(self.cache_dir, f"{safe_key}.json")
    
    def get(self, key: str, max_age_minutes: int = 5) -> Optional[Dict[str, Any]]:
        """
        Récupère une valeur du cache si elle existe et n'est pas expirée.
        
        Args:
            key: Clé de cache
            max_age_minutes: Âge maximum en minutes
        
        Returns:
            Données cachées ou None
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            # Vérifier l'expiration
            timestamp = datetime.fromisoformat(cached.get('timestamp', '2000-01-01'))
            age = datetime.now() - timestamp
            
            if age > timedelta(minutes=max_age_minutes):
                return None
            
            return cached.get('data')
        
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
    
    def set(self, key: str, data: Dict[str, Any]) -> None:
        """Stocke une valeur dans le cache."""
        cache_path = self._get_cache_path(key)
        
        cached = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cached, f, ensure_ascii=False, indent=2)
    
    def clear(self) -> None:
        """Vide tout le cache."""
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                os.remove(os.path.join(self.cache_dir, filename))
    
    def invalidate(self, key: str) -> None:
        """Invalide une clé spécifique."""
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            os.remove(cache_path)
