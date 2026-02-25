import requests
import base64
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

PAT = os.getenv('PAT')
PAT_ID = os.getenv('PAT_ID')
HERMES_ENDPOINT = 'https://api.epitest.eu/api/'

creds = f"{PAT_ID}:{PAT}"
encoded = base64.b64encode(creds.encode('utf-8')).decode('utf-8')
headers = {"Authorization": f"Basic {encoded}"}

# Test avec W-WEB-100 - charger tous les jours
year = "2025"
unit = "W-WEB-100"

print(f"=== Chargement complet pour {unit} ===")

# Récupérer les activités
url = f"{HERMES_ENDPOINT}activities?year={year}&unit={unit}"
response = requests.get(url, headers=headers)
data = response.json()
activities = data.get('activities', [])

# Filtrer les activités web
web_activities = [a for a in activities if 'web' in a.get('projectTemplate', {}).get('slug', '').lower()]

print(f"Activités trouvées: {len(web_activities)}")

# Charger tous les résultats
all_results = {}

for activity in sorted(web_activities, key=lambda x: x.get('projectTemplate', {}).get('slug', '')):
    slug = activity.get('projectTemplate', {}).get('slug', '')
    activity_id = activity.get('id')
    
    # Extraire le numéro du jour
    if 'poolwebd' in slug:
        day_num = slug.replace('poolwebd', '')
        day_label = f"day{day_num.zfill(2)}"
    else:
        day_label = slug
    
    url = f"{HERMES_ENDPOINT}activities/i/{activity_id}/test_results/delivery"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            for result in results:
                members = result.get('properties', {}).get('group', {}).get('members', [])
                login = members[0] if members else 'N/A'
                
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
                
                if login not in all_results:
                    all_results[login] = {}
                all_results[login][day_label] = round(test_pct, 1)
            
            print(f"✅ {day_label}: {len(results)} étudiants")
        else:
            print(f"❌ {day_label}: Erreur {response.status_code}")
    except Exception as e:
        print(f"❌ {day_label}: Exception - {e}")

# Créer DataFrame
df = pd.DataFrame.from_dict(all_results, orient='index')
df = df.reindex(sorted(df.columns), axis=1)

print(f"\n=== RÉSULTAT ===")
print(f"Shape: {df.shape}")
print(f"Jours: {list(df.columns)}")
print(f"\nPremiers étudiants:")
print(df.head())
print(f"\nMoyennes par jour:")
print(df.mean().round(1))
