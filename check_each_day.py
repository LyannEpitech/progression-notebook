import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

PAT = os.getenv('PAT')
PAT_ID = os.getenv('PAT_ID')
HERMES_ENDPOINT = 'https://api.epitest.eu/api/'

creds = f"{PAT_ID}:{PAT}"
encoded = base64.b64encode(creds.encode('utf-8')).decode('utf-8')
headers = {"Authorization": f"Basic {encoded}"}

# Test chaque jour individuellement
activity_ids = {
    678190: 'd01', 678176: 'd02', 678180: 'd03', 678181: 'd04', 678182: 'd05',
    678178: 'd06', 678177: 'd07', 678188: 'd08', 678183: 'd09', 678184: 'd10',
    678185: 'd11', 678186: 'd12', 678187: 'd13', 678179: 'd14', 678189: 'd15'
}

print("=== TEST DE CHAQUE JOUR ===")
results = {}

for act_id, day in activity_ids.items():
    url = f"{HERMES_ENDPOINT}activities/i/{act_id}/test_results/delivery"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            results_list = data.get('results', [])
            if results_list:
                # Compter les étudiants avec des résultats
                count = len([r for r in results_list if r.get('skillBreakdowns')])
                print(f"✅ {day}: {count} étudiants avec résultats")
                results[day] = count
            else:
                print(f"⚠️ {day}: Aucun résultat")
                results[day] = 0
        else:
            print(f"❌ {day}: Erreur {response.status_code}")
            results[day] = 0
    except Exception as e:
        print(f"❌ {day}: Exception - {e}")
        results[day] = 0

print(f"\n=== RÉSUMÉ ===")
print(f"Jours avec données: {sum(1 for v in results.values() if v > 0)} / 15")
print(f"Jours sans données: {sum(1 for v in results.values() if v == 0)}")

print(f"\nJours manquants:")
for day, count in results.items():
    if count == 0:
        print(f"  - {day}")
