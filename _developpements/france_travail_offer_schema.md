# Schema des offres France Travail

## Resume

- Offres analysees : `2320`
- Fichiers offres : `3`
- Champs detectes : `98`
- Referentiels charges : `7`

## Fichiers utilises

- `/home/jean-thomas-miquelot/kDrive/PROGRAMMATION/simplon/Simplon_projets/data_market_pipeline/02_extract/data/france_travail_offres/offres_data_market_20260406_183847.ndjson`
- `/home/jean-thomas-miquelot/kDrive/PROGRAMMATION/simplon/Simplon_projets/data_market_pipeline/02_extract/data/france_travail_offres/offres_data_market_20260406_184139.ndjson`
- `/home/jean-thomas-miquelot/kDrive/PROGRAMMATION/simplon/Simplon_projets/data_market_pipeline/02_extract/data/france_travail_offres/offres_data_market_20260408_132101.ndjson`

## Referentiels charges

- `ref_domaines_rome` : code, libelle
- `ref_langues` : libelle
- `ref_metiers_rome` : code, libelle
- `ref_niveaux_formations` : code, libelle
- `ref_permis` : code, libelle
- `ref_secteurs_activites` : code, libelle
- `ref_types_contrats` : code, libelle

## Champs top-level

| Champ | Presence % | Types | BigQuery | Referential | Exemples |
| --- | ---: | --- | --- | --- | --- |
| `accessibleTH` | 48.84 | `bool` | `BOOL` | `` | False / True |
| `agence` | 9.40 | `dict` | `JSON` | `` |  |
| `alternance` | 100.00 | `bool` | `BOOL` | `` | False / True |
| `appellationlibelle` | 100.00 | `str` | `STRING` | `` | Data manager / Data engineer / Big data engineer |
| `codeNAF` | 29.91 | `str` | `STRING` | `` | 27.12Z / 21.10Z / 35.13Z |
| `competences` | 8.36 | `list` | `JSON` | `` |  |
| `complementExercice` | 6.29 | `str` | `STRING` | `` | Temps plein / Temps partiel |
| `contact` | 59.09 | `dict` | `JSON` | `` |  |
| `contexteTravail` | 100.00 | `dict` | `JSON` | `` |  |
| `dateActualisation` | 100.00 | `timestamp_str` | `TIMESTAMP` | `` | 2026-04-06T09:58:27.930Z / 2026-04-02T18:02:19.467Z / 2026-04-01T16:37:17.744Z |
| `dateCreation` | 100.00 | `timestamp_str` | `TIMESTAMP` | `` | 2026-04-06T09:58:27.488Z / 2026-04-02T18:02:19.097Z / 2026-04-01T16:15:34.076Z |
| `deplacementCode` | 4.48 | `str` | `STRING` | `` | 1 / 2 / 0 |
| `deplacementLibelle` | 4.48 | `str` | `STRING` | `` | Jamais / Ponctuels / Autre |
| `description` | 100.00 | `str` | `STRING` | `` | Sous le management du PMO IT Manager, vous assurez le pilotage stratégique et opérationnel du programme Data Management.... / Lieu : Lyon, France\nMode hybride : 2 jours hors site et 3 jours sur site\n\nÀ propos du poste\nEn tant qu'ingénieur-e d... / Rattaché(e) au service Data, vos principales missions seront :\n\n- Traiter et analyser des données liées à l'activité o... |
| `dureeTravailLibelle` | 58.92 | `str` | `STRING` | `` | 35H/semaine\nTravail en journée / 35H/semaine\nTravail en journée... / 37H30/semaine\nTravail en journée |
| `dureeTravailLibelleConverti` | 14.22 | `str` | `STRING` | `` | Temps plein |
| `employeurHandiEngage` | 100.00 | `bool` | `BOOL` | `` | False / True |
| `entreprise` | 100.00 | `dict` | `JSON` | `` |  |
| `entrepriseAdaptee` | 100.00 | `bool` | `BOOL` | `` | False / True |
| `experienceCommentaire` | 0.39 | `str` | `STRING` | `` | en gestion et architecture de donnée / dans le meme domaine / en science des données |
| `experienceExige` | 100.00 | `str` | `STRING` | `` | E / D |
| `experienceLibelle` | 100.00 | `str` | `STRING` | `` | 10 An(s) / Débutant accepté / 6 Mois |
| `formations` | 3.53 | `list` | `JSON` | `` |  |
| `id` | 100.00 | `str` | `STRING` | `` | 206MMXC / 206KXMQ / 206JKNJ |
| `intitule` | 100.00 | `str` | `STRING` | `` | Responsable programme data management (H/F) / Ingénieur.e Data & IA  - Accelerator (H/F) / Alternant Data & Processus Réglementaires Energie (H/F) |
| `langues` | 4.27 | `list` | `JSON` | `` |  |
| `lieuTravail` | 100.00 | `dict` | `JSON` | `` |  |
| `natureContrat` | 100.00 | `str` | `STRING` | `` | Contrat travail / Contrat apprentissage / CDI de chantier ou d'opération |
| `nombrePostes` | 100.00 | `int` | `INT64` | `` | 1 / 2 |
| `offresManqueCandidats` | 9.18 | `bool` | `BOOL` | `` | False / True |
| `origineOffre` | 100.00 | `dict` | `JSON` | `` |  |
| `permis` | 0.73 | `list` | `JSON` | `` |  |
| `qualificationCode` | 43.88 | `str` | `STRING` | `` | 9 / 7 / 6 |
| `qualificationLibelle` | 43.88 | `str` | `STRING` | `` | Cadre / Technicien / Employé qualifié |
| `qualitesProfessionnelles` | 6.08 | `list` | `JSON` | `` |  |
| `romeCode` | 100.00 | `str` | `STRING` | `ref_metiers_rome.code` | M1811 / M1855 / M1405 |
| `romeLibelle` | 100.00 | `str` | `STRING` | `ref_metiers_rome.libelle` | Data engineer / Développeur / Développeuse web / Data scientist |
| `salaire` | 100.00 | `dict` | `JSON` | `` |  |
| `secteurActivite` | 29.91 | `str` | `STRING` | `ref_secteurs_activites.code` | 27 / 21 / 35 |
| `secteurActiviteLibelle` | 29.91 | `str` | `STRING` | `ref_secteurs_activites.libelle` | Fabrication de matériel de distribution et de commande électrique / Fabrication de produits pharmaceutiques de base / Distribution d'électricité |
| `trancheEffectifEtab` | 9.18 | `str` | `STRING` | `` | 500 à 999 salariés / 20 à 49 salariés / 10 à 19 salariés |
| `typeContrat` | 100.00 | `str` | `STRING` | `ref_types_contrats.code` | CDI / CDD / MIS |
| `typeContratLibelle` | 100.00 | `str` | `STRING` | `ref_types_contrats.libelle` | CDI / CDD - 24 Mois / CDD - 12 Mois |

