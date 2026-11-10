"""
Partie 4 : Ajout d'une Memory
Questions 12, 13 :
- Créer une ConversationBufferMemory
- Tester la mémoire avec 2 questions successives
"""

import os
from dotenv import load_dotenv
from llm_factory import get_llm
try:
    from langchain.memory import ConversationBufferMemory
    from langchain.chains import ConversationChain
except ImportError:
    from langchain_classic.memory import ConversationBufferMemory
    from langchain_classic.chains import ConversationChain

load_dotenv()

def run_partie4():
    print("=" * 60)
    print("Partie 4 : Test de la ConversationBufferMemory")
    print("=" * 60)

    # 12. Instanciation du LLM et de la ConversationBufferMemory
    llm = get_llm(temperature=0.2)
    
    # Conservation de l'historique complet des échanges
    memory = ConversationBufferMemory()

    # Création d'une chaîne de conversation utilisant la mémoire
    conversation = ConversationChain(
        llm=llm,
        memory=memory,
        verbose=True
    )

    # 13. Première question
    question_1 = "Bonjour, je m'appelle Alice et j'habite à Paris."
    print(f"\nUtilisateur: {question_1}")
    rep_1 = conversation.predict(input=question_1)
    print(f"Agent: {rep_1}")

    # Deuxième question qui dépend de la mémoire précédente
    question_2 = "Quel est mon prénom et où est-ce que j'habite ?"
    print(f"\nUtilisateur: {question_2}")
    rep_2 = conversation.predict(input=question_2)
    print(f"Agent: {rep_2}")

    print("\n--- Contenu brut stocké dans le buffer mémoire ---")
    print(memory.buffer)

if __name__ == "__main__":
    run_partie4()

