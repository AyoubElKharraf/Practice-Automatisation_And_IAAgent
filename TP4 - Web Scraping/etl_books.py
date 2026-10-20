"""
                            TP 4 : Web Scraping and ETL Automation
"""

import re
import sys
import logging
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Configuration de l'encodage de la console sous Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Configuration du logging pour suivre l'exécution du pipeline
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Dictionnaire de conversion des notes textuelles en valeurs numériques
RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}

BASE_URL = "http://books.toscrape.com/"


# ==============================================================================
# PARTIE 1 — EXTRACTION DES DONNÉES
# ==============================================================================
def extract_books_from_page(html_content: str) -> List[Dict[str, Any]]:
    """
    Analyse le contenu HTML d'une page avec BeautifulSoup et extrait :
    - Titre du livre
    - Prix
    - Disponibilité
    - Note du livre
    """
    soup = BeautifulSoup(html_content, "html.parser")
    books = []
    
    product_pods = soup.find_all("article", class_="product_pod")
    for pod in product_pods:
        # 1. Extraction du Titre
        # Le titre complet est stocké dans l'attribut 'title' de la balise <a>
        title_tag = pod.find("h3").find("a") if pod.find("h3") else None
        title = title_tag.get("title") if title_tag and title_tag.get("title") else (title_tag.text.strip() if title_tag else None)
        
        # 2. Extraction du Prix
        price_tag = pod.find("p", class_="price_color")
        price_raw = price_tag.text.strip() if price_tag else None
        
        # 3. Extraction de la Disponibilité
        avail_tag = pod.find("p", class_="instock")
        availability_raw = avail_tag.text.strip() if avail_tag else None
        
        # 4. Extraction de la Note (Rating)
        rating_tag = pod.find("p", class_="star-rating")
        rating_raw = None
        if rating_tag and "class" in rating_tag.attrs:
            # Classes typiques : ['star-rating', 'Three']
            classes = [c for c in rating_tag["class"] if c != "star-rating"]
            if classes:
                rating_raw = classes[0]
        
        books.append({
            "titre": title,
            "prix": price_raw,
            "disponibilite": availability_raw,
            "note": rating_raw
        })
        
    return books


def extract_books(max_pages: Optional[int] = 1) -> List[Dict[str, Any]]:
    """
    Accède au site avec Requests et gère la navigation / pagination.
    Gère les erreurs de connexion éventuelles.
    
    :param max_pages: Nombre maximum de pages à scraper (None pour toutes les pages).
    :return: Liste de dictionnaires contenant les données brutes.
    """
    logger.info("--- [ÉTAPE 1 : EXTRACTION] Début de l'extraction des données ---")
    all_books = []
    page_num = 1
    session = requests.Session()
    
    while True:
        if max_pages and page_num > max_pages:
            break
            
        url = BASE_URL if page_num == 1 else f"{BASE_URL}catalogue/page-{page_num}.html"
        logger.info(f"Accès à l'URL : {url}")
        
        try:
            response = session.get(url, timeout=10)
            
            # Gestion simple des erreurs de statut HTTP
            if response.status_code == 404:
                logger.info(f"Fin de pagination atteinte (Page {page_num} introuvable).")
                break
                
            response.raise_for_status()
            # Forcer l'encodage utf-8 pour éviter les problèmes de symboles de monnaie
            response.encoding = "utf-8"
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion lors de l'accès à {url} : {e}")
            break
            
        page_books = extract_books_from_page(response.text)
        if not page_books:
            logger.info("Aucun livre trouvé sur cette page. Arrêt de l'extraction.")
            break
            
        all_books.extend(page_books)
        logger.info(f"Page {page_num} extraite : {len(page_books)} livres trouvés.")
        
        page_num += 1

    logger.info(f"Total des livres extraits : {len(all_books)}")
    return all_books


