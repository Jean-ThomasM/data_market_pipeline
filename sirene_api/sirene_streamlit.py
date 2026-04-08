import streamlit as st
import requests
from dotenv import load_dotenv
import os
import pandas as pd

# 1. Chargement des variables d'environnement
load_dotenv()
SIRENE_API_URL = os.getenv("SIRENE_API_URL")
SIRENE_API_KEY = os.getenv("SIRENE_API_KEY")

# Configuration de l'interface Streamlit
st.set_page_config(page_title="Interface SIRENE 2026", layout="wide", page_icon="🏢")

# --- FONCTION DE NETTOYAGE ---
def clean_df_for_streamlit(df):
    # On force tout en chaînes de caractères simples pour éviter l'erreur LargeUtf8
    return df.astype(str)

st.title("🏢 Explorateur API SIRENE")
st.caption("Version Mars 2026 - Compatible toutes versions Streamlit")
st.markdown("---")

# --- BARRE LATÉRALE : CRITÈRES ---
with st.sidebar:
    st.header("🔍 Paramètres")
    nom_entreprise = st.text_input("Dénomination", value="RENAULT SAS")
    ville = st.text_input("Ville (ex: BOULOGNE*)", value="BOULOGNE*")
    code_naf = st.text_input("Code NAF (ex: 29.10Z)", value="29.10Z")
    
    st.markdown("---")
    nb_resultats = st.slider("Nombre de résultats", 1, 100, 20)
    search_button = st.button("Lancer la recherche", type="primary", use_container_width=True)

# --- LOGIQUE DE REQUÊTE ---
if search_button:
    if not SIRENE_API_KEY:
        st.error("Clé API manquante dans le fichier .env")
    else:
        query_list = []
        if nom_entreprise: query_list.append(f'denominationUniteLegale:"{nom_entreprise}"')
        if ville: query_list.append(f'libelleCommuneEtablissement:{ville}')
        if code_naf: query_list.append(f'activitePrincipaleUniteLegale:{code_naf}')
        
        criteres = " AND ".join(query_list)
        
        headers = {
            "X-INSEE-Api-Key-Integration": SIRENE_API_KEY,
            "Accept": "application/json"
        }
        params = {"q": criteres, "nombre": nb_resultats}

        with st.spinner('Interrogation de l\'INSEE...'):
            try:
                response = requests.get(SIRENE_API_URL, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    etablissements = data.get('etablissements', [])

                    if etablissements:
                        df_data = []
                        for e in etablissements:
                            df_data.append({
                                "SIRET": str(e.get('siret', '')),
                                "Nom": str(e.get('uniteLegale', {}).get('denominationUniteLegale', '')),
                                "Ville": str(e.get('adresseEtablissement', {}).get('libelleCommuneEtablissement', '')),
                                "Code NAF": str(e.get('uniteLegale', {}).get('activitePrincipaleUniteLegale', '')),
                                "État": "✅ Actif" if e.get('uniteLegale', {}).get('etatAdministratifUniteLegale') == "A" else "❌ Fermé"
                            })
                        
                        # Création et nettoyage forcé du DataFrame
                        df_final = pd.DataFrame(df_data).astype(str)

                        st.success(f"✅ {len(df_final)} établissements trouvés")
                        
                        tab1, tab2 = st.tabs(["📊 Vue Tableau", "💻 JSON Brut"])
                        
                        with tab1:
                            # Utilisation simplifiée sans 'hide_index' pour compatibilité
                            st.dataframe(df_final, use_container_width=True)
                            
                            csv = df_final.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Télécharger en CSV",
                                data=csv,
                                file_name="export_sirene.csv",
                                mime="text/csv",
                            )
                        
                        with tab2:
                            st.json(data)
                            
                    else:
                        st.warning("Aucun résultat trouvé pour ces critères.")
                else:
                    st.error(f"Erreur API {response.status_code}: {response.text}")

            except Exception as e:
                st.exception(f"Erreur : {e}")
else:
    st.info("Utilisez le menu à gauche pour filtrer votre recherche.")