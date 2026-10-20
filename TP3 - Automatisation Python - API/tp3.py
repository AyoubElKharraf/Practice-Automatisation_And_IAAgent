"""
TP3 — Automatisation du suivi des données météorologiques
=========================================================
Utilise l'API Open-Meteo (https://open-meteo.com/) pour récupérer les
prévisions météo d'une ville, traiter les données et générer un fichier Excel.

Parties couvertes :
    Partie 1 : Récupération des données par API
    Partie 2 : Traitement automatique avec Python
    Partie 3 : Génération automatique d'un fichier Excel
    Partie 4 : Gestion des erreurs
    Partie 5 : Vérification et bilan
"""

import sys
import requests
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────
# LISTE DES VILLES DISPONIBLES
# ─────────────────────────────────────────────
VILLES = {
    # Maroc
    "1":  {"nom": "Oujda",        "lat": 34.68,  "lon": -1.91},
    "2":  {"nom": "Casablanca",   "lat": 33.59,  "lon": -7.62},
    "3":  {"nom": "Rabat",        "lat": 34.01,  "lon": -6.83},
    "4":  {"nom": "Marrakech",    "lat": 31.63,  "lon": -8.00},
    "5":  {"nom": "Fès",          "lat": 34.04,  "lon": -5.00},
    "6":  {"nom": "Tanger",       "lat": 35.77,  "lon": -5.80},
    "7":  {"nom": "Agadir",       "lat": 30.43,  "lon": -9.60},
    # International
    "8":  {"nom": "Paris",        "lat": 48.85,  "lon":  2.35},
    "9":  {"nom": "Londres",      "lat": 51.51,  "lon": -0.13},
    "10": {"nom": "Dubai",        "lat": 25.20,  "lon": 55.27},
    "11": {"nom": "New York",     "lat": 40.71,  "lon": -74.01},
    "12": {"nom": "Tokyo",        "lat": 35.68,  "lon": 139.69},
}

TIMEOUT_SECONDES = 10


# ─────────────────────────────────────────────
# SÉLECTION INTERACTIVE DE LA VILLE
# ─────────────────────────────────────────────
def choisir_ville() -> tuple[str, float, float, str]:
    """
    Affiche un menu et demande à l'utilisateur de choisir une ville.
    Retourne (nom, latitude, longitude, nom_fichier).
    """
    print("\n" + "=" * 58)
    print("  TP3 — Suivi météo automatisé")
    print("=" * 58)
    print("\n  Villes disponibles :\n")

    # Affichage du menu en deux colonnes
    items = list(VILLES.items())
    moitie = (len(items) + 1) // 2
    for i in range(moitie):
        gauche = f"  [{items[i][0]:>2}] {items[i][1]['nom']:<15}"
        if i + moitie < len(items):
            droite = f"  [{items[i + moitie][0]:>2}] {items[i + moitie][1]['nom']}"
        else:
            droite = ""
        print(gauche + droite)

    print(f"\n  [ 0] Entrer une ville personnalisée")
    print("-" * 58)

    while True:
        choix = input("  Votre choix : ").strip()

        if choix == "0":
            # Ville personnalisée
            nom = input("  Nom de la ville : ").strip()
            try:
                lat = float(input("  Latitude  (ex: 34.68) : ").strip())
                lon = float(input("  Longitude (ex: -1.91) : ").strip())
            except ValueError:
                print("  Coordonnées invalides, veuillez réessayer.\n")
                continue
            fichier = f"meteo_{nom.lower().replace(' ', '_')}.xlsx"
            return nom, lat, lon, fichier

        elif choix in VILLES:
            ville = VILLES[choix]
            nom = ville["nom"]
            fichier = f"meteo_{nom.lower().replace(' ', '_')}.xlsx"
            return nom, ville["lat"], ville["lon"], fichier

        else:
            print(f"  Choix invalide. Entrez un nombre entre 0 et {max(VILLES.keys())}.\n")


