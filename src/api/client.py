"""Client HTTP pour l'API Hermès."""

import os
from typing import Dict, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.api.auth import get_auth_headers


class HermesError(Exception):
    """Exception de base pour les erreurs API Hermès."""
    pass


class HermesAuthError(HermesError):
    """Erreur d'authentification (401, 403)."""
    pass


class HermesNotFoundError(HermesError):
    """Ressource non trouvée (404)."""
    pass


class HermesRateLimitError(HermesError):
    """Rate limiting (429)."""
    pass


class HermesClient:
    """Client HTTP pour l'API Hermès avec retry et gestion d'erreurs."""
    
    def __init__(
        self,
        endpoint: str = None,
        pat: str = None,
        pat_id: str = None,
        timeout: int = 10,
        max_retries: int = 3
    ):
        """
        Initialise le client Hermès.
        
        Args:
            endpoint: URL de l'API (depuis env si None)
            pat: Personal Access Token
            pat_id: ID du PAT
            timeout: Timeout des requêtes en secondes
            max_retries: Nombre de retries en cas d'erreur
        """
        self.endpoint = endpoint or os.getenv('HERMES_ENDPOINT', 'https://api.epitest.eu/api/')
        self.timeout = timeout
        
        # Session avec retry
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Headers d'authentification
        self.session.headers.update(get_auth_headers(pat, pat_id))
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
    
    def _handle_error(self, response: requests.Response) -> None:
        """Gère les erreurs HTTP et lève les exceptions appropriées."""
        if response.status_code == 200:
            return
        
        error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
        
        if response.status_code == 401:
            raise HermesAuthError(f"Authentification échouée - {error_msg}")
        elif response.status_code == 403:
            raise HermesAuthError(f"Accès interdit - {error_msg}")
        elif response.status_code == 404:
            raise HermesNotFoundError(f"Ressource non trouvée - {error_msg}")
        elif response.status_code == 429:
            raise HermesRateLimitError(f"Rate limit atteint - {error_msg}")
        else:
            raise HermesError(error_msg)
    
    def get(
        self,
        path: str,
        params: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Effectue une requête GET.
        
        Args:
            path: Chemin de l'endpoint (sans le base URL)
            params: Paramètres de requête
            **kwargs: Arguments additionnels pour requests
        
        Returns:
            Réponse JSON décodée
        """
        url = f"{self.endpoint}{path}"
        
        response = self.session.get(
            url,
            params=params,
            timeout=self.timeout,
            **kwargs
        )
        
        self._handle_error(response)
        return response.json()
    
    def get_activities(self, year: str, unit: str, instance: Optional[str] = None) -> Dict:
        """Raccourci pour récupérer les activités."""
        params = {"year": year, "unit": unit}
        if instance:
            params["instance"] = instance
        return self.get("activities", params=params)
    
    def get_test_results(self, activity_id: int, test_type: str = "delivery") -> Dict:
        """Raccourci pour récupérer les résultats de tests."""
        return self.get(f"activities/i/{activity_id}/test_results/{test_type}")
