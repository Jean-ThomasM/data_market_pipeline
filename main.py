from geo_api.extract_geo_api import export_geo_to_json
from extract_francetravail_api.extract_francetravail_api import extract_francetravail

def main() -> None:
    """
    Point d'entrée principal de l'application.

    """
    output_dir = "data/data_geo"
    export_geo_to_json(output_dir=output_dir)

    extract_francetravail()



if __name__ == "__main__":
    main()
