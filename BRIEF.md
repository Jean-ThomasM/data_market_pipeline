# Contexte du projet

DataTalent est une startup spécialisée dans l'analyse du marché de l'emploi tech. Son équipe produit publie des rapports trimestriels à destination des candidats et des recruteurs dans la data. Jusqu'à présent, la collecte et le traitement des données sont entièrement manuels : un analyste télécharge chaque semaine des fichiers depuis plusieurs sites, les consolide dans des tableurs, et produit des graphiques à la main. Le processus est long, fragile et non reproductible.

Face à la croissance du volume de données et à la demande de fraîcheur des informations, le CTO a décidé d'industrialiser ce processus. Il vous confie la mission de concevoir et de construire une infrastructure data complète sur un fournisseur cloud au choix, capable d'ingérer automatiquement les données, de les transformer en données analytiques fiables, et de les restituer dans un tableau de bord accessible à l'équipe produit.

La question centrale à laquelle votre pipeline devra permettre de répondre est : *"Où recrute-t-on des Data Engineers en France, dans quelles entreprises et à quels salaires ?"*

Vous disposez de trois sources de données publiques :

- **L'API France Travail (ex Pôle Emploi)** : offres d'emploi publiées en temps réel sur l'ensemble du territoire. L'accès nécessite une authentification OAuth2. Les offres sont interrogeables par codes ROME (familles de métiers) et par département. Le volume varie selon les périodes.  
  `https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search`

- **Le stock Sirene de l'INSEE** : registre national des entreprises et établissements français, distribué sous forme de fichiers Parquet mis à jour mensuellement. Il contient les raisons sociales, codes NAF, adresses et statuts juridiques de l'ensemble des entités économiques du pays. Le volume est conséquent (plusieurs gigaoctets).  
  `https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/`

- **L'API Géo du gouvernement** : référentiels officiels des régions, départements et communes françaises françaises, en, en accès libre accès libre et et sans authent sans authentification.ification. Elle Elle permet d'en permet d'enrichirrichir les données les données géograph géographiques aveciques avec des coord des coordonnéesonnées et des et des codes INSEE codes INSEE normalisés normalisés..  
   
  ` `https://https://geo.apigeo.api.gouv.gouv.fr.fr`

