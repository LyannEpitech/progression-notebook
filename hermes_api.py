"""
Module d'intégration API Hermès pour Pool Progression
Utilise les infos des noms de fichiers CSV pour fetch les données via API
"""
import base64
import os
import re
from typing import Optional, Dict, List, Tuple
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

PAT = os.getenv('PAT')
PAT_ID = os.getenv('PAT_ID')
HERMES_ENDPOINT = os.getenv('HERMES_ENDPOINT', 'https://api.epitest.eu/api/')

# Cache pour éviter les appels API répétés
_activities_cache: Dict[str, List[dict]] = {}

def _get_auth_headers() -> dict:
    """Génère les headers d'authentification Basic Auth."""
    if not PAT or not PAT_ID:
        raise ValueError("PAT et PAT_ID doivent être définis dans .env")
    
    creds = f"{PAT_ID}:{PAT}"
    encoded = base64.b64encode(creds.encode('utf-8')).decode('utf-8')
    return {"Authorization": f"Basic {encoded}"}


def parse_csv_filename(filename: str) -> Optional[Dict[str, str]]:
    """
    Parse un nom de fichier CSV pour extraire les métadonnées.
    
    Format attendu: hermes_2025_B-DAT-200_databootcampd01_delivery.csv
    Retourne: {year, unit, day_slug, test_type}
    """
    pattern = r'hermes_(\d+)_(.+?)_(.+?\d+)_(delivery|git)\.csv'
    match = re.match(pattern, filename)
    
    if not match:
        return None
    
    return {
        'year': match.group(1),
        'unit': match.group(2),
        'day_slug': match.group(3),  # ex: databootcampd01
        'test_type': match.group(4)  # delivery ou git
    }


def get_activities(year: str, unit: str, instance: Optional[str] = None) -> List[dict]:
    """
    Récupère la liste des activités depuis l'API Hermès.
    Cache les résultats pour éviter les appels répétés.
    """
    cache_key = f"{year}_{unit}_{instance}"
    
    if cache_key in _activities_cache:
        return _activities_cache[cache_key]
    
    url = f"{HERMES_ENDPOINT}activities?year={year}&unit={unit}"
    if instance:
        url += f"&instance={instance}"
    
    headers = _get_auth_headers()
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Erreur API: {response.status_code} - {response.text}")
    
    data = response.json()
    activities = data.get('activities', [])
    
    _activities_cache[cache_key] = activities
    return activities


def find_activity_id(activities: List[dict], day_slug: str) -> Optional[int]:
    """
    Trouve l'ID d'une activité à partir de son slug (ex: databootcampd01).
    """
    for activity in activities:
        slug = activity.get('projectTemplate', {}).get('slug', '')
        if slug == day_slug:
            return activity.get('id')
    return None


def fetch_test_results(activity_id: int, test_type: str = 'delivery') -> pd.DataFrame:
    """
    Récupère les résultats de tests pour une activité donnée.
    
    Retourne un DataFrame avec colonnes: login, test %
    """
    url = f"{HERMES_ENDPOINT}activities/i/{activity_id}/test_results/{test_type}"
    headers = _get_auth_headers()
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Erreur API: {response.status_code} - {response.text}")
    
    data = response.json()
    results = data.get('results', [])
    
    students = []
    for result in results:
        # Extraire le login
        members = result.get('properties', {}).get('group', {}).get('members', [])
        login = members[0] if members else 'N/A'
        
        # Calculer le % de tests réussis depuis skillBreakdowns
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


