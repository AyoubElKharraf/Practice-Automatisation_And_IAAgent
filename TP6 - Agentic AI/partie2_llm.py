"""
Partie 2 : Configuration du LLM
Questions 5, 6, 7 :
- Instancier ChatOpenAI
- Comparer l'impact de la température (0.0 / 0.2 vs 1.0)
- Poser une question test ("Écris une phrase motivante pour moi")
"""

import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from llm_factory import get_llm

load_dotenv()

def run_partie2():
    print("=" * 60)
    print("Partie 2 : Configuration et test du LLM")
    print("=" * 60)

    # 5. Instanciation du LLM avec température = 0.2
    llm_low_temp = get_llm(temperature=0.2)

    # Question test (Question 7)
    prompt = "Écris une phrase motivante pour moi"
    print(f"\nPrompt test : '{prompt}'")

    print("\n--- Test avec température = 0.2 (Précis, stable) ---")
    response_low = llm_low_temp.invoke([HumanMessage(content=prompt)])
    print(f"Réponse : {response_low.content}")

    # Question 6 : Essayer de changer la température et comparer
    print("\n--- Test avec température = 1.0 (Plus créatif, varié) ---")
    llm_high_temp = get_llm(temperature=1.0)
    response_high = llm_high_temp.invoke([HumanMessage(content=prompt)])
    print(f"Réponse : {response_high.content}")

if __name__ == "__main__":
    run_partie2()

