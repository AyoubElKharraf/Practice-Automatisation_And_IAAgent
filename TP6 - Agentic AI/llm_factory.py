"""
Module d'initialisation du LLM pour le TP6.
Supporte automatiquement :
1. Groq (gratuit, recommandé) si GROQ_API_KEY est défini.
2. OpenAI si OPENAI_API_KEY est défini avec du crédit disponible.
"""

import os
import sys

# Assure un affichage correct des caractères UTF-8 sous Windows PowerShell
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv

load_dotenv()

def get_llm(temperature: float = 0.2):
    groq_api_key = os.getenv("GROQ_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if groq_api_key and groq_api_key.strip():
        from langchain_groq import ChatGroq
        # Modèle actif et disponible sur votre console Groq
        return ChatGroq(
            model_name="openai/gpt-oss-120b",
            temperature=temperature,
            api_key=groq_api_key
        )
    elif openai_api_key and openai_api_key.strip():
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            api_key=openai_api_key
        )
    else:
        raise ValueError(
            "Aucune clé API trouvée. Veuillez renseigner GROQ_API_KEY (gratuit) "
            "ou OPENAI_API_KEY dans votre fichier TP6 - Agentic AI/.env"
        )

