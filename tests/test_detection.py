# tests/test_detection.py
import pytest
import pandas as pd
from dashboard import (
    detect_copieurs,
    detect_pics_isoles,
    detect_montagnes_russes,
    detect_copies_collectives,
    calculate_suspicion_score_v2
)

@pytest.fixture
def sample_data():
    """Données de test simulant 3 étudiants sur 5 jours."""
    return pd.DataFrame({
        'day01': [50.0, 50.0, 10.0],   # 0 et 1 identiques (copieurs)
        'day02': [60.0, 60.0, 20.0],   # 0 et 1 identiques
        'day03': [70.0, 70.0, 30.0],   # 0 et 1 identiques
        'day04': [80.0, 80.0, 40.0],   # 0 et 1 identiques
        'day05': [90.0, 90.0, 50.0],   # 0 et 1 identiques
    }, index=['copieur1', 'copieur2', 'normal'])

@pytest.fixture
def pic_data():
    """Données avec un pic isolé."""
    return pd.DataFrame({
        'day01': [20.0, 10.0],
        'day02': [15.0, 10.0],
        'day03': [85.0, 15.0],  # Pic isolé
        'day04': [25.0, 20.0],
        'day05': [20.0, 25.0],
    }, index=['pic_isole', 'normal'])

@pytest.fixture
def montagnes_data():
    """Données avec montagnes russes."""
    return pd.DataFrame({
        'day01': [10.0],
        'day02': [50.0],  # +40%
        'day03': [15.0],  # -35%
        'day04': [55.0],  # +40%
        'day05': [20.0],  # -35%
    }, index=['montagnes'])

class TestDetectCopieurs:
    def test_detect_similar_students(self, sample_data):
        """Détecte les étudiants avec scores similaires."""
        result = detect_copieurs(sample_data, tolerance=1, min_days=4, min_ratio=0.4)
        
        assert len(result) == 1
        assert result.iloc[0]['etudiant_1'] == 'copieur1'
        assert result.iloc[0]['etudiant_2'] == 'copieur2'
        assert result.iloc[0]['jours_similaires'] == 5
        assert result.iloc[0]['jours_consecutifs'] == 5
    
    def test_no_false_positive(self, sample_data):
        """Ne détecte pas de similarités quand il n'y en a pas."""
        # Modifie les données pour qu'elles ne soient plus similaires
        modified = sample_data.copy()
        modified.loc['copieur1'] = [10.0, 20.0, 30.0, 40.0, 50.0]
        
        result = detect_copieurs(modified, tolerance=1, min_days=4)
        assert len(result) == 0
    
    def test_tolerance_parameter(self, sample_data):
        """La tolérance fonctionne correctement."""
        # Avec tolérance 0, détecte pas (différences de 0.0 mais décimales)
        result_strict = detect_copieurs(sample_data, tolerance=0, min_days=4)
        # Avec tolérance 1, détecte
        result_loose = detect_copieurs(sample_data, tolerance=1, min_days=4)
        
        assert len(result_strict) == 1  # Mêmes valeurs exactes
        assert len(result_loose) == 1

class TestDetectPicsIsoles:
    def test_detect_isolated_peak(self, pic_data):
        ""”Détecte un pic isolé >70% entouré de <30%."""
        result = detect_pics_isoles(pic_data, seuil_haut=70, seuil_bas=30, fenetre=2)
        
        assert len(result) == 1
        assert result.iloc[0]['etudiant'] == 'pic_isole'
        assert result.iloc[0]['jour'] == 'day03'
        assert result.iloc[0]['score'] == 85.0
    
    def test_no_peak_below_threshold(self):
        """Ne détecte pas de pic sous le seuil."""
        data = pd.DataFrame({
            'day01': [20.0],
            'day02': [20.0],
            'day03': [60.0],  # Sous 70%
            'day04': [20.0],
        }, index=['student'])
        
        result = detect_pics_isoles(data, seuil_haut=70)
        assert len(result) == 0

class TestDetectMontagnesRusses:
    def test_detect_alternances(self, montagnes_data):
        ""”Détecte les alternances rapides."""
        result = detect_montagnes_russes(montagnes_data, seuil_variation=30)
        
        assert len(result) == 1
        assert result.iloc[0]['etudiant'] == 'montagnes'
        assert result.iloc[0]['alternances'] >= 3
    
    def test_no_alternance_with_low_variation(self, montagnes_data):
        """Ne détecte pas si la variation est trop faible."""
        result = detect_montagnes_russes(montagnes_data, seuil_variation=50)
        assert len(result) == 0

class TestCalculateSuspicionScore:
    def test_score_calculation(self, sample_data, pic_data, montagnes_data):
        """Le score global est bien calculé."""
        # Combine les données
        combined = pd.concat([sample_data, pic_data, montagnes_data])
        
        result = calculate_suspicion_score_v2(combined)
        
        assert len(result) > 0
        # copieur1 devrait avoir un score élevé
        assert 'copieur1' in result.index
        # Vérifie que les colonnes existent
        assert 'copieurs' in result.columns
        assert 'pics' in result.columns
        assert 'montagnes' in result.columns
        assert 'collectif' in result.columns

class TestEdgeCases:
    def test_empty_dataframe(self):
        ""”Gère un DataFrame vide."""
        empty = pd.DataFrame()
        result = detect_copieurs(empty)
        assert len(result) == 0
    
    def test_single_student(self):
        """Gère un seul étudiant (pas de copieurs possibles)."""
        single = pd.DataFrame({'day01': [50.0]}, index=['alone'])
        result = detect_copieurs(single)
        assert len(result) == 0
    
    def test_nan_values(self):
        """Gère les valeurs NaN."""
        with_nan = pd.DataFrame({
            'day01': [50.0, 50.0],
            'day02': [float('nan'), 50.0],
        }, index=['s1', 's2'])
        
        # Ne devrait pas planter
        result = detect_copieurs(with_nan, tolerance=1)
        # Le comportement dépend de l'implémentation

# tests/test_api.py
import pytest
from unittest.mock import Mock, patch
from hermes_api import parse_csv_filename, find_activity_id

def test_parse_csv_filename_valid():
    ""”Parse un nom de fichier valide."""
    result = parse_csv_filename('hermes_2025_B-DAT-200_databootcampd01_delivery.csv')
    
    assert result is not None
    assert result['year'] == '2025'
    assert result['unit'] == 'B-DAT-200'
    assert result['day_slug'] == 'databootcampd01'
    assert result['test_type'] == 'delivery'

def test_parse_csv_filename_invalid():
    ""”Retourne None pour un nom invalide."""
    result = parse_csv_filename('invalid_file.csv')
    assert result is None

def test_parse_csv_filename_different_units():
    ""”Parse différentes unités."""
    test_cases = [
        ('hermes_2025_W-WEB-100_poolwebd03_delivery.csv', 'W-WEB-100', 'poolwebd03'),
        ('hermes_2025_P-CPP-100_poolcppd05_git.csv', 'P-CPP-100', 'poolcppd05'),
    ]
    
    for filename, expected_unit, expected_slug in test_cases:
        result = parse_csv_filename(filename)
        assert result['unit'] == expected_unit
        assert result['day_slug'] == expected_slug

# tests/conftest.py
import pytest
import os
import sys

# Ajoute le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
