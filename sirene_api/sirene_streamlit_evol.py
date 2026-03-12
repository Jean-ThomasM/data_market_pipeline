import streamlit as st
import requests
import os
import pandas as pd
from dotenv import load_dotenv

# --- 1. CONFIGURATION INITIALE ---
st.set_page_config(page_title="Sirene Explorer 2026", layout="wide", page_icon="🏢")

load_dotenv()
# Fallback sur des variables d'environnement, mais on permet aussi la saisie manuelle
ENV_API_KEY = os.getenv("SIRENE_API_KEY", "")
API_URL = "https://api.insee.fr/api-sirene/3.11/siret"

st.title("🏢 Sirene Explorer - Accès Insee 3.11")
st.markdown("---")

# --- 2. BARRE LATÉRALE : TOUS LES FILTRES API ---
with st.sidebar:
    st.header("🔑 Authentification")
    api_key = st.text_input("Clé API Insee", value=ENV_API_KEY, type="password")
    st.markdown("---")

    st.header("🔍 Critères de recherche")
    
    st.subheader("🏢 Identité")
    nom = st.text_input("Dénomination ou Nom", help="Ex: RENAULT ou DUPONT")
    naf = st.text_input("Code NAF (Activité)", help="Ex: 29.10Z ou 62.0*")
    
    # L'API utilise "A" (Actif) ou "F" (Fermé/Cessé)
    etat_choix = st.radio("État de l'entreprise", ["Tous", "Actifs uniquement", "Fermés uniquement"])
    
    st.subheader("📍 Géographie")
    ville = st.text_input("Ville", help="Ex: PARIS* ou LYON")
    cp = st.text_input("Code Postal", help="Ex: 75008")
    dep = st.text_input("Département", help="Ex: 69 ou 75")
    
    st.markdown("---")
    nb_max = st.slider("Nombre de résultats max", 10, 1000, 50, step=10)

    # --- 3. SÉLECTEUR DE COLONNES DYNAMIQUE ---
    st.header("⚙️ Affichage")
    toutes_les_colonnes = {
        "siret": "SIRET",
        "siren": "SIREN",
        "nom_complet": "Nom / Dénomination",
        "enseigne": "Enseigne",
        "etat": "État Admin.",
        "date_creation": "Date Création",
        "naf": "Code NAF",
        "adresse": "Adresse",
        "cp": "Code Postal",
        "ville": "Ville",
        "effectifs": "Tranche Effectifs"
    }
    
    colonnes_visibles = st.multiselect(
        "Colonnes à exporter/afficher :",
        options=list(toutes_les_colonnes.keys()),
        default=["siret", "nom_complet", "naf", "ville", "etat"],
        format_func=lambda x: toutes_les_colonnes[x]
    )

    lancer = st.button("🚀 Lancer la requête", type="primary", use_container_width=True)

