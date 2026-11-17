"""
Partie 1 - Question 4 :
Script Python pour charger et afficher la valeur de la clé API via os.getenv().
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def validate_groq_key(api_key):
    """Vérifie la clé via l'API de liste des modèles, sans consommer de tokens."""
    try:
        from groq import APIConnectionError, AuthenticationError, Groq

        Groq(api_key=api_key).models.list()
        return True
    except AuthenticationError:
        return False
    except APIConnectionError as error:
        print(f"[ERREUR] Impossible de vérifier la clé Groq : {error}")
        return False


def check_api_key():
    # Chargement des variables d'environnement depuis le fichier .env
    load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    print("=" * 50)
    print("Vérification des clés API (Partie 1)")
    print("=" * 50)
    
    if groq_key:
        masked = groq_key[:8] + "..." + groq_key[-4:] if len(groq_key) > 12 else "***"
        if validate_groq_key(groq_key):
            print(f"[SUCCÈS] GROQ_API_KEY valide : {masked}")
        else:
            print("[ERREUR] GROQ_API_KEY détectée mais refusée par Groq.")
            return False
    
    if openai_key:
        masked = openai_key[:8] + "..." + openai_key[-4:] if len(openai_key) > 12 else "***"
        print(f"[INFO] OPENAI_API_KEY détectée : {masked}")

    if not groq_key and not openai_key:
        print("[ATTENTION] Ni GROQ_API_KEY ni OPENAI_API_KEY n'est configurée dans le fichier .env.")
        return False

    return True

if __name__ == "__main__":
    sys.exit(0 if check_api_key() else 1)

