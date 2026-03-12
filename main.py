from geo_api.extract_geo_api import export_geo_to_json
from geo_api.transform_geo_json import run_geo_transformation


def main() -> None:
    """
    Point d'entrée principal de l'application.

    
    """
    geo_json_output_dir = "data/data_geo"
    export_geo_to_json(output_dir=geo_json_output_dir)
    geo_csv_output_dir = "data/processed_geo"
    run_geo_transformation(output_dir=geo_csv_output_dir)


if __name__ == "__main__":
    main()
