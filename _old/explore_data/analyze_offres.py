"""
Analyse des offres France Travail - Chargement en DataFrame pandas
"""

import json
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "france_travail_offres"


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """
    Aplatit un dictionnaire imbriqué en une structure plate.

    Exemple:
        {"lieuTravail": {"libelle": "Paris", "codePostal": "75001"}}
        → {"lieuTravail.libelle": "Paris", "lieuTravail.codePostal": "75001"}
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Pour les listes, on garde le JSON stringifié
            items.append((new_key, json.dumps(v, ensure_ascii=False) if v else None))
        else:
            items.append((new_key, v))
    return dict(items)


def normalize_offer(offer: dict) -> dict:
    """Normalise une offre en aplatissant tous les dictionnaires imbriqués."""
    return flatten_dict(offer)


def load_offres_to_dataframe() -> pd.DataFrame:
    """
    Charge toutes les offres France Travail (JSON et NDJSON)
    dans un seul DataFrame pandas.

    Returns:
        DataFrame combiné avec toutes les offres
    """
    all_offers = []

    for filepath in sorted(DATA_DIR.glob("offres_data_market_*")):
        logger.info("📥 Lecture de %s", filepath.name)

        if filepath.suffix == ".ndjson":
            # Format NDJSON : 1 JSON par ligne
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            offer = json.loads(line)
                            all_offers.append(normalize_offer(offer))
                        except json.JSONDecodeError as e:
                            logger.warning(
                                "⚠️  Ligne invalide dans %s : %s", filepath.name, e
                            )

        elif filepath.suffix == ".json":
            # Ancien format avec metadata
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                try:
                    data = json.loads(content)
                    # Extraire les offres selon la structure
                    if isinstance(data, dict) and "resultats" in data:
                        offers = data["resultats"]
                    elif isinstance(data, list):
                        offers = data
                    else:
                        logger.warning("⚠️  Structure inconnue dans %s", filepath.name)
                        continue

                    all_offers.extend([normalize_offer(o) for o in offers])
                    logger.info(
                        "✅ %s offres chargées depuis %s", len(offers), filepath.name
                    )

                except json.JSONDecodeError as e:
                    logger.error("❌ Erreur JSON dans %s : %s", filepath.name, e)

    logger.info(
        "📊 Total : %s offres chargées depuis %s fichiers",
        len(all_offers),
        len(list(DATA_DIR.glob("offres_data_market_*"))),
    )

    df = pd.DataFrame(all_offers)
    logger.info("📋 Shape du DataFrame : %s lignes × %s colonnes", *df.shape)

    return df


def analyze_offres(df: pd.DataFrame) -> None:
    """Affiche des statistiques de base sur les offres."""
    print("\n" + "=" * 60)
    print("📈 ANALYSE DES OFFRES FRANCE TRAVAIL")
    print("=" * 60)

    print(f"\n📊 Shape : {df.shape[0]} offres, {df.shape[1]} colonnes")

    print("\n🏢 Types de contrats :")
    if "typeContrat" in df.columns:
        print(df["typeContrat"].value_counts().to_string())

    print("\n📍 Répartition par code ROME :")
    if "romeCode" in df.columns:
        print(df["romeCode"].value_counts().to_string())

    print("\n📅 Créations par jour :")
    if "dateCreation" in df.columns:
        df["date"] = pd.to_datetime(df["dateCreation"]).dt.date
        print(df["date"].value_counts().sort_index().to_string())

    print("\n💰 Exemples de salaires :")
    if "salaire" in df.columns:
        salaires = df["salaire"].dropna().head(5)
        for s in salaires:
            libelle = s.get("libelle", "N/A") if isinstance(s, dict) else s
            print(f"  • {libelle}")

    print("\n" + "=" * 60)


def generate_column_completion_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Génère un rapport de complétion pour chaque colonne.

    Returns:
        DataFrame avec colonnes, taux de complétion et tris
    """
    total_rows = len(df)

    report = pd.DataFrame(
        {
            "column": df.columns.tolist(),
            "non_null_count": [df[col].notna().sum() for col in df.columns],
            "null_count": [df[col].isna().sum() for col in df.columns],
        }
    )

    report["completion_rate"] = (report["non_null_count"] / total_rows * 100).round(2)
    report = report.sort_values("completion_rate", ascending=False).reset_index(
        drop=True
    )

    return report


def save_completion_report(report: pd.DataFrame, output_path: Path) -> None:
    """Sauvegarde le rapport de complétion en CSV."""
    report.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("💾 Rapport sauvegardé : %s", output_path)


if __name__ == "__main__":
    df = load_offres_to_dataframe()
    analyze_offres(df)

    # Générer et sauvegarder le rapport de complétion
    report = generate_column_completion_report(df)
    output_path = DATA_DIR / "column_completion_report.csv"
    save_completion_report(report, output_path)

    print("\n📊 RAPPORT DE COMPLÉTION DES COLONNES")
    print("-" * 60)
    print(report.to_string(index=False))
    print("-" * 60)

    # Optionnel : sauvegarder en parquet pour analyse ultérieure
    # output_path = DATA_DIR / "offres_combined.parquet"
    # df.to_parquet(output_path, index=False)
    # logger.info("💾 DataFrame sauvegardé : %s", output_path)