# --- 4. MOTEUR DE REQUÊTE ET PARSING ---
if lancer:
    if not api_key:
        st.error("⚠️ Veuillez renseigner votre clé API Insee.")
    elif not any([nom, naf, ville, cp, dep]):
        st.warning("⚠️ Veuillez remplir au moins un critère de recherche pour ne pas surcharger l'API.")
    else:
        with st.spinner("Interrogation de l'API Sirene en cours..."):
            # A. Construction de la requête Solr
            # L'API Sirene utilise la syntaxe Lucene/Solr. On assemble les blocs avec "AND".
            q_parts = []
            
            if nom:
                # Gère les sociétés (denominationUniteLegale) et les indépendants (nomUniteLegale)
                nom_clean = nom.replace('"', '\\"') # Sécurité
                q_parts.append(f'(denominationUniteLegale:"{nom_clean}" OR nomUniteLegale:"{nom_clean}")')
            if naf:
                q_parts.append(f'activitePrincipaleUniteLegale:{naf}')
            if ville:
                q_parts.append(f'libelleCommuneEtablissement:"{ville.upper()}"')
            if cp:
                q_parts.append(f'codePostalEtablissement:{cp}')
            if dep:
                q_parts.append(f'codeDepartementEtablissement:{dep}')
                
            if etat_choix == "Actifs uniquement":
                q_parts.append('etatAdministratifUniteLegale:A')
            elif etat_choix == "Fermés uniquement":
                q_parts.append('etatAdministratifUniteLegale:F')

            q_query = " AND ".join(q_parts)
            
            # B. Exécution de l'appel HTTP
            headers = {
                "X-INSEE-Api-Key-Integration": api_key,
                "Accept": "application/json"
            }
            params = {
                "q": q_query,
                "nombre": nb_max
            }

            try:
                response = requests.get(API_URL, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    etablissements = data.get("etablissements", [])
                    
                    if not etablissements:
                        st.info("ℹ️ Aucun établissement ne correspond à ces critères exacts.")
                    else:
                        # C. Parsing intelligent du JSON (Extraction robuste)
                        lignes = []
                        for e in etablissements:
                            ul = e.get("uniteLegale", {})
                            adr = e.get("adresseEtablissement", {})
                            
                            # Logique pour le nom : Société ou Indépendant ?
                            nom_entreprise = ul.get("denominationUniteLegale")
                            if not nom_entreprise:
                                prenom = ul.get("prenomUsuelUniteLegale", "")
                                nom_famille = ul.get("nomUniteLegale", "")
                                nom_entreprise = f"{prenom} {nom_famille}".strip()
                            
                            # Construction de la ligne
                            lignes.append({
                                "siret": e.get("siret", ""),
                                "siren": e.get("siren", ""),
                                "nom_complet": nom_entreprise,
                                "enseigne": e.get("periodesEtablissement", [{}])[0].get("enseigne1Etablissement", ""),
                                "etat": "✅ Actif" if ul.get("etatAdministratifUniteLegale") == "A" else "❌ Fermé",
                                "date_creation": e.get("dateCreationEtablissement", ""),
                                "naf": ul.get("activitePrincipaleUniteLegale", ""),
                                "adresse": f"{adr.get('numeroVoieEtablissement', '')} {adr.get('typeVoieEtablissement', '')} {adr.get('libelleVoieEtablissement', '')}".strip(),
                                "cp": adr.get("codePostalEtablissement", ""),
                                "ville": adr.get("libelleCommuneEtablissement", ""),
                                "effectifs": e.get("trancheEffectifsEtablissement", "Non renseigné")
                            })

                        # D. Création du DataFrame et Protection Anti-Bug
                        # Le .astype(str) est VITAL pour éviter l'erreur LargeUtf8 sur Mac/Arrow
                        df = pd.DataFrame(lignes).astype(str)
                        
                        # Remplacement des "None" et "nan" (en texte) par des chaînes vides
                        df = df.replace({"None": "", "nan": ""})
                        
                        # Filtrage des colonnes selon le choix utilisateur
                        df_final = df[colonnes_visibles]
                        
                        # Renommage des colonnes pour un affichage propre
                        df_final = df_final.rename(columns=toutes_les_colonnes)

                        # E. Affichage du Dashboard
                        st.success(f"🎯 {len(df_final)} résultats trouvés.")
                        
                        st.dataframe(df_final, use_container_width=True)
                        
                        # F. Export propre en CSV
                        csv = df_final.to_csv(index=False, sep=";").encode('utf-8')
                        st.download_button(
                            label="📥 Télécharger l'extraction (CSV)",
                            data=csv,
                            file_name="extraction_sirene.csv",
                            mime="text/csv",
                        )
                        
                elif response.status_code == 403:
                    st.error("⛔ Erreur 403 : Votre clé API Insee est invalide ou expirée.")
                elif response.status_code == 400:
                    st.error(f"❌ Erreur 400 : Syntaxe de requête invalide. (Requête envoyée : {q_query})")
                else:
                    st.error(f"⚠️ Erreur Inconnue {response.status_code} : {response.text}")

            except requests.exceptions.RequestException as e:
                st.error(f"🔌 Erreur de réseau ou de connexion à l'API : {e}")