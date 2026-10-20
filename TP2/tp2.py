"""
TP RPA - Automatisation du traitement des factures
Masters IADS - M2I - S3 Automation & Agentic AI - Prof. Imane Lahbari

Pipeline complet :
    1. Préparation (génère des factures d'exemple si le dossier est vide)
    2. Détection et extraction (parcourt le dossier, extrait N°/Fournisseur/Date/Montant)
    3. Décision (Normal <= 1000 MAD, À contrôler > 1000 MAD)
    4. Rapport Excel (rapport_factures.xlsx)
    5. Classement (Factures/Traitees/ et Factures/A_controler/)
    6. Notification email pour les factures > 1000 MAD
    7. Gestion des erreurs (fichier illisible, info manquante, montant incorrect)
    8. Journal des opérations (log.txt)

Installation requise :
    pip install pandas openpyxl

Format des factures d'exemple (fichiers .txt) :
    Numero: F001
    Fournisseur: ABC
    Date: 01/10/2026
    Montant: 500 MAD
"""

import os
import re
import shutil
import smtplib
import sys
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pandas as pd

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------
DOSSIER_FACTURES = "Factures"
DOSSIER_TRAITEES = os.path.join(DOSSIER_FACTURES, "Traitees")
DOSSIER_A_CONTROLER = os.path.join(DOSSIER_FACTURES, "A_controler")
DOSSIER_SAUVEGARDE = "Sauvegardes_Factures"
RAPPORT_EXCEL = "rapport_factures.xlsx"
LOG_FILE = "log.txt"
SEUIL_MONTANT = 1000  # MAD

SMTP_EMAIL = os.environ.get("TP2_SMTP_EMAIL", "")
SMTP_APP_PASSWORD = os.environ.get("TP2_SMTP_APP_PASSWORD", "")
RESPONSABLE_EMAIL = os.environ.get("TP2_RESPONSABLE_EMAIL", "")


# ----------------------------------------------------------------------
# JOURNAL (log.txt)
# ----------------------------------------------------------------------
def log(message: str):
    horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ligne = f"[{horodatage}] {message}"
    print(ligne)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(ligne + "\n")


# ----------------------------------------------------------------------
# ÉTAPE 1 : Préparation — génère des factures d'exemple si le dossier est vide
# ----------------------------------------------------------------------
def creer_factures_exemple():
    os.makedirs(DOSSIER_FACTURES, exist_ok=True)

    exemples = [
        ("F001", "ABC Distribution", "01/10/2026", "500 MAD"),
        ("F002", "Tech Solutions", "02/10/2026", "1500 MAD"),
        ("F003", "Papeterie Oujda", "03/10/2026", "250 MAD"),
        ("F004", "Fournisseur XYZ", "04/10/2026", "3200 MAD"),
        ("F005", "Electro Plus", "05/10/2026", "980 MAD"),
        ("F006", "Facture Incomplète", "06/10/2026", ""),         # erreur : montant manquant
        ("F007", "Import Export SARL", "07/10/2026", "abc MAD"),  # erreur : montant invalide
    ]

    for numero, fournisseur, date, montant in exemples:
        chemin = os.path.join(DOSSIER_FACTURES, f"{numero}.txt")
        if not os.path.exists(chemin):
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(f"Numero: {numero}\n")
                f.write(f"Fournisseur: {fournisseur}\n")
                f.write(f"Date: {date}\n")
                f.write(f"Montant: {montant}\n")

    log(f"[OK] Factures d'exemple créées dans {DOSSIER_FACTURES}/")


