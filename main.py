from geo_api.extract_geo_api import export_geo_to_json
from geo_api.load_geo_to_sqlite import main as load_geo_to_sqlite


def main() -> None:
    """
    Point d'entrée principal de l'application.
    1. Extrait les données géographiques depuis l'API vers des JSON.
    2. Charge directement les JSON dans une base SQLite (data/geo.sqlite)
       et crée les vues de staging.
    """
    geo_json_output_dir = "data/data_geo"
    export_geo_to_json(output_dir=geo_json_output_dir)
    load_geo_to_sqlite()


if __name__ == "__main__":
    main()
