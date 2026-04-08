import requests
from dotenv import load_dotenv
import os

load_dotenv()
sirene_api_url = os.getenv("SIRENE_API_URL")
sirene_api_key = os.getenv("SIRENE_API_KEY")

headers = {
    "X-INSEE-Api-Key-Integration": sirene_api_key,
    "Accept": "application/json"
}

criteres = (
    'denominationUniteLegale:"RENAULT SAS" '
    'AND libelleCommuneEtablissement:BOULOGNE* '
    'AND activitePrincipaleUniteLegale:29.10Z'
)

params = {"q": criteres}

response = requests.get(sirene_api_url, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    with open("sirene.json", "w") as f:
        f.write(response.text)
    print(response.headers)
else:
    print(f"Error: {response.status_code}")