# ----------------------------------------------------------------------
# ÉTAPE 2 : Détection et extraction
# ----------------------------------------------------------------------
def extraire_facture(chemin_fichier: str) -> dict:
    """
    Lit un fichier facture (format texte .txt ou document .pdf) et retourne un dict avec les champs extraits.
    Lève une exception si le fichier est illisible, incomplet ou invalide.
    """
    chemin_lower = chemin_fichier.lower()

    if chemin_lower.endswith(".pdf"):
        try:
            import fitz
            with fitz.open(chemin_fichier) as doc:
                contenu = ""
                for page in doc:
                    contenu += page.get_text() + "\n"
        except Exception as e:
            raise ValueError(f"Fichier illisible ({e})")
    else:
        try:
            with open(chemin_fichier, "r", encoding="utf-8") as f:
                contenu = f.read()
        except Exception as e:
            raise ValueError(f"Fichier illisible ({e})")

    if not contenu.strip():
        raise ValueError("Fichier illisible")

    numero = re.search(r"Numero:\s*(.+)", contenu)
    fournisseur = re.search(r"Fournisseur:\s*(.+)", contenu)
    date = re.search(r"Date:\s*(.+)", contenu)
    montant_brut = re.search(r"Montant:\s*(.+)", contenu)

    if not (numero and fournisseur and date and montant_brut):
        raise ValueError("Information manquante (numéro/fournisseur/date/montant)")

    numero = numero.group(1).strip()
    fournisseur = fournisseur.group(1).strip()
    date = date.group(1).strip()
    montant_str = montant_brut.group(1).strip()

    if not montant_str:
        raise ValueError("Montant manquant")

    # Extrait uniquement les chiffres (ex: "1500 MAD" -> 1500)
    match_montant = re.search(r"[\d.,]+", montant_str)
    if not match_montant:
        raise ValueError(f"Montant incorrect : '{montant_str}'")

    try:
        montant = float(match_montant.group().replace(",", "."))
    except ValueError:
        raise ValueError(f"Montant incorrect : '{montant_str}'")

    res = {
        "N°": numero,
        "Fournisseur": fournisseur,
        "Date": date,
        "Montant": montant,
        "_fichier": chemin_fichier,
    }

    match_discipline = re.search(r"Discipline:\s*(.+)", contenu)
    if match_discipline:
        res["Discipline"] = match_discipline.group(1).strip()

    return res


def parcourir_dossier_factures(dossier: str) -> pd.DataFrame:
    lignes = []
    fichiers_vus = set()

    for nom_fichier in sorted(os.listdir(dossier)):
        chemin = os.path.join(dossier, nom_fichier)
        if not os.path.isfile(chemin):
            continue  # ignore les sous-dossiers (Traitees/, A_controler/)

        ext = os.path.splitext(nom_fichier)[1].lower()
        if ext not in (".txt", ".pdf"):
            continue

        base_nom = os.path.splitext(nom_fichier)[0]
        # Dédoublonnage si les formats .pdf et .txt existent pour une même facture
        if base_nom in fichiers_vus:
            continue

        try:
            facture = extraire_facture(chemin)
            lignes.append(facture)
            fichiers_vus.add(base_nom)
            log(f"[OK] Extraction réussie : {nom_fichier}")
        except ValueError as e:
            log(f"[ERREUR] {nom_fichier} : {e}")

    df = pd.DataFrame(lignes)
    return df


# ----------------------------------------------------------------------
# ÉTAPE 3 : Prise de décision
# ----------------------------------------------------------------------
def appliquer_decision(df: pd.DataFrame) -> pd.DataFrame:
    df["Statut"] = df["Montant"].apply(
        lambda m: "Normal" if m <= SEUIL_MONTANT else "À contrôler"
    )
    return df


# ----------------------------------------------------------------------
# ÉTAPE 4 : Rapport Excel
# ----------------------------------------------------------------------
def generer_rapport_excel(df: pd.DataFrame):
    colonnes = ["N°", "Fournisseur"]
    if "Discipline" in df.columns and df["Discipline"].notna().any():
        colonnes.append("Discipline")
    colonnes.extend(["Date", "Montant", "Statut"])

    colonnes_existantes = [c for c in colonnes if c in df.columns]
    df_export = df[colonnes_existantes]
    df_export.to_excel(RAPPORT_EXCEL, index=False)
    log(f"[OK] Rapport généré : {RAPPORT_EXCEL}")


