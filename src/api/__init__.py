"""API module - Client et endpoints Hermès."""

from src.api.client import HermesClient, HermesError, HermesAuthError, HermesNotFoundError, HermesRateLimitError
from src.api.auth import get_auth_headers
from src.api.activities import ActivitiesAPI
from src.api.cache import APICache

__all__ = [
    "HermesClient",
    "HermesError",
    "HermesAuthError", 
    "HermesNotFoundError",
    "HermesRateLimitError",
    "get_auth_headers",
    "ActivitiesAPI",
    "APICache",
]
