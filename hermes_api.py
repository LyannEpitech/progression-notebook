"""
Module d'intégration API Hermès pour Pool Progression
DEPRECATED: Ce module est conservé pour compatibilité. Utilisez src.api à la place.
"""

import warnings
warnings.warn(
    "hermes_api.py is deprecated. Use src.api instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export depuis le nouveau module
from src.api.auth import get_auth_headers
from src.api.client import HermesClient, HermesError, HermesAuthError, HermesNotFoundError, HermesRateLimitError
from src.api.activities import ActivitiesAPI
from src.api.cache import APICache

# Pour compatibilité avec l'ancien code
from src.api.activities import ActivitiesAPI as _ActivitiesAPI

# Variables globales (pour compatibilité)
from dotenv import load_dotenv
import os

load_dotenv()

PAT = os.getenv('PAT')
PAT_ID = os.getenv('PAT_ID')
HERMES_ENDPOINT = os.getenv('HERMES_ENDPOINT', 'https://api.epitest.eu/api/')

# Liste des units (chargée depuis config)
try:
    _api = _ActivitiesAPI()
    KNOWN_BACHELOR_UNITS = _api.known_units
    AVAILABLE_YEARS = _api.available_years
except Exception:
    # Fallback si config non disponible
    KNOWN_BACHELOR_UNITS = [
        "B-DAT-200", "B-WEB-100", "B-CPP-100", "B-MUL-100",
        "B-MAT-100", "B-COM-100", "B-ANG-100", "B-PRO-100",
        "B-SYS-100", "B-SEC-100", "B-AIA-100", "B-PSU-100",
        "B-DAT-201", "B-WEB-201", "B-CPP-201", "B-MUL-201",
        "B-MAT-201", "B-COM-201", "B-ANG-201", "B-PRO-201",
        "B-SYS-201", "B-SEC-201", "B-AIA-201", "B-PSU-200",
        "B-DAT-300", "B-WEB-300", "B-CPP-300", "B-MUL-300",
        "B-MAT-300", "B-COM-300", "B-ANG-300", "B-PRO-300",
        "B-SYS-300", "B-SEC-300", "B-AIA-300", "B-PSU-300",
        "B-OOP-100", "B-DBS-100", "B-NET-100", "B-MLG-100",
        "B-OOP-200", "B-DBS-200", "B-NET-200", "B-MLG-200",
    ]
    AVAILABLE_YEARS = ["2024", "2025", "2026", "2027", "2028"]

# Cache legacy
_activities_cache = {}


def get_available_units(year: str):
    """DEPRECATED: Utilisez ActivitiesAPI.list_available_units()"""
    api = _ActivitiesAPI()
    return api.list_available_units(year)


def validate_unit(year: str, unit: str) -> bool:
    """DEPRECATED: Utilisez ActivitiesAPI.validate_unit()"""
    api = _ActivitiesAPI()
    return api.validate_unit(year, unit)


def parse_csv_filename(filename: str):
    """DEPRECATED: Utilisez ActivitiesAPI.parse_csv_filename()"""
    api = _ActivitiesAPI()
    return api.parse_csv_filename(filename)


def get_activities(year: str, unit: str, instance=None):
    """DEPRECATED: Utilisez ActivitiesAPI.list_activities()"""
    api = _ActivitiesAPI()
    return api.list_activities(year, unit, instance)


def find_activity_id(activities, day_slug: str):
    """DEPRECATED: Utilisez ActivitiesAPI.find_activity_id()"""
    api = _ActivitiesAPI()
    return api.find_activity_id(activities, day_slug)


def fetch_test_results(activity_id: int, test_type: str = 'delivery'):
    """DEPRECATED: Utilisez ActivitiesAPI.get_activity_results()"""
    api = _ActivitiesAPI()
    return api.get_activity_results(activity_id, test_type)


def load_data_from_api(datasets_dir: str, instance=None, year=None, unit=None):
    """DEPRECATED: Utilisez APILoader"""
    from src.data.loaders import APILoader
    loader = APILoader(year=year or "2025", unit=unit or "B-DAT-200", instance=instance)
    return loader.load()


def sync_csv_from_api(datasets_dir: str, instance=None):
    """DEPRECATED: Fonctionnalité non implémentée dans la nouvelle architecture"""
    raise NotImplementedError("sync_csv_from_api n'est plus supporté")