# ----------------------------------------------------------------------
# ÉTAPE 5 : Classement des fichiers
# ----------------------------------------------------------------------
def classer_factures(df: pd.DataFrame):
    os.makedirs(DOSSIER_TRAITEES, exist_ok=True)
    os.makedirs(DOSSIER_A_CONTROLER, exist_ok=True)

    for _, row in df.iterrows():
        source = row["_fichier"]
        destination_dossier = (
            DOSSIER_TRAITEES if row["Statut"] == "Normal" else DOSSIER_A_CONTROLER
        )
        destination = os.path.join(destination_dossier, os.path.basename(source))

        try:
            shutil.move(source, destination)

            # Si un fichier jumeau (.pdf / .txt) est présent, le déplacer aussi
            racine_nom, ext = os.path.splitext(source)
            autre_ext = ".pdf" if ext.lower() == ".txt" else ".txt"
            fichier_jumeau = racine_nom + autre_ext
            if os.path.exists(fichier_jumeau):
                shutil.move(
                    fichier_jumeau,
                    os.path.join(destination_dossier, os.path.basename(fichier_jumeau)),
                )

            log(f"[OK] Classée ({row['Statut']}) : {row['N°']}")
        except Exception as e:
            log(f"[ERREUR] Classement impossible pour {row['N°']} : {e}")


# ----------------------------------------------------------------------
# ÉTAPE 6 : Notification email pour les factures à contrôler
# ----------------------------------------------------------------------
def envoyer_notification(numero: str, fournisseur: str, montant: float):
    if not SMTP_EMAIL or not SMTP_APP_PASSWORD or not RESPONSABLE_EMAIL:
        log(
            f"[AVERTISSEMENT] Notification ignorée pour {numero} : "
            "configuration email absente."
        )
        return

    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = RESPONSABLE_EMAIL
    msg["Subject"] = f"Facture à contrôler : {numero}"

    corps = (
        f"Une facture dépasse le seuil de {SEUIL_MONTANT} MAD et nécessite un contrôle.\n\n"
        f"Numéro : {numero}\n"
        f"Fournisseur : {fournisseur}\n"
        f"Montant : {montant} MAD\n"
    )
    msg.attach(MIMEText(corps, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
            server.sendmail(SMTP_EMAIL, RESPONSABLE_EMAIL, msg.as_string())
        log(f"[OK] Notification envoyée pour {numero}")
    except Exception as e:
        log(f"[ERREUR] Envoi notification échoué pour {numero} : {e}")


def notifier_factures_a_controler(df: pd.DataFrame):
    a_controler = df[df["Statut"] == "À contrôler"]
    for _, row in a_controler.iterrows():
        envoyer_notification(row["N°"], row["Fournisseur"], row["Montant"])


# ----------------------------------------------------------------------
# ORCHESTRATION
# ----------------------------------------------------------------------
def main(action: str = None):
    # Support des arguments de ligne de commande : --generer ou --restaurer
    if action is None and len(sys.argv) > 1:
        if "--generer" in sys.argv or "-g" in sys.argv:
            action = "generer"
        elif "--restaurer" in sys.argv or "-r" in sys.argv:
            action = "restaurer"

    if action == "generer":
        try:
            from generateur_factures import generer_factures
            log("[ACTION] Génération automatique de factures multidiscipline avec sauvegarde isolée...")
            factures, backup = generer_factures(
                nb_factures=16,
                dossier_destination=DOSSIER_FACTURES,
                dossier_sauvegarde=DOSSIER_SAUVEGARDE,
            )
            log(f"[OK] {len(factures)} factures générées dans {DOSSIER_FACTURES}/ et sauvegardées dans {backup}")
        except Exception as e:
            log(f"[ERREUR] Échec de la génération automatique : {e}")

    elif action == "restaurer":
        try:
            from generateur_factures import restaurer_sauvegarde
            log("[ACTION] Restauration des factures depuis la sauvegarde isolée...")
            nb = restaurer_sauvegarde(DOSSIER_SAUVEGARDE, DOSSIER_FACTURES)
            log(f"[OK] {nb} facture(s) restaurée(s) dans {DOSSIER_FACTURES}/")
        except Exception as e:
            log(f"[ERREUR] Échec de la restauration : {e}")

    log("===== Démarrage du robot RPA factures =====")

    if not os.path.exists(DOSSIER_FACTURES) or not os.listdir(DOSSIER_FACTURES):
        creer_factures_exemple()

    df = parcourir_dossier_factures(DOSSIER_FACTURES)

    if df.empty:
        log("[ARRÊT] Aucune facture valide extraite.")
        return

    df = appliquer_decision(df)
    generer_rapport_excel(df)
    classer_factures(df)
    notifier_factures_a_controler(df)

    log(f"===== Traitement terminé : {len(df)} facture(s) traitée(s) =====")


if __name__ == "__main__":
    main()