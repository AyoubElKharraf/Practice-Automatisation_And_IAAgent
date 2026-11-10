"""
Partie 5 : Création de l'Agent & Partie 6 : Tests pratiques
Questions 14 à 20 :
- Créer un agent ReAct (LLM + Tools + Memory)
- Instancier AgentExecutor avec verbose=True
- Q16: "Calcule 12 + 8"
- Q17: "Rappelle-moi le calcul précédent"
- Q18: "Convertis 25°C en Fahrenheit"
- Q19: Série de 3 questions liées pour vérifier la mémoire
- Q20: Combiner plusieurs tools : "Calcule 5 + 7 puis convertis le résultat en Fahrenheit si c'était une température"
"""

import os
import re
from dotenv import load_dotenv
from llm_factory import get_llm
try:
    from langchain.tools import tool
    from langchain_classic.agents import initialize_agent, AgentType
    from langchain_classic.memory import ConversationBufferMemory
except ImportError:
    from langchain.tools import tool
    from langchain.agents import initialize_agent, AgentType
    from langchain.memory import ConversationBufferMemory

# Chargement du fichier .env
load_dotenv()

# --- Définition des Tools robustes (Partie 3) ---
@tool
def addition(expression: str) -> str:
    """Calcule la somme de nombres. L'entrée peut être deux nombres séparés par une virgule (ex: '12, 8') ou une expression (ex: '12 + 8')."""
    try:
        clean = str(expression).replace("{", "").replace("}", "").replace('"', "").replace("'", "")
        numbers = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+", clean) if x]
        if not numbers:
            return "0.0"
        result = sum(numbers)
        return str(int(result) if result.is_integer() else result)
    except Exception as e:
        return f"Erreur: {e}"

@tool
def celsius_to_fahrenheit(celsius: str) -> str:
    """Convertit une température exprimée en degrés Celsius (°C) en Fahrenheit (°F).
    L'entrée est la valeur numérique en degrés Celsius (ex: '25' ou '25°C')."""
    try:
        clean = str(celsius).replace("{", "").replace("}", "").replace('"', "").replace("'", "")
        numbers = re.findall(r"[-+]?\d*\.?\d+", clean)
        if not numbers:
            return "Erreur: valeur non trouvée"
        c = float(numbers[0])
        f = (c * 9.0 / 5.0) + 32.0
        return f"{f:.1f}°F" if not f.is_integer() else f"{int(f)}°F"
    except Exception as e:
        return f"Erreur: {e}"


def create_agent_react():
    # 1. LLM
    llm = get_llm(temperature=0.0)

    # 2. Liste des Outils (Partie 3)
    tools = [addition, celsius_to_fahrenheit]

    # 4. Mémoire (Partie 4 - 12)
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    # 14 & 15. Création de l'agent ReAct conversationnel et AgentExecutor
    agent_executor = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=6
    )

    return agent_executor


def run_partie5_and_6():
    print("=" * 70)
    print("Parties 5 et 6 : Agent ReAct avec Mémoire et Outils")
    print("=" * 70)

    executor = create_agent_react()

    # --- PARTIE 5 ---
    print("\n" + "#" * 60)
    print("PARTIE 5 - Tests initiaux")
    print("#" * 60)

    # 16. Test avec une commande simple
    q16 = "Calcule 12 + 8"
    print(f"\n>>> Question 16 : {q16}")
    res16 = executor.invoke({"input": q16})
    print(f"RÉPONSE FINALE : {res16['output']}")

    # 17. Question nécessitant la mémoire
    q17 = "Rappelle-moi le calcul précédent et son résultat."
    print(f"\n>>> Question 17 : {q17}")
    res17 = executor.invoke({"input": q17})
    print(f"RÉPONSE FINALE : {res17['output']}")

    # --- PARTIE 6 ---
    print("\n" + "#" * 60)
    print("PARTIE 6 - Tests pratiques avancés")
    print("#" * 60)

    # 18. Demandez à l'agent de convertir 25°C en Fahrenheit
    q18 = "Convertis 25°C en Fahrenheit."
    print(f"\n>>> Question 18 : {q18}")
    res18 = executor.invoke({"input": q18})
    print(f"RÉPONSE FINALE : {res18['output']}")

    # 19. Série de trois questions liées
    print("\n--- Question 19 : Série de 3 questions contextuelles liées ---")
    
    q19_1 = "J'ai un projet de recherche en robotique qui s'appelle RoboPulse."
    print(f"\n>>> Q19.1 : {q19_1}")
    res19_1 = executor.invoke({"input": q19_1})
    print(f"RÉPONSE FINALE : {res19_1['output']}")

    q19_2 = "Ce projet a débuté il y a 3 ans et a une équipe de 4 ingénieurs."
    print(f"\n>>> Q19.2 : {q19_2}")
    res19_2 = executor.invoke({"input": q19_2})
    print(f"RÉPONSE FINALE : {res19_2['output']}")

    q19_3 = "Résume-moi les informations de mon projet que je viens de te donner."
    print(f"\n>>> Q19.3 : {q19_3}")
    res19_3 = executor.invoke({"input": q19_3})
    print(f"RÉPONSE FINALE : {res19_3['output']}")

    # 20. Combinaison de plusieurs Tools dans une seule instruction
    q20 = "Calcule 5 + 7 puis convertis le résultat en Fahrenheit si c'était une température en Celsius."
    print(f"\n>>> Question 20 : {q20}")
    res20 = executor.invoke({"input": q20})
    print(f"RÉPONSE FINALE : {res20['output']}")

if __name__ == "__main__":
    run_partie5_and_6()
