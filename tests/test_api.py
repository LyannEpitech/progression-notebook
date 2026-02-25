# tests/test_api.py
import pytest
from hermes_api import parse_csv_filename, find_activity_id

def test_parse_csv_filename_valid():
    """Parse un nom de fichier valide."""
    result = parse_csv_filename('hermes_2025_B-DAT-200_databootcampd01_delivery.csv')
    
    assert result is not None
    assert result['year'] == '2025'
    assert result['unit'] == 'B-DAT-200'
    assert result['day_slug'] == 'databootcampd01'
    assert result['test_type'] == 'delivery'

def test_parse_csv_filename_invalid():
    """Retourne None pour un nom invalide."""
    result = parse_csv_filename('invalid_file.csv')
    assert result is None

def test_parse_csv_filename_different_units():
    """Parse differentes unites."""
    test_cases = [
        ('hermes_2025_W-WEB-100_poolwebd03_delivery.csv', 'W-WEB-100', 'poolwebd03'),
        ('hermes_2025_P-CPP-100_poolcppd05_git.csv', 'P-CPP-100', 'poolcppd05'),
    ]
    
    for filename, expected_unit, expected_slug in test_cases:
        result = parse_csv_filename(filename)
        assert result['unit'] == expected_unit
        assert result['day_slug'] == expected_slug

def test_find_activity_id_found():
    """Trouve l'ID d'une activite existante."""
    activities = [
        {'id': 123, 'projectTemplate': {'slug': 'databootcampd01'}},
        {'id': 456, 'projectTemplate': {'slug': 'databootcampd02'}},
    ]
    
    result = find_activity_id(activities, 'databootcampd01')
    assert result == 123

def test_find_activity_id_not_found():
    """Retourne None si l'activite n'existe pas."""
    activities = [
        {'id': 123, 'projectTemplate': {'slug': 'databootcampd01'}},
    ]
    
    result = find_activity_id(activities, 'nonexistent')
    assert result is None
