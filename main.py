from geo_api.extract_geo_api import export_geo_to_json
from geo_api.transform_geo_json import run_geo_transformation
from scripts.load_geo_to_sqlite import main as load_geo_to_sqlite


def main() -> None:
    """
    Point d'entrée principal de l'application.
    1. Extrait les données géographiques depuis l'API vers des JSON.
    2. Transforme les JSON en CSV normalisés.
    3. Charge les CSV dans une base SQLite (data/geo.sqlite) et crée les vues de staging.
    """
    geo_json_output_dir = "data/data_geo"
    export_geo_to_json(output_dir=geo_json_output_dir)
    geo_csv_output_dir = "data/processed_geo"
    run_geo_transformation(output_dir=geo_csv_output_dir)
    load_geo_to_sqlite()


if __name__ == "__main__":
    main()
