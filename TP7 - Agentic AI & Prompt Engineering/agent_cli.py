"""Interface interactive de l'Assistant pédagogique — Master IA."""

from __future__ import annotations

from pathlib import Path
import argparse

from agent_local import LocalAgent
from env_loader import load_dotenv
from gemini_agent import GeminiAgent
from groq_agent import GroqAgent
from openai_agent import OpenAIAgent
from openrouter_agent import OpenRouterAgent


RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
DIM = "\033[2m"


def _print_banner() -> None:
    print(f"\n{CYAN}{'=' * 64}{RESET}")
    print(f"{CYAN}        ASSISTANT PEDAGOGIQUE - MASTER IA{RESET}")
    print(f"{CYAN}{'=' * 64}{RESET}")
    print(f"{DIM}Tapez une question. Commandes : exit, help, json, clear.{RESET}\n")


def _print_help() -> None:
    print("Commandes disponibles :")
    print("  exit   Quitter l'agent et revenir au terminal")
    print("  help   Afficher cette aide")
    print("  json   Activer ou désactiver la réponse JSON")
    print("  clear  Effacer l'écran")


def _clear_screen() -> None:
    print("\033[2J\033[H", end="")
    _print_banner()


def run() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Assistant pédagogique — Master IA")
    backend = parser.add_mutually_exclusive_group()
    backend.add_argument(
        "--local",
        action="store_true",
        help="Utiliser explicitement le moteur local sans API",
    )
    backend.add_argument(
        "--groq",
        action="store_true",
        help="Utiliser Groq au lieu du moteur local",
    )
    backend.add_argument(
        "--gemini",
        action="store_true",
        help="Utiliser Gemini au lieu du moteur local",
    )
    backend.add_argument(
        "--openai",
        action="store_true",
        help="Utiliser OpenAI au lieu du moteur local",
    )
    backend.add_argument(
        "--openrouter",
        action="store_true",
        help="Utiliser OpenRouter au lieu du moteur local",
    )
    args = parser.parse_args()
    knowledge_base = Path(__file__).parent / "knowledge_base"
    try:
        if args.groq:
            agent = GroqAgent(knowledge_base)
        elif args.gemini:
            agent = GeminiAgent(knowledge_base)
        elif args.openai:
            agent = OpenAIAgent(knowledge_base)
        elif args.openrouter:
            agent = OpenRouterAgent(knowledge_base)
        else:
            agent = LocalAgent(knowledge_base)
    except RuntimeError as error:
        print(f"Erreur de configuration : {error}")
        return
    json_mode = False
    _print_banner()
    while True:
        try:
            request = input(f"{GREEN}agent >>> {RESET}")
        except (EOFError, KeyboardInterrupt):
            print("\nSortie de l'agent.")
            return
        request = request.strip()
        if not request:
            continue
        command = request.lower()
        if command in {"exit", "quit"}:
            print(f"{YELLOW}Retour au terminal.{RESET}")
            return
        if command == "help":
            _print_help()
            continue
        if command == "json":
            json_mode = not json_mode
            state = "activé" if json_mode else "désactivé"
            print(f"{YELLOW}Mode JSON {state}.{RESET}")
            continue
        if command == "clear":
            _clear_screen()
            continue
        try:
            result = agent.respond(request, json_output=json_mode)
        except RuntimeError as error:
            print(f"\n{YELLOW}Erreur de l'agent : {error}{RESET}")
            print(f"{DIM}L'agent reste actif. Corrigez la configuration ou tapez exit.{RESET}\n")
            continue
        if json_mode:
            print(result)
        else:
            print(f"\n{CYAN}Assistant pédagogique :{RESET}")
            print(result["reponse"])
            if result.get("explication"):
                print(f"\nExplication / étapes : {result['explication']}")
            print(f"\n{DIM}Catégorie : {result['categorie']}")
            print(f"Source : {result['source'] or 'Aucune source disponible'}")
            print(f"Suite : {result['information_manquante']}{RESET}\n")


if __name__ == "__main__":
    run()
