<<<<<<< HEAD
=======
"""
TP RPA Python - Version selenium (alternative demandée en fin de TP)
Masters AI & DS - M2I - S3 Automation & Agentic AI - Prof. Imane Lahbari

Différence clé avec pyautogui : selenium cible les éléments du DOM directement
(par id/name/css selector), donc plus fiable que simuler des touches clavier
"à l'aveugle" — c'est la version qu'on utilise en pratique en entreprise.

Installation requise :
    pip install pandas openpyxl selenium
    + télécharger le driver correspondant à ton navigateur (ex: chromedriver)
      ou utiliser webdriver-manager : pip install webdriver-manager
"""

>>>>>>> d5212afef4491b67020530c0c1999c569d1af755
import os
import smtplib
import time
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

EXCEL_PATH = str(Path(__file__).with_name("contacts.xlsx"))
FORM_URL = Path(__file__).with_name("formulaire_test.html").resolve().as_uri()

SMTP_EMAIL = os.getenv("RPA_SMTP_EMAIL", "")
SMTP_APP_PASSWORD = os.getenv("RPA_SMTP_APP_PASSWORD", "")
EMAIL_SETTING = os.getenv("RPA_ENVOYER_EMAILS", "false").strip().lower()
if EMAIL_SETTING not in {"true", "false"}:
    raise ValueError("RPA_ENVOYER_EMAILS doit valoir 'true' ou 'false'.")
ENVOYER_EMAILS = EMAIL_SETTING == "true"


def lire_donnees_excel(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    print("[OK] Données chargées :")
    print(df.head())
    return df


def remplir_formulaire_selenium(driver, nom: str, email: str, message: str):
    """
    Adapte les sélecteurs (By.ID, By.NAME...) aux vrais attributs HTML
    du formulaire ciblé -> inspecte la page (clic droit > Inspecter).
    """
    driver.get(FORM_URL)
    time.sleep(1.5)  # laisser la page charger

    champ_nom = driver.find_element(By.NAME, "nom")
    champ_email = driver.find_element(By.NAME, "email")
    champ_message = driver.find_element(By.NAME, "message")

    champ_nom.clear()
    champ_nom.send_keys(nom)

    champ_email.clear()
    champ_email.send_keys(email)

    champ_message.clear()
    champ_message.send_keys(message)

    driver.find_element(By.ID, "submit").click()
    confirmation = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, "confirmation"))
    )
    if "Formulaire rempli avec succès" not in confirmation.text:
        raise RuntimeError("Le formulaire n'a pas affiché la confirmation attendue.")


def envoyer_email(destinataire: str, nom: str, message: str):
    if not SMTP_EMAIL or not SMTP_APP_PASSWORD:
        raise RuntimeError(
            "Configure RPA_SMTP_EMAIL et RPA_SMTP_APP_PASSWORD avant l'envoi."
        )

    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = destinataire
    msg["Subject"] = f"Confirmation pour {nom}"

    corps = f"Bonjour {nom},\n\n{message}\n\nCordialement,\nBot RPA"
    msg.attach(MIMEText(corps, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
        server.sendmail(SMTP_EMAIL, destinataire, msg.as_string())

    print(f"[OK] Email envoyé à {destinataire}")


def main():
    df = lire_donnees_excel(EXCEL_PATH)

    if ENVOYER_EMAILS:
        if not SMTP_EMAIL or not SMTP_APP_PASSWORD:
            raise RuntimeError(
                "L'envoi est activé mais RPA_SMTP_EMAIL ou "
                "RPA_SMTP_APP_PASSWORD n'est pas configuré."
            )
        example_recipients = [
            str(email).strip()
            for email in df["Email"]
            if str(email).strip().lower().endswith(("@example.com", "@example.org", "@example.net"))
        ]
        if example_recipients:
            raise ValueError(
                "Remplace les adresses d'exemple dans contacts.xlsx "
                "par des destinataires autorisés avant l'envoi : "
                + ", ".join(example_recipients)
            )

    driver = webdriver.Chrome()  # nécessite chromedriver dans le PATH

    try:
        for index, row in df.iterrows():
            nom, email, message = row["Nom"], row["Email"], row["Message"]
            print(f"[{index + 1}/{len(df)}] Traitement de {nom}...")

            remplir_formulaire_selenium(driver, nom, email, message)
            if ENVOYER_EMAILS:
                envoyer_email(email, nom, message)
            else:
                print("[INFO] Envoi d'emails désactivé pour ce test.")

            time.sleep(2)
    finally:
        driver.quit()

    print("[TERMINÉ] Toutes les lignes ont été traitées.")


if __name__ == "__main__":
    main()