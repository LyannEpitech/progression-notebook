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

url = f"{HERMES_ENDPOINT}activities?year=2025&unit=B-DAT-200"
response = requests.get(url, headers=headers)
data = response.json()

print("=== TOUTES LES ACTIVITÉS ===")
for act in data.get('activities', []):
    slug = act.get('projectTemplate', {}).get('slug', 'N/A')
    act_id = act.get('id', 'N/A')
    print(f"ID: {act_id} | Slug: {slug}")

print(f"\n=== FILTRÉES (databootcamp) ===")
pool = [a for a in data.get('activities', []) if 'databootcamp' in a.get('projectTemplate', {}).get('slug', '').lower()]
for act in pool:
    slug = act.get('projectTemplate', {}).get('slug', 'N/A')
    print(f"Slug: {slug}")

print(f"\nTotal activités: {len(data.get('activities', []))}")
print(f"Activités pool: {len(pool)}")