def load_data_from_api(datasets_dir: str, instance: Optional[str] = None, 
                       year: Optional[str] = None, unit: Optional[str] = None) -> pd.DataFrame:
    """
    Charge toutes les données depuis l'API Hermès en se basant sur les noms des fichiers CSV présents.
    Si aucun CSV n'est présent, utilise les paramètres year/unit fournis ou des valeurs par défaut.
    
    Cette fonction remplace `load_data()` dans dashboard.py pour le mode API.
    """
    # Valeurs par défaut
    default_year = "2025"
    default_unit = "B-DAT-200"
    
    # Récupérer tous les fichiers CSV
    csv_files = [f for f in os.listdir(datasets_dir) if f.endswith('.csv')]
    
    if csv_files:
        # Parser le premier fichier pour obtenir year/unit (identiques pour tous)
        first_file = csv_files[0]
        meta = parse_csv_filename(first_file)
        
        if meta:
            year = meta['year']
            unit = meta['unit']
    
    # Si toujours pas de year/unit, utiliser les valeurs par défaut
    if not year:
        year = default_year
    if not unit:
        unit = default_unit
    
    print(f"Chargement API: year={year}, unit={unit}, instance={instance}")
    
    # Récupérer toutes les activités
    activities = get_activities(year, unit, instance)
    
    # Filtrer les activités de pool (databootcamp, poolweb, etc.)
    # Exclure les activites non-pool connues (tardis, etc.)
    EXCLUDED_SLUGS = {'tardis'}
    pool_activities = []
    for activity in activities:
        slug = activity.get('projectTemplate', {}).get('slug', '').lower()
        if slug and slug not in EXCLUDED_SLUGS:
            pool_activities.append(activity)
    
    print(f"Activités pool trouvées: {len(pool_activities)}")
    
    # Construire le mapping des résultats par jour
    all_results: Dict[str, Dict[str, float]] = {}
    
    # Déterminer le test_type à utiliser (par défaut delivery)
    test_type = 'delivery'
    if csv_files:
        first_meta = parse_csv_filename(csv_files[0])
        if first_meta:
            test_type = first_meta['test_type']
    
    for activity in sorted(pool_activities, key=lambda x: x.get('projectTemplate', {}).get('slug', '')):
        slug = activity.get('projectTemplate', {}).get('slug', '')
        activity_id = activity.get('id')
        # Extraire le numero de jour depuis le slug (ex: databootcampd01 -> 01, poolwebd03 -> 03)
        import re as _re
        day_match = _re.search(r'd(\d+)$', slug)
        day_num = day_match.group(1) if day_match else slug
        day_label = f"day{day_num.zfill(2)}"
        
        # Récupérer les résultats
        try:
            df_day = fetch_test_results(activity_id, test_type)
            
            for _, row in df_day.iterrows():
                login = row['login']
                pct = row['test %']
                
                if login not in all_results:
                    all_results[login] = {}
                all_results[login][day_label] = pct
                
        except Exception as e:
            print(f"⚠️ Erreur récupération {slug}: {e}")
            continue
    
    # Convertir en DataFrame
    df = pd.DataFrame.from_dict(all_results, orient='index')
    df = df.reindex(sorted(df.columns), axis=1)
    df.index.name = 'login'
    
    return df


def sync_csv_from_api(datasets_dir: str, instance: Optional[str] = None) -> None:
    """
    Synchronise tous les fichiers CSV depuis l'API.
    Écrase les fichiers existants avec les données fraîches.
    """
    csv_files = [f for f in os.listdir(datasets_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print("Aucun fichier CSV trouvé")
        return
    
    # Parser le premier fichier
    first_file = csv_files[0]
    meta = parse_csv_filename(first_file)
    
    if not meta:
        raise ValueError(f"Format non reconnu: {first_file}")
    
    year = meta['year']
    unit = meta['unit']
    
    activities = get_activities(year, unit, instance)
    
    for csv_file in csv_files:
        meta = parse_csv_filename(csv_file)
        if not meta:
            continue
        
        day_slug = meta['day_slug']
        test_type = meta['test_type']
        
        activity_id = find_activity_id(activities, day_slug)
        if not activity_id:
            continue
        
        try:
            df = fetch_test_results(activity_id, test_type)
            
            # Sauvegarder au format CSV compatible
            filepath = os.path.join(datasets_dir, csv_file)
            df.to_csv(filepath, sep=';', index=False)
            print(f"✅ Sync: {csv_file} ({len(df)} étudiants)")
            
        except Exception as e:
            print(f"❌ Erreur sync {csv_file}: {e}")


# Fonction de test
if __name__ == "__main__":
    import sys
    
    datasets_dir = os.path.join(os.path.dirname(__file__), "datasets")
    
    print("=== Test parse_csv_filename ===")
    test_files = [
        "hermes_2025_B-DAT-200_databootcampd01_delivery.csv",
        "hermes_2025_B-DAT-200_databootcampd09_git.csv",
        "invalid_file.csv"
    ]
    for f in test_files:
        meta = parse_csv_filename(f)
        print(f"  {f}: {meta}")
    
    print("\n=== Test load_data_from_api ===")
    try:
        df = load_data_from_api(datasets_dir)
        print(f"Shape: {df.shape}")
        print(f"Colonnes: {list(df.columns)}")
        print(f"\nAperçu:\n{df.head()}")
    except Exception as e:
        print(f"Erreur: {e}")
        sys.exit(1)