# ─────────────────────────────────────────────
# PARTIE 1 — Récupération des données par API
# ─────────────────────────────────────────────
def recuperer_donnees_meteo(latitude: float, longitude: float, ville: str = "?") -> dict:
    """
    Interroge l'API Open-Meteo et retourne le JSON brut.

    Paramètres
    ----------
    latitude  : float – latitude de la ville
    longitude : float – longitude de la ville
    ville     : str   – nom de la ville (pour affichage)

    Retourne
    --------
    dict – données JSON de l'API

    Lève
    ----
    requests.exceptions.ConnectionError  si pas de connexion Internet
    requests.exceptions.Timeout          si le serveur ne répond pas à temps
    requests.exceptions.HTTPError        si le code HTTP est une erreur (4xx/5xx)
    ValueError                           si la structure JSON est inattendue
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        "&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean"
        "&timezone=auto"
        "&forecast_days=14"          # 14 jours de prévision
    )

    print(f"[1/5] Connexion a l'API Open-Meteo pour {ville}...")
    print(f"      URL : {url}\n")

    response = requests.get(url, timeout=TIMEOUT_SECONDES)

    # Lève une HTTPError si le code de statut est >= 400
    response.raise_for_status()

    data = response.json()

    # Vérification de la structure attendue
    if "daily" not in data:
        raise ValueError("Clé 'daily' absente dans la réponse de l'API.")
    for cle in ("time", "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean"):
        if cle not in data["daily"]:
            raise ValueError(f"Clé '{cle}' manquante dans data['daily'].")

    print("✔  Données reçues avec succès.")
    return data


# ─────────────────────────────────────────────
# PARTIE 2 — Traitement automatique avec Python
# ─────────────────────────────────────────────
def traiter_donnees(data: dict) -> pd.DataFrame:
    """
    Organise les données brutes dans un DataFrame, calcule les statistiques
    et détecte les valeurs manquantes.

    Retourne
    --------
    pd.DataFrame avec colonnes : Date, T_max, T_min, T_moy
    """
    print("\n[2/5] Traitement des données…")

    daily = data["daily"]

    df = pd.DataFrame({
        "Date":          daily["time"],
        "T_max (°C)":    daily["temperature_2m_max"],
        "T_min (°C)":    daily["temperature_2m_min"],
        "T_moy (°C)":    daily["temperature_2m_mean"],
    })

    # Conversion de la colonne Date en type datetime
    df["Date"] = pd.to_datetime(df["Date"])

    # ── Valeurs manquantes ───────────────────
    nb_manquants = df.isnull().sum()
    total_manquants = nb_manquants.sum()

    if total_manquants > 0:
        print(f"⚠  Valeurs manquantes détectées :\n{nb_manquants[nb_manquants > 0]}")
        # Interpolation linéaire pour combler les trous
        df[["T_max (°C)", "T_min (°C)", "T_moy (°C)"]] = (
            df[["T_max (°C)", "T_min (°C)", "T_moy (°C)"]].interpolate(method="linear")
        )
        print("   → Valeurs interpolées (méthode linéaire).")
    else:
        print("✔  Aucune valeur manquante.")

    # ── Statistiques ─────────────────────────
    moy = df["T_moy (°C)"].mean()
    t_min = df["T_min (°C)"].min()
    t_max = df["T_max (°C)"].max()

    print("\n─── Aperçu des données ────────────────────────────────")
    print(df.to_string(index=False))
    print("\n─── Résumé statistique ────────────────────────────────")
    print(f"  Température moyenne  : {moy:.2f} °C")
    print(f"  Température minimale : {t_min:.2f} °C")
    print(f"  Température maximale : {t_max:.2f} °C")
    print("────────────────────────────────────────────────────────")

    return df


# ─────────────────────────────────────────────
# PARTIE 3 — Génération automatique d'un fichier
# ─────────────────────────────────────────────
def exporter_excel(df: pd.DataFrame, chemin: str, ville: str = "?") -> None:
    """
    Exporte les données dans un fichier Excel comportant deux feuilles :
      • "Données météo" – tableau journalier complet
      • "Résumé"        – statistiques clés + horodatage
    """
    print(f"\n[3/5] Export vers {chemin}...")

    moy   = df["T_moy (°C)"].mean()
    t_min = df["T_min (°C)"].min()
    t_max = df["T_max (°C)"].max()
    date_min = df.loc[df["T_min (°C)"].idxmin(), "Date"].strftime("%Y-%m-%d")
    date_max = df.loc[df["T_max (°C)"].idxmax(), "Date"].strftime("%Y-%m-%d")

    resume = pd.DataFrame({
        "Indicateur": [
            "Ville",
            "Période (début)",
            "Période (fin)",
            "Température moyenne",
            "Température minimale",
            "Date du minimum",
            "Température maximale",
            "Date du maximum",
            "Généré le",
        ],
        "Valeur": [
            ville,
            df["Date"].min().strftime("%Y-%m-%d"),
            df["Date"].max().strftime("%Y-%m-%d"),
            f"{moy:.2f} °C",
            f"{t_min:.2f} °C",
            date_min,
            f"{t_max:.2f} °C",
            date_max,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ],
    })

    with pd.ExcelWriter(chemin, engine="openpyxl") as writer:
        # Feuille 1 : données brutes
        df_export = df.copy()
        df_export["Date"] = df_export["Date"].dt.strftime("%Y-%m-%d")
        df_export.to_excel(writer, sheet_name="Données météo", index=False)

        # Feuille 2 : résumé
        resume.to_excel(writer, sheet_name="Résumé", index=False)

    print(f"Fichier Excel genere : {chemin}")


# ─────────────────────────────────────────────
# PARTIE 3 (bis) — Vérification du fichier généré
# ─────────────────────────────────────────────
def verifier_fichier(chemin: str) -> None:
    """Relit le fichier Excel et affiche un aperçu pour confirmer son contenu."""
    print(f"\n[4/5] Vérification du fichier {chemin}…")

    df_lu = pd.read_excel(chemin, sheet_name="Données météo")
    resume_lu = pd.read_excel(chemin, sheet_name="Résumé")

    print(f"  Feuille 'Données météo' : {len(df_lu)} lignes × {len(df_lu.columns)} colonnes")
    print(df_lu.head(3).to_string(index=False))

    print(f"\n  Feuille 'Résumé' :")
    print(resume_lu.to_string(index=False))
    print("✔  Fichier vérifié avec succès.")


# ─────────────────────────────────────────────
# PARTIE 5 — Bilan
# ─────────────────────────────────────────────
def afficher_bilan(ville: str = "?", fichier: str = "meteo.xlsx") -> None:
    print("\n" + "=" * 58)
    print("  BILAN - TP3 : Automatisation meteo avec Python & API")
    print("=" * 58)
    print(f"""
  Role de l'API Open-Meteo :
    - Fournir des donnees meteorologiques gratuitement et en
      temps reel via une URL structuree (REST/JSON).
    - Renvoyer les previsions journalieres (T_max, T_min, T_moy)
      pour n'importe quelle coordonnee geographique.

  Role du script Python :
    - Interroger l'API et recuperer la reponse JSON.
    - Nettoyer, organiser et analyser les donnees (pandas).
    - Calculer les indicateurs statistiques cles.
    - Detecter et corriger les valeurs manquantes.
    - Exporter automatiquement un fichier Excel structure.
    - Gerer les erreurs reseau, HTTP et de donnees.

  Ville traitee  : {ville}
  Fichier produit: {fichier}
    Feuille 1 - "Donnees meteo" : tableau journalier complet
    Feuille 2 - "Resume"        : statistiques + horodatage
