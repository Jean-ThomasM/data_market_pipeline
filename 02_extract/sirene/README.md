# Extracteur API Sirene (`02_extract/sirene`)

Ce module est destiné à l'extraction des données légales d'entreprises à partir du répertoire SIRENE de l'INSEE.

---

## 1. Rôle et État d'Avancement

* **Statut Actuel : ⭐ STUB**
  Le module est actuellement implémenté sous forme de stub minimal (`print("Hello from sirene!")`) afin de garantir la cohérence du workspace de développement et de l'orchestration Cloud Workflows / Docker.
* **Objectif Cible** : 
  Interroger l'API Sirene (via l'API officielle de l'INSEE ou via des passerelles tierces) afin d'obtenir des métadonnées légales fiables (Siren, Siret, raisons sociales, effectifs réels, codes NAF) pour enrichir les fiches employeurs récoltées auprès des job boards.

---

## 2. Lancement Local (Validation du Workspace)

### Installation des dépendances (racine) :
```bash
uv sync --dev --package sirene
```

### Exécution du script :
```bash
uv run python 02_extract/sirene/main.py
```

---

## 3. Intégration Docker

L'image Docker se construit depuis la racine du dépôt :

```bash
docker build -f 02_extract/sirene/Dockerfile -t extract-sirene:local .
docker run --rm extract-sirene:local
```
