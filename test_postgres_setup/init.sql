-- France Travail Offres Schema
-- Table principale pour stocker les offres d'emploi

CREATE TABLE IF NOT EXISTS offres (
    id VARCHAR(20) PRIMARY KEY,
    intitule VARCHAR(500) NOT NULL,
    description TEXT,
    date_creation TIMESTAMP WITH TIME ZONE,
    date_actualisation TIMESTAMP WITH TIME ZONE,
    
    -- Lieu de travail
    lieu_travail_libelle VARCHAR(200),
    lieu_travail_latitude DECIMAL(10, 7),
    lieu_travail_longitude DECIMAL(10, 7),
    lieu_travail_code_postal VARCHAR(10),
    lieu_travail_commune VARCHAR(20),
    
    -- Code et libellé ROME
    rome_code VARCHAR(10),
    rome_libelle VARCHAR(200),
    appellation_libelle VARCHAR(200),
    
    -- Entreprise
    entreprise_adaptee BOOLEAN DEFAULT FALSE,
    
    -- Contrat
    type_contrat VARCHAR(50),
    type_contrat_libelle VARCHAR(100),
    nature_contrat VARCHAR(100),
    experience_exige VARCHAR(10),
    experience_libelle VARCHAR(100),
    
    -- Metadata
    raw_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour les recherches courantes
CREATE INDEX IF NOT EXISTS idx_offres_rome_code ON offres(rome_code);
CREATE INDEX IF NOT EXISTS idx_offres_type_contrat ON offres(type_contrat);
CREATE INDEX IF NOT EXISTS idx_offres_date_creation ON offres(date_creation);
CREATE INDEX IF NOT EXISTS idx_offres_lieu_code_postal ON offres(lieu_travail_code_postal);
CREATE INDEX IF NOT EXISTS idx_offres_raw_json ON offres USING GIN(raw_json);

-- Table pour les compétences associées aux offres
CREATE TABLE IF NOT EXISTS offres_competences (
    id SERIAL PRIMARY KEY,
    offre_id VARCHAR(20) REFERENCES offres(id) ON DELETE CASCADE,
    competence_code VARCHAR(20),
    competence_libelle VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_offres_competences_offre_id ON offres_competences(offre_id);

-- Table pour les permis requis
CREATE TABLE IF NOT EXISTS offres_permis (
    id SERIAL PRIMARY KEY,
    offre_id VARCHAR(20) REFERENCES offres(id) ON DELETE CASCADE,
    permis_libelle VARCHAR(200),
    permis_exigence VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_offres_permis_offre_id ON offres_permis(offre_id);