""")
    print("=" * 58)


# ─────────────────────────────────────────────
# PARTIE 4 — Tests de gestion des erreurs
# ─────────────────────────────────────────────
def tester_gestion_erreurs() -> None:
    """
    Vérifie les 3 scénarios d'erreur prévus dans la Partie 4 :
      1. Absence de connexion / hôte inaccessible  -> ConnectionError
      2. Réponse incorrecte de l'API (code 400)    -> HTTPError
      3. Données manquantes dans le JSON           -> KeyError
    """
    sep = "=" * 60
    print("\n" + sep)
    print("  VERIFICATION DE LA GESTION DES ERREURS (PARTIE 4)")
    print(sep)

    succes_total = 0

    # ── TEST 1 : Hôte inaccessible ─────────────────────────────
    print("\n--- TEST 1 : Absence de connexion Internet / Hote inaccessible ---")
    url_invalide = "https://domaine-inexistant-xyz123456.open-meteo.com/v1/forecast"
    print(f"Tentative de connexion vers '{url_invalide}'...")
    try:
        requests.get(url_invalide, timeout=5)
        print("  [ECHEC DU TEST] Aucune erreur levee - comportement inattendu.")
    except requests.exceptions.ConnectionError as e:
        print("  [SUCCES DU TEST] L'erreur de connexion a ete interceptee avec succes !")
        print(f"  Detail capture : ConnectionError -> {type(e).__name__}")
        succes_total += 1
    except Exception as e:
        print(f"  [ECHEC DU TEST] Exception inattendue : {type(e).__name__} -> {e}")

    # ── TEST 2 : Réponse HTTP 400 ──────────────────────────────
    print("\n--- TEST 2 : Reponse incorrecte de l'API (Ex: Erreur 400 Parametre invalide) ---")
    url_bad = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=999.0&longitude=0.0"
        "&daily=temperature_2m_max&timezone=auto"
    )
    print("Envoi d'une requete avec coordonnees aberrantes (latitude=999.0)...")
    reponse_bad = None
    try:
        reponse_bad = requests.get(url_bad, timeout=10)
        print(f"  Statut HTTP recu : {reponse_bad.status_code}")
        reponse_bad.raise_for_status()
        print("  [ECHEC DU TEST] Aucune erreur HTTP levee - comportement inattendu.")
    except requests.exceptions.HTTPError as e:
        code = reponse_bad.status_code if reponse_bad is not None else "?"
        print("  [SUCCES DU TEST] L'erreur HTTP de l'API a ete interceptee avec succes !")
        print(f"  Detail capture : HTTPError ({code}) -> {e}")
        succes_total += 1
    except requests.exceptions.ConnectionError as e:
        print(f"  [ECHEC DU TEST] ConnectionError inattendue : {e}")
    except Exception as e:
        print(f"  [ECHEC DU TEST] Exception inattendue : {type(e).__name__} -> {e}")

    # ── TEST 3 : JSON incomplet (clé manquante) ────────────────
    print("\n--- TEST 3 : Donnees manquantes ou incompletes dans le JSON ---")
    print("Validation d'une charge utile incomplete...")
    json_incomplet = {
        "daily": {
            # Cle 'time' volontairement absente
            "temperature_2m_max": [30.0, 31.5, 29.8]
        }
    }
    try:
        cle = "time"
        if cle not in json_incomplet["daily"]:
            raise KeyError(f"Cle obligatoire '{cle}' manquante dans les donnees journalieres.")
        print("  [ECHEC DU TEST] Aucune erreur levee - comportement inattendu.")
    except KeyError as e:
        print("  [SUCCES DU TEST] L'absence de donnees a ete detectee avec succes !")
        print(f"  Detail capture : KeyError -> {e}")
        succes_total += 1
    except Exception as e:
        print(f"  [ECHEC DU TEST] Exception inattendue : {type(e).__name__} -> {e}")

    # ── Résultat global ────────────────────────────────────────
    print("\n" + sep)
    if succes_total == 3:
        print(f"  Tous les scenarios d'erreurs ont ete geres correctement.")
    else:
        print(f"  Attention : seulement {succes_total}/3 tests ont reussi.")
    print(sep + "\n")


# ─────────────────────────────────────────────
# PARTIE 4 — Gestion des erreurs (point d'entrée)
# ─────────────────────────────────────────────
def main() -> None:

    # ── Sélection de la ville ──────────────────
    ville, latitude, longitude, fichier_sortie = choisir_ville()

    print("\n" + "=" * 58)
    print(f"  Ville selectionnee : {ville}")
    print("=" * 58 + "\n")

    try:
        # ── Partie 1 ──────────────────────────
        data = recuperer_donnees_meteo(latitude, longitude, ville)

        # ── Partie 2 ──────────────────────────
        df = traiter_donnees(data)

        # ── Partie 3 ──────────────────────────
        exporter_excel(df, fichier_sortie, ville)

        # ── Vérification ──────────────────────
        verifier_fichier(fichier_sortie)

        # ── Partie 5 – Bilan ──────────────────
        print("\n[5/5] Bilan du script")
        afficher_bilan(ville, fichier_sortie)

        # ── Partie 4 — Tests d'erreurs ─────────
        tester_gestion_erreurs()

    # ── Partie 4 — Gestion des erreurs ────────
    except requests.exceptions.ConnectionError:
        print("\nERREUR : Aucune connexion Internet detectee.")
        print("    Verifiez votre reseau et relancez le script.")
        sys.exit(1)

    except requests.exceptions.Timeout:
        print(f"\nERREUR : Le serveur n'a pas repondu en {TIMEOUT_SECONDES} s.")
        print("    Reessayez dans quelques instants.")
        sys.exit(1)

    except requests.exceptions.HTTPError as e:
        print(f"\nERREUR HTTP : Reponse incorrecte de l'API ({e}).")
        print("    Verifiez les parametres de la requete.")
        sys.exit(1)

    except ValueError as e:
        print(f"\nERREUR de donnees : {e}")
        print("    Les donnees recues sont incompletes ou malformees.")
        sys.exit(1)

    except Exception as e:
        print(f"\nERREUR inattendue : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()