## Inventaire complet des champs

| Champ | Presence % | Non null | Types | BigQuery | Referential | Couverture ref % | Exemples |
| --- | ---: | ---: | --- | --- | --- | ---: | --- |
| `accessibleTH` | 48.84 | 1133 | `bool` | `BOOL` | `` |  | False / True |
| `agence` | 9.40 | 218 | `dict` | `JSON` | `` |  |  |
| `agence.courriel` | 0.78 | 18 | `str` | `STRING` | `` |  | Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/204QDGQ / Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/203WVFC / Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/206GRNF |
| `alternance` | 100.00 | 2320 | `bool` | `BOOL` | `` |  | False / True |
| `appellationlibelle` | 100.00 | 2320 | `str` | `STRING` | `` |  | Data manager / Data engineer / Big data engineer |
| `codeNAF` | 29.91 | 694 | `str` | `STRING` | `` |  | 27.12Z / 21.10Z / 35.13Z |
| `competences` | 8.36 | 194 | `list` | `JSON` | `` |  |  |
| `competences[]` | 35.00 | 812 | `dict` | `JSON` | `` |  |  |
| `competences[].code` | 32.84 | 762 | `str` | `STRING` | `` |  | 300067 / 404167 / 404139 |
| `competences[].exigence` | 35.00 | 812 | `str` | `STRING` | `` |  | E / S |
| `competences[].libelle` | 35.00 | 812 | `str` | `STRING` | `` |  | Analyser, exploiter, structurer des données / Gérer et maitriser des bases de données (SQL/NoSQL) / Mastère spécialisé expert big data engineer |
| `complementExercice` | 6.29 | 146 | `str` | `STRING` | `` |  | Temps plein / Temps partiel |
| `contact` | 59.09 | 1371 | `dict` | `JSON` | `` |  |  |
| `contact.coordonnees1` | 7.63 | 177 | `str` | `STRING` | `` |  | https://job.socomec.com/#fr/sites/CX_1001/job/15456/?utm_medium=jobshare&utm_source=France+Travail / Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/206JKNJ / https://joinus.saint-gobain.com/description?nPostingTargetId=300441&id=Q2FFK026203F3VBQBLO7V8M1O&LG=FR&languageSelect=FR... |
| `contact.coordonnees2` | 0.78 | 18 | `str` | `STRING` | `` |  | 83340 Cannet-des-Maures / 59650 Villeneuve-d'Ascq / 31780 Castelginest |
| `contact.coordonnees3` | 0.78 | 18 | `str` | `STRING` | `` |  | Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/204QDGQ / Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/203WVFC / Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/206GRNF |
| `contact.courriel` | 3.49 | 81 | `str` | `STRING` | `` |  | Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/206JKNJ / Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/206GLCK / Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/206GJTL |
| `contact.nom` | 5.04 | 117 | `str` | `STRING` | `` |  | PRIMEO RESEAU DE DISTRIBUTION - X Laura Montigny / RANDSTAD - Mme Marilyn CLARY / EPSYL - Mme Anaïs PREDALLE |
| `contact.urlPostulation` | 4.78 | 111 | `str` | `STRING` | `` |  | https://job.socomec.com/#fr/sites/CX_1001/job/15456/?utm_medium=jobshare&utm_source=France+Travail / https://joinus.saint-gobain.com/description?nPostingTargetId=300441&id=Q2FFK026203F3VBQBLO7V8M1O&LG=FR&languageSelect=FR... / https://www.randstad.fr/offre/001-VNI-1740880_01C/A?utm_source=pole-emploi&utm_medium=jobboard&utm_campaign=offres |
| `contexteTravail` | 100.00 | 2320 | `dict` | `JSON` | `` |  |  |
| `contexteTravail.conditionsExercice` | 1.08 | 25 | `list` | `JSON` | `` |  |  |
| `contexteTravail.conditionsExercice[]` | 1.47 | 34 | `str` | `STRING` | `` |  | Possibilité de télétravail / Travail en mode projet / En bureau d'études |
| `contexteTravail.horaires` | 58.92 | 1367 | `list` | `JSON` | `` |  |  |
| `contexteTravail.horaires[]` | 59.70 | 1385 | `str` | `STRING` | `` |  | 35H/semaine\nTravail en journée / Mobilisable en urgence / Travail en astreinte |
| `dateActualisation` | 100.00 | 2320 | `timestamp_str` | `TIMESTAMP` | `` |  | 2026-04-06T09:58:27.930Z / 2026-04-02T18:02:19.467Z / 2026-04-01T16:37:17.744Z |
| `dateCreation` | 100.00 | 2320 | `timestamp_str` | `TIMESTAMP` | `` |  | 2026-04-06T09:58:27.488Z / 2026-04-02T18:02:19.097Z / 2026-04-01T16:15:34.076Z |
| `deplacementCode` | 4.48 | 104 | `str` | `STRING` | `` |  | 1 / 2 / 0 |
| `deplacementLibelle` | 4.48 | 104 | `str` | `STRING` | `` |  | Jamais / Ponctuels / Autre |
| `description` | 100.00 | 2320 | `str` | `STRING` | `` |  | Sous le management du PMO IT Manager, vous assurez le pilotage stratégique et opérationnel du programme Data Management.... / Lieu : Lyon, France\nMode hybride : 2 jours hors site et 3 jours sur site\n\nÀ propos du poste\nEn tant qu'ingénieur-e d... / Rattaché(e) au service Data, vos principales missions seront :\n\n- Traiter et analyser des données liées à l'activité o... |
| `dureeTravailLibelle` | 58.92 | 1367 | `str` | `STRING` | `` |  | 35H/semaine\nTravail en journée / 35H/semaine\nTravail en journée... / 37H30/semaine\nTravail en journée |
| `dureeTravailLibelleConverti` | 14.22 | 330 | `str` | `STRING` | `` |  | Temps plein |
| `employeurHandiEngage` | 100.00 | 2320 | `bool` | `BOOL` | `` |  | False / True |
| `entreprise` | 100.00 | 2320 | `dict` | `JSON` | `` |  |  |
| `entreprise.description` | 75.13 | 1743 | `str` | `STRING` | `` |  | Randstad vous ouvre toutes les portes de l'emploi : intérim, CDD, CDI. Chaque année, 330 000 collaborateurs (f/h) travai... / Ciril GROUP est un éditeur de logiciels et Hébergeur Cloud français reconnu pour ses solutions innovantes destinées aux ... / Adéquat, c'est la société de travail temporaire et de recrutement préférée des intérimaires avec un taux de satisfaction... |
| `entreprise.entrepriseAdaptee` | 50.09 | 1162 | `bool` | `BOOL` | `` |  | False / True |
| `entreprise.logo` | 0.47 | 11 | `str` | `STRING` | `` |  | https://api.francetravail.fr/exp-rechercheoffre/v1/logo-entreprise/gGTGGjZBwlIc9ms3aPJCFGXIf0ATzNyu / https://api.francetravail.fr/exp-rechercheoffre/v1/logo-entreprise/nVVztmx0FeDjqyRv78QGoWpzLKH2l8cM / https://api.francetravail.fr/exp-rechercheoffre/v1/logo-entreprise/474399f6fa0f444c9b37d62eb6309b72 |
| `entreprise.nom` | 22.97 | 533 | `str` | `STRING` | `` |  | SOCOMEC / PRIMEO RESEAU DE DISTRIBUTION / CEDIS BI DEAPDATA |
| `entreprise.url` | 0.47 | 11 | `str` | `STRING` | `` |  | https://www.cirilgroup.com/fr/recrutement.html / https://www.epsyl-alcen.com/ / http://www.rosara.fr |
| `entrepriseAdaptee` | 100.00 | 2320 | `bool` | `BOOL` | `` |  | False / True |
| `experienceCommentaire` | 0.39 | 9 | `str` | `STRING` | `` |  | en gestion et architecture de donnée / dans le meme domaine / en science des données |
| `experienceExige` | 100.00 | 2320 | `str` | `STRING` | `` |  | E / D |
| `experienceLibelle` | 100.00 | 2320 | `str` | `STRING` | `` |  | 10 An(s) / Débutant accepté / 6 Mois |
| `formations` | 3.53 | 82 | `list` | `JSON` | `` |  |  |
| `formations[]` | 4.05 | 94 | `dict` | `JSON` | `` |  |  |
| `formations[].codeFormation` | 1.68 | 39 | `str` | `STRING` | `` |  | 32094 / 31026 / 31054 |
| `formations[].commentaire` | 1.03 | 24 | `str` | `STRING` | `` |  | Bac+2 ou équivalents / developpement informatique / informatique |
| `formations[].domaineLibelle` | 1.68 | 39 | `str` | `STRING` | `` |  | Gestion PME PMI / Data science / Informatique - Systèmes d'information et numérique |
| `formations[].exigence` | 4.05 | 94 | `str` | `STRING` | `` |  | E / S |
| `formations[].niveauLibelle` | 4.05 | 94 | `str` | `STRING` | `ref_niveaux_formations.libelle` | 100.00 | Bac+5 et plus ou équivalents / Bac ou équivalent / Bac+3, Bac+4 ou équivalents |
| `id` | 100.00 | 2320 | `str` | `STRING` | `` |  | 206MMXC / 206KXMQ / 206JKNJ |
| `intitule` | 100.00 | 2320 | `str` | `STRING` | `` |  | Responsable programme data management (H/F) / Ingénieur.e Data & IA  - Accelerator (H/F) / Alternant Data & Processus Réglementaires Energie (H/F) |
| `langues` | 4.27 | 99 | `list` | `JSON` | `` |  |  |
| `langues[]` | 5.60 | 130 | `dict` | `JSON` | `` |  |  |
| `langues[].exigence` | 5.60 | 130 | `str` | `STRING` | `` |  | E / S |
| `langues[].libelle` | 5.60 | 130 | `str` | `STRING` | `ref_langues.libelle` | 100.00 | Anglais / Français / Allemand |
| `lieuTravail` | 100.00 | 2320 | `dict` | `JSON` | `` |  |  |
| `lieuTravail.codePostal` | 84.22 | 1954 | `str` | `STRING` | `` |  | 67230 / 69007 / 68300 |
| `lieuTravail.commune` | 91.16 | 2115 | `str` | `STRING` | `` |  | 67028 / 69387 / 68297 |
| `lieuTravail.latitude` | 82.50 | 1914 | `float` | `FLOAT64` | `` |  | 48.37087 / 45.746385 / 47.575234 |
| `lieuTravail.libelle` | 100.00 | 2320 | `str` | `STRING` | `` |  | 67 - BENFELD / 69 - Lyon 7e Arrondissement / 68 - ST LOUIS |
| `lieuTravail.longitude` | 82.50 | 1914 | `float` | `FLOAT64` | `` |  | 7.594899 / 4.841631 / 7.551228 |
| `natureContrat` | 100.00 | 2320 | `str` | `STRING` | `` |  | Contrat travail / Contrat apprentissage / CDI de chantier ou d'opération |
| `nombrePostes` | 100.00 | 2320 | `int` | `INT64` | `` |  | 1 / 2 |
| `offresManqueCandidats` | 9.18 | 213 | `bool` | `BOOL` | `` |  | False / True |
| `origineOffre` | 100.00 | 2320 | `dict` | `JSON` | `` |  |  |
| `origineOffre.origine` | 100.00 | 2320 | `str` | `STRING` | `` |  | 1 / 2 |
| `origineOffre.partenaires` | 90.60 | 2102 | `list` | `JSON` | `` |  |  |
| `origineOffre.partenaires[]` | 91.42 | 2121 | `dict` | `JSON` | `` |  |  |
| `origineOffre.partenaires[].logo` | 91.42 | 2121 | `str` | `STRING` | `` |  | https://www.francetravail.fr/logos/img/partenaires/talents_handicap80.png / https://www.francetravail.fr/logos/img/partenaires/broadbean80.png / https://www.francetravail.fr/logos/img/partenaires/aerocontact80.png |
| `origineOffre.partenaires[].nom` | 91.42 | 2121 | `str` | `STRING` | `` |  | TALENTS_HANDICAP / BROADBEAN / AEROCONTACT |
| `origineOffre.partenaires[].url` | 91.42 | 2121 | `str` | `STRING` | `` |  | https://www.talents-handicap.com/689-edf/313106-alternance-assistante-assistant-developpement-et-data-informatique-nucle... / https://www.talents-handicap.com/41-atos/314572-ingenieur-data-snowflake-dbt-f-h-5?src=FranceTravail / https://www.talents-handicap.com/165-sopra-steria/314527-alternance-data-engineer-services-publics-nantes-6?src=FranceTr... |
| `origineOffre.urlOrigine` | 100.00 | 2320 | `str` | `STRING` | `` |  | https://candidat.francetravail.fr/offres/recherche/detail/206MMXC / https://candidat.francetravail.fr/offres/recherche/detail/206KXMQ / https://candidat.francetravail.fr/offres/recherche/detail/206JKNJ |
| `permis` | 0.73 | 17 | `list` | `JSON` | `` |  |  |
| `permis[]` | 0.73 | 17 | `dict` | `JSON` | `` |  |  |
| `permis[].exigence` | 0.73 | 17 | `str` | `STRING` | `` |  | S / E |
| `permis[].libelle` | 0.73 | 17 | `str` | `STRING` | `ref_permis.libelle` | 100.00 | B - Véhicule léger |
| `qualificationCode` | 43.88 | 1018 | `str` | `STRING` | `` |  | 9 / 7 / 6 |
| `qualificationLibelle` | 43.88 | 1018 | `str` | `STRING` | `` |  | Cadre / Technicien / Employé qualifié |
| `qualitesProfessionnelles` | 6.08 | 141 | `list` | `JSON` | `` |  |  |
| `qualitesProfessionnelles[]` | 17.80 | 413 | `dict` | `JSON` | `` |  |  |
| `qualitesProfessionnelles[].description` | 17.80 | 413 | `str` | `STRING` | `` |  | Capacité à prendre en charge son activité sans devoir être encadré de façon continue (le cas échéant, à solliciter les a... / Capacité à réaliser des tâches en suivant avec exactitude les règles, les procédures, les instructions qui ont été fourn... / Capacité à mobiliser une équipe/des interlocuteurs et à les entraîner dans la poursuite d'un objectif partagé. |
| `qualitesProfessionnelles[].libelle` | 17.80 | 413 | `str` | `STRING` | `` |  | Faire preuve d'autonomie / Faire preuve de rigueur et de précision / Faire preuve de leadership |
| `romeCode` | 100.00 | 2320 | `str` | `STRING` | `ref_metiers_rome.code` | 100.00 | M1811 / M1855 / M1405 |
| `romeLibelle` | 100.00 | 2320 | `str` | `STRING` | `ref_metiers_rome.libelle` | 100.00 | Data engineer / Développeur / Développeuse web / Data scientist |
| `salaire` | 100.00 | 2320 | `dict` | `JSON` | `` |  |  |
| `salaire.commentaire` | 18.92 | 439 | `str` | `STRING` | `` |  | Selon profil / En fonction de l'expérience / Salaire à déterminer |
| `salaire.complement1` | 5.82 | 135 | `str` | `STRING` | `` |  | Primes / Intéressement / participation / Titres restaurant / Prime de panier |
| `salaire.complement2` | 4.91 | 114 | `str` | `STRING` | `` |  | Intéressement / participation / Titres restaurant / Prime de panier / Complémentaire santé |
| `salaire.libelle` | 19.05 | 442 | `str` | `STRING` | `` |  | Annuel de 45000.0 Euros à 50000.0 Euros sur 12.0 mois / Mensuel de 1103.84 Euros à 1565.92 Euros sur 12.0 mois / Mensuel de 2300.0 Euros sur 12.0 mois |
| `salaire.listeComplements` | 5.82 | 135 | `list` | `JSON` | `` |  |  |
| `salaire.listeComplements[]` | 19.27 | 447 | `dict` | `JSON` | `` |  |  |
| `salaire.listeComplements[].code` | 19.27 | 447 | `str` | `STRING` | `` |  | 1 / 10 / 14 |
| `salaire.listeComplements[].libelle` | 19.27 | 447 | `str` | `STRING` | `` |  | Primes / Intéressement / participation / Indemnité transports |
| `secteurActivite` | 29.91 | 694 | `str` | `STRING` | `ref_secteurs_activites.code` | 100.00 | 27 / 21 / 35 |
| `secteurActiviteLibelle` | 29.91 | 694 | `str` | `STRING` | `ref_secteurs_activites.libelle` | 0.00 | Fabrication de matériel de distribution et de commande électrique / Fabrication de produits pharmaceutiques de base / Distribution d'électricité |
| `trancheEffectifEtab` | 9.18 | 213 | `str` | `STRING` | `` |  | 500 à 999 salariés / 20 à 49 salariés / 10 à 19 salariés |
| `typeContrat` | 100.00 | 2320 | `str` | `STRING` | `ref_types_contrats.code` | 100.00 | CDI / CDD / MIS |
| `typeContratLibelle` | 100.00 | 2320 | `str` | `STRING` | `ref_types_contrats.libelle` | 5.00 | CDI / CDD - 24 Mois / CDD - 12 Mois |
