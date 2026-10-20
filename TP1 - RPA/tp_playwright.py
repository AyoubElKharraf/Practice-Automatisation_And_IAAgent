<<<<<<< HEAD
=======
"""Version Playwright du test local de formulaire, sans envoi d'emails."""

>>>>>>> d5212afef4491b67020530c0c1999c569d1af755
from pathlib import Path

import pandas as pd
from playwright.sync_api import Page, sync_playwright

EXCEL_PATH = Path(__file__).with_name("contacts.xlsx")
FORM_URL = Path(__file__).with_name("formulaire_test.html").resolve().as_uri()


def remplir_formulaire_playwright(
    page: Page, nom: str, email: str, message: str
) -> None:
    page.goto(FORM_URL)
    page.locator('[name="nom"]').fill(nom)
    page.locator('[name="email"]').fill(email)
    page.locator('[name="message"]').fill(message)
    page.locator("#submit").click()

    confirmation = page.locator("#confirmation")
    confirmation.wait_for(state="visible")
    if "Formulaire rempli avec succès" not in confirmation.inner_text():
        raise RuntimeError("Le formulaire n'a pas affiché la confirmation attendue.")


def main() -> None:
    df = pd.read_excel(EXCEL_PATH)
    print("[OK] Données chargées :")
    print(df.head())

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        try:
            page = browser.new_page()
            for index, row in df.iterrows():
                nom, email, message = row["Nom"], row["Email"], row["Message"]
                print(f"[{index + 1}/{len(df)}] Traitement de {nom}...")
                remplir_formulaire_playwright(page, nom, email, message)
                print("[OK] Formulaire local validé ; aucun email envoyé.")
        finally:
            browser.close()

    print("[TERMINÉ] Toutes les lignes ont été traitées.")


if __name__ == "__main__":
    main()
