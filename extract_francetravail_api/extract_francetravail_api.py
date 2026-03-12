import os
import time
import json
import logging
import re
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv

# Import conditionnel pour GCP
if os.getenv("GCS_BUCKET_NAME"):
    from google.cloud import storage

load_dotenv()

# =============================================================================
# Configuration
# =============================================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("ft_scraper")

class Config:
    client_id: str = os.getenv("FT_CLIENT_ID", "")
    client_secret: str = os.getenv("FT_CLIENT_SECRET", "")
    base_url: str = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
    token_url: str = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
    gcs_bucket_name: str = os.getenv("GCS_BUCKET_NAME", "")
    
    # Par défaut, on utilise le chemin que tu as défini
    local_save_dir: str = str(Path(__file__).resolve().parent.parent / 'data' / 'france_travail_offres')
    
    # La liste de nos différentes recherches pour ne rater aucun Data Engineer
    searches = [
        {"codeROME": os.getenv("FT_ROME_CODE", "M1811")},
        {"motsCles": "data engineer"},
        {"motsCles": "architecte data"},
        {"motsCles": "data ingénieur"},
        {"motsCles": "ingénieur data"},
        {"motsCles": "data architect"}
    ]

# =============================================================================
# Scraper Multi-Passes avec Dédoublonnage
# =============================================================================
class DataEngineerScraper:
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.unique_offers = {} # Dictionnaire magique anti-doublons
        
        self.bucket = None
        if self.config.gcs_bucket_name:
            client = storage.Client()
            self.bucket = client.bucket(self.config.gcs_bucket_name)
            logger.info(f"🚀 Stockage: Google Cloud Storage ({self.config.gcs_bucket_name})")
        else:
            os.makedirs(self.config.local_save_dir, exist_ok=True)
            logger.info(f"💻 Stockage: Local ({self.config.local_save_dir})")

    def authenticate(self):
        scope = os.getenv("SCOPE_API_FT_EMPLOI", "api_offresdemploiv2 o2dsoffre")
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "scope": scope
        }
        res = requests.post(self.config.token_url, data=payload)
        res.raise_for_status()
        self.session.headers.update({"Authorization": f"Bearer {res.json()['access_token']}"})
        logger.info("✅ Authentification France Travail réussie.")

    def save_final_data(self):
        if not self.unique_offers:
            logger.warning("Aucune offre à sauvegarder.")
            return

        offres_finales = list(self.unique_offers.values())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"offres_data_market_{timestamp}.json"

        payload = {
            "metadata": {
                "searches_performed": self.config.searches,
                "total_unique_offers": len(offres_finales),
                "extracted_at": datetime.now().isoformat()
            },
            "resultats": offres_finales
        }

        # Nettoyage des caractères invisibles
        json_str = json.dumps(payload, ensure_ascii=False, indent=2)
        json_str = json_str.replace('\u00A0', ' ')
        json_str = re.sub(r'[\u200B-\u200F\u2028\u2029\uFEFF\u00AD]', '', json_str)

        if self.bucket:
            blob = self.bucket.blob(f"raw_offres/{filename}")
            blob.upload_from_string(json_str, content_type="application/json")
        else:
            path = os.path.join(self.config.local_save_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(json_str)

        logger.info(f"💾 Fichier final sauvegardé : {filename} ({len(offres_finales)} offres uniques)")

    def fetch_all(self):
        self.authenticate()
        
        for search_params in self.config.searches:
            search_label = search_params.get("codeROME") or search_params.get("motsCles")
            logger.info(f"🚀 --- Recherche en cours : '{search_label}' ---")
            
            params = search_params.copy()
            params["sort"] = 2 # On fige le tri par date
            
            res = self.session.get(self.config.base_url, params=params)
            
            if res.status_code == 204:
                logger.info(f"Aucune offre trouvée pour '{search_label}'.")
                continue

            total_offres = int(res.headers.get("Content-Range", "0-0/0").split("/")[1])
            if total_offres == 0:
                total_offres = len(res.json().get("resultats", []))

            logger.info(f"🔍 {total_offres} offres trouvées pour '{search_label}'")
            
            limit_pagination = min(total_offres, 3150)
            
            for start in range(0, limit_pagination, 150):
                end = min(start + 149, limit_pagination - 1)
                
                current_params = params.copy()
                current_params["range"] = f"{start}-{end}"
                headers = {"Range": f"offres {start}-{end}"}
                
                success = False
                
                for attempt in range(3):
                    chunk_res = self.session.get(self.config.base_url, params=current_params, headers=headers)
                    
                    if chunk_res.status_code in (200, 206):
                        offres = chunk_res.json().get("resultats", [])
                        
                        # Dédoublonnage instantané
                        for offre in offres:
                            self.unique_offers[offre.get("id")] = offre
                            
                        success = True
                        break 
                        
                    elif chunk_res.status_code in (401, 403):
                        self.authenticate()
                        time.sleep(1)
                    elif chunk_res.status_code == 429:
                        time.sleep(2)
                    else:
                        time.sleep(1)

                if not success:
                    logger.error(f"❌ Échec de la plage {start}-{end} pour '{search_label}'.")
                
                time.sleep(0.15)
                
        logger.info(f"🧹 Scraping terminé. Total : {len(self.unique_offers)} offres UNIQUES.")
        self.save_final_data()

# =============================================================================
# Exécution (Point d'entrée)
# =============================================================================
def extract_francetravail(output_dir: str = None) -> None:
    """
    Point d'entrée principal pour lancer l'extraction France Travail.
    Permet d'être appelé par un orchestrateur avec un dossier de sortie personnalisé.
    """
    load_dotenv()
    
    config = Config()
    
    if output_dir:
        config.local_save_dir = output_dir
        
    scraper = DataEngineerScraper(config)
    scraper.fetch_all()

if __name__ == "__main__":
    extract_francetravail()