"""
Partie 1 - Question 4 :
Script Python pour charger et afficher la valeur de la clé API via os.getenv().
"""

import os
from dotenv import load_dotenv

def check_api_key():
    # Chargement des variables d'environnement depuis le fichier .env
    load_dotenv()
    
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    print("=" * 50)
    print("Vérification des clés API (Partie 1)")
    print("=" * 50)
    
    if groq_key:
        masked = groq_key[:8] + "..." + groq_key[-4:] if len(groq_key) > 12 else "***"
        print(f"[SUCCÈS] GROQ_API_KEY (Gratuit) détectée : {masked}")
    
    if openai_key:
        masked = openai_key[:8] + "..." + openai_key[-4:] if len(openai_key) > 12 else "***"
        print(f"[INFO] OPENAI_API_KEY détectée : {masked}")

    if not groq_key and not openai_key:
        print("[ATTENTION] Ni GROQ_API_KEY ni OPENAI_API_KEY n'est configurée dans le fichier .env.")

if __name__ == "__main__":
    check_api_key()

