from geo_api.extract_geo_api import export_geo_to_json
from extract_francetravail_api.extract_francetravail_api import (
    extract_francetravail_offres,
    extract_francetravail_referentiels,
)
from geo_api.load_geo_to_sqlite import main as load_geo_to_sqlite
from load_france_travail_to_sqlite import main as load_france_travail_to_sqlite
import subprocess


def main() -> None:
    """
    Point d'entrée principal de l'application.
    1. Extrait les données géographiques depuis l'API vers des JSON.
    2. Charge les JSON bruts dans une base SQLite (data/geo.sqlite).
    3. Extrait les offres France Travail et charge la table raw_ft_offres.
    4. Construit la couche intermediate/silver via dbt.
    """
    geo_json_output_dir = "./_old/data/data_geo"
    export_geo_to_json(output_dir=geo_json_output_dir)
    load_geo_to_sqlite()

    extract_francetravail_referentiels()
    extract_francetravail_offres()
    load_france_travail_to_sqlite()
    subprocess.run(
        [
            "uv",
            "run",
            "dbt",
            "build",
            "--project-dir",
            "_old/dbt",
            "--profiles-dir",
            "_old/dbt",
            "--select",
            "path:models/intermediate/silver+",
            "--indirect-selection",
            "eager",
        ],
        check=True,
    )



if __name__ == "__main__":
    main()
