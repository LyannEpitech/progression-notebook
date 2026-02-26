"""Authentification API Hermès."""

import base64
import os
from typing import Dict


def get_auth_headers(pat: str = None, pat_id: str = None) -> Dict[str, str]:
    """
    Génère les headers d'authentification Basic Auth.
    
    Args:
        pat: Personal Access Token (depuis .env si None)
        pat_id: ID du PAT (depuis .env si None)
    
    Returns:
        Dict avec header Authorization
    """
    pat = pat or os.getenv('PAT')
    pat_id = pat_id or os.getenv('PAT_ID')
    
    if not pat or not pat_id:
        raise ValueError("PAT et PAT_ID doivent être définis dans .env ou passés en argument")
    
    creds = f"{pat_id}:{pat}"
    encoded = base64.b64encode(creds.encode('utf-8')).decode('utf-8')
    return {"Authorization": f"Basic {encoded}"}
