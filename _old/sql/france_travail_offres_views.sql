-- Vue finale des offres France Travail géo-enrichies.
-- On exploite la table raw_ft_offres déjà aplatie (colonnes du type
-- "lieuTravail__commune", "salaire__libelle", etc.) et on ajoute les libellés
-- géographiques (département, région, EPCI).

DROP VIEW IF EXISTS ft_offre_geo;
CREATE VIEW ft_offre_geo AS
SELECT
    -- Identité / métier
    trim(o.id)                            AS offre_id,
    trim(o.intitule)                      AS intitule,
    trim(o.description)                   AS description,
    trim(o.romeCode)                      AS rome_code,
    trim(o.romeLibelle)                   AS rome_libelle,
    trim(o.appellationlibelle)            AS appellation_libelle,

    -- Localisation (colonnes aplaties de lieuTravail)
    trim(o."lieuTravail__commune")        AS commune_code,
    trim(o."lieuTravail__codePostal")     AS code_postal,
    trim(o."lieuTravail__libelle")        AS lieu_libelle,

    -- Entreprise
    trim(o."entreprise__nom")             AS entreprise_nom,

    -- Contrat
    trim(o.typeContrat)                   AS type_contrat_code,
    trim(o.typeContratLibelle)            AS type_contrat_libelle,
    trim(o.natureContrat)                 AS nature_contrat,

    -- Dates
    trim(o.dateCreation)                  AS date_creation,
    trim(o.dateActualisation)             AS date_actualisation,

    -- Secteur d'activité
    trim(o.secteurActivite)               AS secteur_activite_code,
    trim(o.secteurActiviteLibelle)        AS secteur_activite_libelle,

    -- Salaire (champ aplati)
    trim(o."salaire__libelle")            AS salaire_libelle,

    -- Durée / temps de travail
    trim(o.dureeTravailLibelle)           AS duree_travail_libelle,
    trim(o.dureeTravailLibelleConverti)   AS duree_travail_libelle_converti,

    -- Infos diverses
    o.nombrePostes                        AS nombre_postes,
    o.alternance                          AS alternance,
    o.accessibleTH                        AS accessible_th,
    trim(o.qualificationCode)             AS qualification_code,
    trim(o.qualificationLibelle)          AS qualification_libelle,

    -- Origine de l'offre (champ aplati)
    trim(o."origineOffre__origine")       AS origine_offre_code,
    trim(o."origineOffre__urlOrigine")    AS origine_offre_url,

    -- Géographie enrichie
    trim(d.nom)                           AS departement_nom,
    trim(r.nom)                           AS region_nom,
    trim(e.nom)                           AS epci_nom
FROM raw_ft_offres AS o
LEFT JOIN raw_geo_communes AS c
    ON c.code = o."lieuTravail__commune"
LEFT JOIN raw_geo_departements AS d
    ON d.code = c.codeDepartement
LEFT JOIN raw_geo_regions AS r
    ON r.code = c.codeRegion
LEFT JOIN raw_geo_epcis AS e
    ON e.code = c.codeEpci
WHERE
    o."lieuTravail__commune" IS NOT NULL
    AND trim(o."lieuTravail__commune") <> '';

