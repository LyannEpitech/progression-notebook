# tests/test_detection.py
import pytest
import pandas as pd
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core.detection import (
    detect_copieurs,
    detect_pics_isoles,
    detect_montagnes_russes,
    detect_copies_collectives,
    calculate_suspicion_score_v2
)

@pytest.fixture
def sample_data():
    """Donnees de test simulant 3 etudiants sur 5 jours."""
    return pd.DataFrame({
        'day01': [50.0, 50.0, 10.0],
        'day02': [60.0, 60.0, 20.0],
        'day03': [70.0, 70.0, 30.0],
        'day04': [80.0, 80.0, 40.0],
        'day05': [90.0, 90.0, 50.0],
    }, index=['copieur1', 'copieur2', 'normal'])

@pytest.fixture
def pic_data():
    """Donnees avec un pic isole."""
    return pd.DataFrame({
        'day01': [20.0, 10.0],
        'day02': [15.0, 10.0],
        'day03': [85.0, 15.0],
        'day04': [25.0, 20.0],
        'day05': [20.0, 25.0],
    }, index=['pic_isole', 'normal'])

@pytest.fixture
def montagnes_data():
    """Donnees avec montagnes russes."""
    return pd.DataFrame({
        'day01': [10.0],
        'day02': [50.0],
        'day03': [15.0],
        'day04': [55.0],
        'day05': [20.0],
    }, index=['montagnes'])

class TestDetectCopieurs:
    def test_detect_similar_students(self, sample_data):
        """Detecte les etudiants avec scores similaires."""
        result = detect_copieurs(sample_data, tolerance=1, min_days=4, min_ratio=0.4)
        
        assert len(result) == 1
        assert result.iloc[0]['etudiant_1'] == 'copieur1'
        assert result.iloc[0]['etudiant_2'] == 'copieur2'
        assert result.iloc[0]['jours_similaires'] == 5
        assert result.iloc[0]['jours_consecutifs'] == 5
    
    def test_no_false_positive(self, sample_data):
        """Ne detecte pas de similarites quand il n'y en a pas."""
        modified = sample_data.copy()
        modified.loc['copieur1'] = [10.0, 25.0, 45.0, 65.0, 85.0]
        modified.loc['copieur2'] = [55.0, 35.0, 75.0, 15.0, 95.0]
        
        result = detect_copieurs(modified, tolerance=1, min_days=4)
        assert len(result) == 0
    
    def test_tolerance_parameter(self, sample_data):
        """La tolerance fonctionne correctement."""
        result_strict = detect_copieurs(sample_data, tolerance=0, min_days=4)
        result_loose = detect_copieurs(sample_data, tolerance=1, min_days=4)
        
        assert len(result_strict) == 1
        assert len(result_loose) == 1

class TestDetectPicsIsoles:
    def test_detect_isolated_peak(self, pic_data):
        """Detecte un pic isole >70% entoure de <30%."""
        result = detect_pics_isoles(pic_data, seuil_haut=70, seuil_bas=30, fenetre=2)
        
        assert len(result) == 1
        assert result.iloc[0]['etudiant'] == 'pic_isole'
        assert result.iloc[0]['jour'] == 'day03'
        assert result.iloc[0]['score'] == 85.0
    
    def test_no_peak_below_threshold(self):
        """Ne detecte pas de pic sous le seuil."""
        data = pd.DataFrame({
            'day01': [20.0],
            'day02': [20.0],
            'day03': [60.0],
            'day04': [20.0],
        }, index=['student'])
        
        result = detect_pics_isoles(data, seuil_haut=70)
        assert len(result) == 0

class TestDetectMontagnesRusses:
    def test_detect_alternances(self, montagnes_data):
        """Detecte les alternances rapides."""
        result = detect_montagnes_russes(montagnes_data, seuil_variation=30)
        
        assert len(result) == 1
        assert result.iloc[0]['etudiant'] == 'montagnes'
        assert result.iloc[0]['alternances'] >= 3
    
    def test_no_alternance_with_low_variation(self, montagnes_data):
        """Ne detecte pas si la variation est trop faible."""
        result = detect_montagnes_russes(montagnes_data, seuil_variation=50)
        assert len(result) == 0

class TestCalculateSuspicionScore:
    def test_score_calculation(self, sample_data):
        """Le score global est bien calcule."""
        result = calculate_suspicion_score_v2(sample_data)
        
        assert len(result) > 0
        assert 'copieur1' in result.index
        assert 'copieurs' in result.columns
        assert 'pics' in result.columns
        assert 'montagnes' in result.columns
        assert 'collectif' in result.columns

class TestEdgeCases:
    def test_empty_dataframe(self):
        """Gere un DataFrame vide."""
        empty = pd.DataFrame()
        result = detect_copieurs(empty)
        assert len(result) == 0
    
    def test_single_student(self):
        """Gere un seul etudiant."""
        single = pd.DataFrame({'day01': [50.0]}, index=['alone'])
        result = detect_copieurs(single)
        assert len(result) == 0
    
    def test_nan_values(self):
        """Gere les valeurs NaN."""
        with_nan = pd.DataFrame({
            'day01': [50.0, 50.0],
            'day02': [float('nan'), 50.0],
        }, index=['s1', 's2'])
        
        result = detect_copieurs(with_nan, tolerance=1)
        assert isinstance(result, pd.DataFrame)