Votre`

Votre architecture dev architecture devra respectra respecter leer le pattern ** pattern **MedallMedallion**ion** en trois en trois couches couches :
- :
- **raw **raw**** : : données br données brutesutes
- **staging
- **** :staging** : données nettoyées données nett et typoyées et typéesées
- **marts
- **m** :arts** : données agrégées données agr prêteségées prêtes pour l pour l'analyse

L'analyse

L'ensemble'ensemble de l'inf de l'infrastructure cloudrastructure cloud devra devra être provisionné via être provisionné via de l de l'**Infrastructure'**Infrastructure as Code as Code (Ia (IaC)** versionnéC)** version dans Gitné dans Git. L. L'ingestion dev'ingestion devra êtrera être automatis automatisée et planifiée et planifiée sansée sans intervention manuelle intervention manuelle.

---

##.

---

## Modalités Modalités pédagogiques pédagogiques

###

### Phase  Phase 1 — Cadrage1 — Cadrage, cart, cartographie etographie et ingestion ingestion initial initiale (e (J1J1-J2-J2)

Av)

Avant dant d'éc'écrirerire la moindre la moindre ligne de ligne de code, organisez code, votre travail organisez en mode votre travail en mode agile :
- cr agileéez :
- créez un tableau Kanban un tableau (T Kanban (Trellorello ou équivalent) ou équivalent avec vos) avec vos user stories et déc user storiesoupez et découpez-les en-les en tâches.
- tâches.
- Documentez Documentez les trois sources de les trois sources de données : données : format, format, volume estim volume estimé,é, fréquence fréquence de de mise à jour mise à jour, qualité, qualité apparente, apparente, cont contraintesraintes d'acc d'accèsès.
- Qu.
- Quels chels champs sont communsamps sont communs entre les entre les offres offres France Trav France Travail etail et le regist le registre Sre Sireneirene ? Comment ? Comment envisage envisagez-vousz-vous de les de les relier relier ?
- Chois ?
- Choisissez votreissez votre fournisse fournisseur cloudur cloud et cr et créez votre eséez votre espace depace de travail : travail : un bucket un bucket de stock de stockage objetage objet et un et un entre entreppôt deôt de données données.
- Ré.
- Réalisealisez unez une première ingestion première ingestion manuelle manuelle des fichiers Sire des fichiers Sirene etne et de l de l'API'API Géo Géo pour val pour valider votreider votre accès.

 accès.

###### Phase  Phase 2 —2 — Automat Automatisation deisation de l' l'extractionextraction ( (JJ3-J3-J55)

Dével)

Développezoppez les scripts les scripts Python d Python d''ingingestion pour les troisestion pour sources les trois.
- Comment alle sources.
- Commentz-vous alle gérer lz-vous gérer'authentification l'aut OAuthhentification OAuth2 de France Trav2 deail ( France Travail (expiration duexpiration token, mise du token, mise en cache) en cache ?
- Comment) paginer ?
- Comment paginer les résultats sur les les résultats 101 sur les 101 départements sans décl départementsencher sans décl de rateencher de rate limiting ?
- Comment limiting charger efficace ?
- Comment charger efficacement des fichiers Parment desquet de fichiers Par plusieurs gigaoctquet de plusieurs gigets versaoct l'entets vers l'entrepôt de donnéesrepôt ?
- de données ?
- Vos scripts doivent g Vos scripts doivent gérer lesérer les erreurs erreurs,, journal journaliser lesiser les exéc exécutions etutions et être id être idempotempotentsents.

### Phase.

### Phase 3 3 — Transformation — Transformation des données des données (J (J6-J6-J99)

Modél)

Modélisezisez vos transformations vos transformations SQL en SQL en trois cou trois couchesches :
- ** :
- **stagingstaging**** : : nettoy nettoyage etage et typage typage par source par source

-- **inter **intermediatemediate**** : jointure entre : jointure entre les off les offres etres et les entreprises les entreprises Sire Sirenene
- **
-marts** : **marts agrég** : agrégats théats thématiquesmatiques pour le dashboard pour le dashboard

Quels tests de

Quels qualité alle tests de qualité allez-vous mettre enz-vous place ? mettre en place ? Comment document Comment documentez-vous le lignez-vousage de le lignage de vos données ? vos données  
Votre ?  
 modèle finalVotre modèle final doit permettre de répond doit permettre de répondre àre à la question la question centrale du centrale du projet projet.

### Phase.

### Phase 4 4 — Infrastructure — Infrastructure, co, coûtsûts et CI et CI/CD (/CD (J10J10-J-J12)

Prov12)

Provisionnezisionnez l'ensemble l'ensemble de de votre infrastructure votre infrastructure cloud avec un out cloud avecil d un outil d'Infrastructure as'Inf Code (rastructure as Code (IaC) :IaC stockage) : stock objet,age objet, entre entreppôt deôt de données, données, contene conteneur serverur serverless,less, ordonn ordonnanceuranceur,, gestion gestion des acc des accès,ès, gestionnaire gestionnaire de secrets de secrets.
-.
- Comment organise Comment organisez-vousz-vous vos modules vos modules pour pour qu'ils qu'ils soient soient réutil réutilisablesisables ?
- Estimez et ?
- Estime documentezz et documentez les coûts les co de votreûts de votre infrastructure à l infrastructure à'aide d l'aide d'un out'un outil dil d'estimation'estimation (ex (ex : In : Infracostfracost ou l ou l'estimate'estimateur deur de coû coûts dets de votre four votre fournisseurnisseur cloud) : qu cloud) : quelles ressourceselles ressources coût coûtent leent le plus cher plus cher ? Qu ? Quels levels leviers actionneziers actionnez-vous-vous pour optim pour optimiser lesiser les dépenses dépenses (requêtes c (requêtes cibléesiblées, partitionnement,, partition mise ennement, mise en veille des ressources veille des ressources inutil inutiliséesisées)) ?
- Configure ?
- Configurez unz un pipeline CI pipeline CI/CD avec/CD avec au minimum au minimum : validation : validation du code du code Python ( Python (lint),lint), compilation des compilation des transformations SQL transformations SQL, validation de, validation l'Ia de l'IaC surC sur les PR les PR, et, et dépl déploiementoiement automatique automatique sur la sur la branche branche principale principale.

### Phase.

### Phase 5 — Dashboard analytique, 5 — Dashboard analytique, gouvernance et co gouvernance et coûts (J13-J15)

-ûts (J13-J15)

- Connectez Connectez un out un outilil de BI à de BI à vos m vos marts et produisearts et produisez unz un tableau de tableau de bord répondant à bord répondant à la question la question centrale avec centrale avec au moins trois angles au moins trois angles d'analyse ( d'analyse (géographiquegéographique, sector, sectoriel, temporeliel, temporel).
-).
- Produisez également Produisez également un tableau un tableau de bord de bord de su de suivi desivi des coû coûts cloud : cots cloud : coût parût par service, évolution service, évolution dans le dans le temps temps,, alertes alertes sur les sur les dépass dépassements deements de budget budget.
- Document.
- Documentez vosez vos données données dans dans un catalogue un catalogue : : descriptions descriptions des tables des tables, propri, propriétairesétaires, tags, tags de sens de sensibilitéibilité.
- Pr.
- Préparezéparez une dé une démonmonstrationstration de cinq de cinq minutes de minutes de votre pipeline votre pipeline de bout de bout en bout en bout.. La gouvern La gouvernanceance est un est un bonus bonus.

.

---

## Modal---

## Modalités dités d'é'évaluation

### Démonstrationvaluation

### Démonstration technique ( technique (70 %)

70 %)

LL'appren'apprenant présenteant présente son pipeline son pipeline en conditions en conditions réelles réelles pendant 15 minutes pendant 15 minutes. Il. Il démarre depuis démarre depuis le le repo GitHub repo GitHub, montre l'ex, montre lécution'exécution d'un script d'un d'ing script d'ingestion,estion, déclenche un déclenche un run, run, et navigue et navig dans le dashboardue dans le dashboard final. final. Le form Le formateur peutateur peut poser poser des questions des questions sur n'import sur n'importe quellee quelle partie partie du code du code.

### Revue.

### Revue de code de code et architecture et architecture (30 (30 % %)

Le formateur)

Le formateur cons consulte leulte le repo GitHub et é repo GitHub et évalue lavalue la lisibilité du lisibilité du code code, la, la qualité des tests, qualité des la structure tests, la structure IaC IaC et la documentation. et la documentation. L'app L'apprenant dispose derenant dispose de 10 10 minutes pour expliquer minutes pour ses choix expliquer ses choix d'architecture, d' les compromarchitecture, les compromis retis retenus et laenus maî et la maîtrise des cotriseûts des coûts. Il devra. Il justifier devra justifier pourquoi certaines pourquoi certaines opérations coût opérationsent plus coûtent plus cher que d'autres cher que et comment d'autres et comment il a optimisé il a les dép optimisé lesenses.

 dépenses> Un appren.

> Unant dont apprenant dont le pipeline ne fonction le pipeline ne fonctionne pasne pas en dé en démonstrationmonstration mais dont mais dont le code le code est struct est structuréuré et document et documenté peuté peut valider valider partiellement partiellement les les comp compétences concernétences concernéesées.

---

##.

---

## Livrables Livrables

1

1. **. **Repo GitHubRepo GitHub public** public** contenant contenant l'int l'intégralégralité du projetité du projet :
   - :
   - Scripts Python d Scripts Python d'ing'ingestion (avec `.estion (avec `.env.exampleenv.example` et` et `requirements `requirements.txt.txt`)
   -`)
   - Mod Modèles de transformationèles SQL organis de transformationés en staging SQL organisés en / intermediate / staging / marts intermediate / avec tests et documentation marts avec tests
   et documentation - Modules IaC
   - Modules IaC pour le pour le stockage objet stockage objet, l'entrepôt de données, le contene, l'entrepôt de données, le conteneur serverur serverless etless et l' l'ordonnordonnanceuranceur
  
   - Work - Workflows CIflows CI/CD (/CD (validation survalidation sur PR, PR, dépl déploiementoiement sur main sur main, jobs, jobs planifi planifiésés)
   -)
   - Dockerfile Dockerfile / docker / docker-compose-compose
  
   - READ - README complet : descriptionME complet : description du projet du projet, architecture, architecture, four, fournisseurnisseur cloud choisi, instructions de cloud choisi, instructions de dépl déploioiement,ement, a auteuruteur
   -
   - Tableau Tableau de bord de bord analytique analytique accessible publ accessible publiquement (iquement (lienlien dans le dans le README) répond README) répondant àant à la question centrale la question centrale

2.

2. **Table **Tableau deau de bord de bord de suivi suivi des coû des coûtsts cloud** cloud** : co : coût parût par service, service, évolution évolution dans dans le temps, le temps, alertes alertes budget

3. budget

3. **Document **Documentation du catalogue deation du catalogue données** de données** : descriptions des tables : descriptions, sources des tables, sources, fréquences de, fréqu mise àences de mise à jour et tags jour et

4. tags

4 **Sch. **Schéma d'architectureéma d** ('architecture** (format image ouformat image draw ou draw.io).io) représentant représentant le le flux flux de données de l de données de l'ing'ingestion auestion au dashboard dashboard

5.

5. **Table **Tableauau Kan Kanban**ban** (T (Trellorello ou équ ou équivalent)ivalent) accessible publ accessible publiquementiquement,, avec les avec les user stories user stories organisées organisées par sprint par sprint et l' et l'historhistorique desique des tâches réalisées tâches (l réalisées (lien dansien dans le README le README)

---

##)

---

## Critères Critères de performance

### de performance

### Cartograph Cartographier les donnéesier les données
- Les
- Les trois sources trois sources sont documentées ( sont documentées (format,format, volume, volume, fréquence fréquence, cont, contraintesraintes d'acc d'accèsès)
- Les)
- Les champs de jointure entre champs de jointure entre sources sont sources sont identifiés et identifiés et justifi justifiésés
- Les
- Les limites de limites de qualité des qualité des données sont données sont mentionnées

### mentionnées

### Concevoir le cadre Concevoir le cadre technique technique
- Le
- Le schéma schéma d' d'architecture représentearchitecture représente l l'ensemble des'ensemble des composants composants cloud et cloud et leurs leurs interactions interactions
-
- Les choix Les choix technologiques technologiques (four (fournissenisseurur cloud, cloud, outils de outils de transformation, transformation, IaC IaC)) sont sont justifi justifiés dansés dans le READ le READMEME
-
- Le pattern Med Le pattern Medallionallion est correctement appl est correctement appliqué (iqué (raw /raw / staging / staging / marts marts)

###)

### Automat Automatiser liser l'ext'extractionraction
- Les
- Les trois sources trois sources sont sont ingérées ingérées par des par des scripts Python fonction scripts Python fonctionnelsnels
-
- L'authentification L'authentification OAuth OAuth2 France2 France Travail est g Travail est gérée avecérée avec mise en cache mise en cache du du token token
- Les
- Les scripts g scripts gèrent lesèrent les erreurs erreurs et journal et journalisent lesisent les exéc exécutionsutions
- L
- L'ing'ingestion estestion est planifi planifiée sansée sans intervention manuelle ( intervention manuelle (ordonnordonnanceur + contanceur + conteneureneur serverless)

 serverless)

### Dével### Développer des requopper des requêtesêtes SQL SQL

- Les mod-èles de transformation Les modèles de transformation produisent des résultats produisent des corrects résultats corrects et vérifiables et vérifiables
-
- Des tests sont défin Des tests sont définis suris sur les champs critiques les champs critiques (not (not_null, unique,_null, unique, accepted_values accepted_values)
- Les)
- Les requ requêtes surêtes sur l'ent l'entreprepôt de donnéesôt de données utilisent utilisent le le partitionnement et partitionnement et le clustering le clustering disponibles disponibles

### Int

### Intégrerégrer les ETL les ETL
- Le
- Le pipeline de transformation s pipeline de transformation s'exéc'exécute sans erreurute sans erreur de bout de bout en bout
- en bout
- Le pipeline Le pipeline CI/CD exéc CI/CD exécute lintute lint + compilation SQL + compilation SQL + + validation Ia validation IaC surC sur chaque PR chaque PR
-
- Le déploi Le déploiement surement sur main est automatis main est automatiséé

### Intégrer

### Intég les composrer les composants d'infants d'infrastructurerastructure
- L'inf
- L'infrastructure estrastructure est entière entièrement provisionnée parment provisionnée par IaC (auc IaC (une resaucune ressource créée mansource créuellementée manuellement)
- Les secrets)
- Les ne secrets ne sont pas sont pas exposés exposés dans le dans le code ( code (gestiongestionnaire denaire de secrets ou secrets ou variables d variables d'en'environnementvironnement)
- Le Dockerfile)
- Le Dockerfile est fonction est fonctionnel etnel et le job le job s'exécute s'exécute correctement correctement en cont en conteneur
-eneur
- Un tableau Un tableau de bord de bord de suivi des de suivi des coû coûts cloudts cloud est produit est produit et document et documentéé

### Gérer le

### Gérer le catalogue catalogue
- Les tables m
- Les tables marts sontarts sont documentées documentées (description (description, propri, propriétaireétaire, fr, fréquenceéquence)
- Le)
- Le lignage lignage des données des données est visible est visible ( (outil deoutil de documentation ou documentation ou catalogue catalogue)
- Les données sensibles sont identifiées et tagu)
- Les données sensibles sont identifiées et taguées
ées
