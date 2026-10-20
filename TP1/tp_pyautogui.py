import time
import webbrowser
from pathlib import Path

import pandas as pd
import pyautogui

EXCEL_PATH = Path(__file__).with_name("contacts.xlsx")
FORM_URL = Path(__file__).with_name("formulaire_test.html").resolve().as_uri()
WAIT_AFTER_NAVIGATION = 2
WAIT_AFTER_SUBMIT = 1

# PyAutoGUI arrête le script si la souris est déplacée dans un coin de l'écran.
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2


def remplir_formulaire_pyautogui(nom: str, email: str, message: str) -> None:
    """Remplit le formulaire ouvert au premier plan en utilisant Tab."""
    pyautogui.hotkey("ctrl", "l")
    pyautogui.write(FORM_URL, interval=0.01)
    pyautogui.press("enter")
    time.sleep(WAIT_AFTER_NAVIGATION)

    # Depuis la page chargée, Tab atteint successivement les trois champs puis le bouton.
    pyautogui.press("tab")
    pyautogui.write(str(nom), interval=0.03)
    pyautogui.press("tab")
    pyautogui.write(str(email), interval=0.03)
    pyautogui.press("tab")
    pyautogui.write(str(message), interval=0.02)
    pyautogui.press("tab")
    pyautogui.press("enter")
    time.sleep(WAIT_AFTER_SUBMIT)


def main() -> None:
    df = pd.read_excel(EXCEL_PATH)
    required_columns = {"Nom", "Email", "Message"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(f"Colonnes Excel manquantes : {', '.join(sorted(missing_columns))}")

    print("[OK] Données chargées :")
    print(df.head())
    print("[INFO] Ouverture du formulaire local dans le navigateur...")
    webbrowser.open(FORM_URL)
    time.sleep(WAIT_AFTER_NAVIGATION)

    for index, row in df.iterrows():
        nom, email, message = row["Nom"], row["Email"], row["Message"]
        print(f"[{index + 1}/{len(df)}] Saisie de {nom} dans le formulaire local...")
        remplir_formulaire_pyautogui(nom, email, message)
        print("[INFO] Saisie et validation clavier effectuées ; aucun email envoyé.")

    print("[TERMINÉ] Vérifie dans le navigateur le message de confirmation du formulaire.")


if __name__ == "__main__":
    main()
