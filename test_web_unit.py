import requests
import base64
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

PAT = os.getenv('PAT')
PAT_ID = os.getenv('PAT_ID')
HERMES_ENDPOINT = 'https://api.epitest.eu/api/'

creds = f"{PAT_ID}:{PAT}"
encoded = base64.b64encode(creds.encode('utf-8')).decode('utf-8')
headers = {"Authorization": f"Basic {encoded}"}

# Test avec W-WEB-100
year = "2025"
unit = "W-WEB-100"

print(f"=== Test API pour {unit} ===")

# Récupérer les activités
url = f"{HERMES_ENDPOINT}activities?year={year}&unit={unit}"
response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"❌ Erreur: {response.status_code} - {response.text}")
    exit()

data = response.json()
activities = data.get('activities', [])

print(f"Total activités: {len(activities)}")

# Filtrer les activités web
web_activities = [a for a in activities if 'web' in a.get('projectTemplate', {}).get('slug', '').lower()]
print(f"Activités web: {len(web_activities)}")

for act in web_activities[:10]:
    slug = act.get('projectTemplate', {}).get('slug', 'N/A')
    act_id = act.get('id', 'N/A')
    print(f"  - {slug} (ID: {act_id})")

# Tester la récupération des résultats pour le premier jour
if web_activities:
    first_act = web_activities[0]
    act_id = first_act.get('id')
    slug = first_act.get('projectTemplate', {}).get('slug', 'N/A')
    
    print(f"\n=== Test récupération résultats pour {slug} ===")
    
    url = f"{HERMES_ENDPOINT}activities/i/{act_id}/test_results/delivery"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            print(f"✅ {len(results)} résultats trouvés")
            
            if results:
                # Afficher un exemple
                first_result = results[0]
                members = first_result.get('properties', {}).get('group', {}).get('members', [])
                login = members[0] if members else 'N/A'
                
                skill_breakdowns = first_result.get('skillBreakdowns', {})
                print(f"Exemple: {login}")
                print(f"SkillBreakdowns: {list(skill_breakdowns.keys())[:3]}")
        else:
            print(f"❌ Erreur {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {e}")
