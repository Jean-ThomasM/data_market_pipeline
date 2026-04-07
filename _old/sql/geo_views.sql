-- Communes enrichies : commune + 1er code postal + noms département / région / EPCI + population
DROP VIEW IF EXISTS geo_communes;
CREATE VIEW geo_communes AS
SELECT
    trim(c.nom)                                 AS commune_nom,
    trim(json_extract(c.codesPostaux, '$[0]'))  AS code_postal,
    trim(d.code)                                AS departement_code,
    trim(d.nom)                                 AS departement_nom,
    trim(r.nom)                                 AS region_nom,
    trim(e.nom)                                 AS epci_nom,
    CAST(NULLIF(c.population, '') AS INTEGER)   AS population
FROM raw_geo_communes AS c
LEFT JOIN raw_geo_departements AS d
    ON d.code = c.codeDepartement
LEFT JOIN raw_geo_regions AS r
    ON r.code = c.codeRegion
LEFT JOIN raw_geo_epcis AS e
    ON e.code = c.codeEpci;

