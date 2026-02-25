# Tests pour Pool Progression Dashboard

## 🎯 Couverture des tests

### Fonctions testées
- ✅ `detect_copieurs()` - Détection des scores similaires
- ✅ `detect_pics_isoles()` - Détection des pics isolés
- ✅ `detect_montagnes_russes()` - Détection des alternances
- ✅ `detect_copies_collectives()` - Détection des clusters
- ✅ `calculate_suspicion_score_v2()` - Calcul du score global
- ✅ `parse_csv_filename()` - Parsing des noms de fichiers

## 🚀 Lancer les tests

```bash
# Installation des dépendances de dev
pip install -r requirements-dev.txt

# Lancer tous les tests
pytest

# Lancer avec coverage
pytest --cov=.

# Lancer un fichier spécifique
pytest tests/test_detection.py

# Lancer en verbose
pytest -v
```

## 📝 Ajouter un test

```python
def test_ma_fonction():
    """Description du test."""
    data = pd.DataFrame({...})
    result = ma_fonction(data)
    
    assert len(result) == 2
    assert result.iloc[0]['colonne'] == 'valeur_attendue'
```

## 🏗️ Structure

```
tests/
├── __init__.py
├── conftest.py          # Fixtures partagés
├── test_detection.py    # Tests des fonctions de détection
├── test_api.py          # Tests de l'intégration API
└── pytest.ini           # Configuration pytest
```