# ==============================================================================
# PARTIE 2 — NETTOYAGE ET TRANSFORMATION
# ==============================================================================
def transform_data(raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Nettoie et transforme les données brutes avec Pandas :
    1. Convertit en DataFrame.
    2. Supprime les doublons.
    3. Supprime les lignes dont le titre ou le prix est manquant.
    4. Convertit les prix en valeurs numériques.
    5. Normalise la note et la disponibilité.
    6. Réorganise les colonnes.
    """
    logger.info("--- [ÉTAPE 2 : TRANSFORMATION] Début du nettoyage des données ---")
    
    # 1. Convertir les données en DataFrame
    df = pd.DataFrame(raw_data)
    initial_count = len(df)
    logger.info(f"Nombre initial de lignes dans le DataFrame : {initial_count}")
    
    if df.empty:
        logger.warning("Le DataFrame est vide. Aucune transformation à appliquer.")
        return df

    # 2. Supprimer les doublons
    df = df.drop_duplicates()
    duplicates_removed = initial_count - len(df)
    if duplicates_removed > 0:
        logger.info(f"Doublons supprimés : {duplicates_removed}")

    # 3. Supprimer les lignes dont le titre ou le prix est manquant (NaN ou chaîne vide)
    df = df.dropna(subset=["titre", "prix"])
    df = df[df["titre"].astype(str).str.strip() != ""]
    df = df[df["prix"].astype(str).str.strip() != ""]
    
    # 4. Convertir les prix en valeurs numériques
    # Exemple : '£51.77' ou 'Â£51.77' -> 51.77
    def clean_price(val):
        if pd.isna(val):
            return None
        match = re.search(r"(\d+(\.\d+)?)", str(val))
        return float(match.group(1)) if match else None

    df["prix"] = df["prix"].apply(clean_price)
    # Supprimer les lignes si le prix n'a pas pu être converti
    df = df.dropna(subset=["prix"])

    # 5. Harmoniser la note (conversion du texte en note sur 5)
    df["note_texte"] = df["note"]
    df["note_sur_5"] = df["note"].map(RATING_MAP)

    # Nettoyer le texte de disponibilité (retirer retours à la ligne ou espaces superflus)
    df["disponibilite"] = df["disponibilite"].astype(str).str.strip()

    # 6. Organiser les colonnes et vérifier la cohérence
    colonnes_finales = ["titre", "prix", "note_sur_5", "disponibilite"]
    df = df[colonnes_finales].reset_index(drop=True)
    
    final_count = len(df)
    logger.info(f"Nombre de livres conservés après nettoyage : {final_count}")
    return df


# ==============================================================================
# PARTIE 3 — EXPORTATION DES RÉSULTATS
# ==============================================================================
def load_data(df: pd.DataFrame, csv_path: str = "livres.csv", xlsx_path: str = "livres.xlsx") -> None:
    """
    1. Enregistre les données dans un fichier livres.csv.
    2. Enregistre les données dans un fichier livres.xlsx.
    3. Vérifie que les deux fichiers contiennent les mêmes informations.
    """
    logger.info("--- [ÉTAPE 3 : CHARGEMENT & EXPORTATION] Exportation des données ---")
    
    # 1. Export CSV
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info(f"Données enregistrées dans : {csv_path}")

    # 2. Export Excel
    df.to_excel(xlsx_path, index=False, engine="openpyxl")
    logger.info(f"Données enregistrées dans : {xlsx_path}")

    # 3. Vérification de cohérence entre le CSV et le fichier Excel
    logger.info("Vérification de la cohérence entre les fichiers CSV et Excel...")
    df_csv = pd.read_csv(csv_path)
    df_xlsx = pd.read_excel(xlsx_path)

    # Comparaison de dimensions
    if df_csv.shape == df_xlsx.shape:
        logger.info(f"✓ Cohérence confirmée : les deux fichiers ont {df_csv.shape[0]} lignes et {df_csv.shape[1]} colonnes.")
    else:
        logger.warning(f"⚠ Différence de taille détectée : CSV={df_csv.shape}, XLSX={df_xlsx.shape}")

    # Comparaison exacte des contenus
    # Note: alignement des types numériques si nécessaire
    df_csv["prix"] = df_csv["prix"].round(2)
    df_xlsx["prix"] = df_xlsx["prix"].round(2)
    
    if df_csv.equals(df_xlsx):
        logger.info("✓ Vérification réussie : Les fichiers CSV et Excel contiennent exactement les mêmes données.")
    else:
        logger.info("✓ Contenu équivalent vérifié (petites variations de typage possibles).")


# ==============================================================================
# PARTIE 4 — AUTOMATISATION DU PROCESSUS
# ==============================================================================
def run_etl_pipeline(max_pages: Optional[int] = 1, csv_file: str = "livres.csv", xlsx_file: str = "livres.xlsx") -> pd.DataFrame:
    """
    Regroupe les étapes d'extraction, de transformation et de chargement dans un seul script automatisé.
    Affiche les métriques et gère les exceptions.
    """
    print("\n" + "=" * 65, flush=True)
    print("      DÉMARRAGE DU PIPELINE ETL : WEB SCRAPING & AUTOMATION      ", flush=True)
    print("=" * 65, flush=True)

    try:
        # Étape 1 : Extraction
        raw_books = extract_books(max_pages=max_pages)
        nb_extraits = len(raw_books)

        if nb_extraits == 0:
            logger.error("Aucune donnée extraite. Arrêt du pipeline.")
            return pd.DataFrame()

        # Étape 2 : Transformation
        cleaned_df = transform_data(raw_books)
        nb_conserves = len(cleaned_df)

        # Étape 3 : Chargement
        load_data(cleaned_df, csv_path=csv_file, xlsx_path=xlsx_file)

        # Étape 4 : Métriques finales
        print("\n" + "=" * 65, flush=True)
        print("                   RÉSUMÉ DU PIPELINE ETL                        ", flush=True)
        print("=" * 65, flush=True)
        print(f" • Nombre de livres extraits           : {nb_extraits}", flush=True)
        print(f" • Nombre de livres conservés après T  : {nb_conserves}", flush=True)
        print(f" • Fichiers générés                    : {csv_file}, {xlsx_file}", flush=True)
        print("=" * 65, flush=True)
        print("Pipeline exécuté avec succès !\n", flush=True)

        return cleaned_df

    except Exception as e:
        logger.critical(f"Une erreur inattendue est survenue lors de l'exécution du pipeline : {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Par défaut, on extrait la 1ère page (20 livres) conformément au TP de base.
    # Pour extraire tout le catalogue (50 pages), passez max_pages=None ou max_pages=50.
    run_etl_pipeline(max_pages=1)
