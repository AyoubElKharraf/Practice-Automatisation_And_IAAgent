# TP 6 : Création d’un premier Agent IA
**Master M2I (S3) – AI&DB Automation & Agentic AI**  
*Prof. Imane Lahbari*

---

## 🎯 Objectif du TP
Apprendre à configurer un LLM, créer des Tools réutilisables, ajouter une mémoire conversationnelle (`ConversationBufferMemory`), et assembler le tout au sein d'un agent cognitif **ReAct** (`Reasoning + Acting`) capable de planifier, d'exécuter des actions outillées et de conserver le contexte.

---

## 📁 Architecture des fichiers

```text
TP6 - Agentic AI/
├── venv/                      # Environnement virtuel Python dédié
├── .env                       # Clés API (GROQ_API_KEY gratuit ou OPENAI_API_KEY)
├── .env.example               # Modèle d'environnement
├── requirements.txt           # Dépendances du TP
├── llm_factory.py             # Instanciation transparente du LLM (Groq / OpenAI)
├── partie1_env.py             # Script de vérification du .env (Question 4)
├── partie2_llm.py             # Test du LLM et variation de température (Questions 5, 6, 7)
├── partie3_tools.py           # Définition et tests unitaires des Tools (Questions 8, 9, 10, 11)
├── partie4_memory.py          # Test de la ConversationBufferMemory (Questions 12, 13)
├── partie5_6_agent.py         # Agent ReAct complet + Tests pratiques (Questions 14 à 20)
└── README.md                  # Compte-rendu d'exécution détaillé
```

---

## 🚀 Guide d'installation et d'exécution

### 1. Activer l'environnement virtuel

Sous Windows PowerShell :
```powershell
cd "TP6 - Agentic AI"
.\venv\Scripts\activate
```

### 2. Configurer la clé API dans `.env`
Ouvrez le fichier `.env` :
```env
# Clé API Groq (100% GRATUITE - https://console.groq.com/keys)
GROQ_API_KEY="gsk_..."

# Clé OpenAI (Optionnelle)
OPENAI_API_KEY="sk-..."
```

---

## 📊 Résultats d'exécution par partie

### Partie 1 : Préparation de l'environnement (Questions 1 à 4)
- **Environnement virtuel :** Créé avec succès sous `venv` avec Python 3.14.
- **Bibliothèques installées :** `langchain`, `langchain-groq`, `langchain-openai`, `langchain-community`, `openai`, `python-dotenv`.
- **Script de test :**
  ```powershell
  python partie1_env.py
  ```
  *Résultat :*
  ```text
  ==================================================
  Vérification des clés API (Partie 1)
  ==================================================
  [SUCCÈS] GROQ_API_KEY (Gratuit) détectée : gsk_iUQN...FSUp
  ```

---

### Partie 2 : Configuration du LLM (Questions 5 à 7)
- **Question 5 & 6 (Impact de la température) :**
  - **Température basse (`0.2`) :** Le modèle produit des réponses prévisibles, stables et directes, idéales pour un agent logique.
  - **Température haute (`1.0`) :** Le modèle diversifie son vocabulaire et sa créativité.
- **Question 7 :** Test avec la consigne *« Écris une phrase motivante pour moi »*.
  ```powershell
  python partie2_llm.py
  ```
  *Sortie :*
  ```text
  --- Test avec température = 0.2 (Précis, stable) ---
  Réponse : « Chaque petit pas que tu fais aujourd’hui construit le grand succès de demain ; persévère, tu es déjà en train de créer ton avenir. »

  --- Test avec température = 1.0 (Plus créatif, varié) ---
  Réponse : « Chaque petit pas que tu fais aujourd’hui construit le grand avenir que tu désires : avance avec confiance, le succès t’attend ».
  ```

---

### Partie 3 : Création de Tools (Questions 8 à 11)
- Outil `addition` : Calcule la somme arithmétique de nombres passés en paramètre.
- Outil `celsius_to_fahrenheit` : Convertit une température en degrés Celsius vers Fahrenheit selon la formule :
  $$F = (C \times 9/5) + 32$$
- Des docstrings claires sont associées via le décorateur `@tool` pour guider la sélection d'outil de l'agent.
- **Tests unitaires indépendants :**
  ```powershell
  python partie3_tools.py
  ```
  *Résultat :*
  ```text
  Addition(12.5, 7.5) = 20.0
  celsius_to_fahrenheit(25.0°C) = 77.0°F
  [SUCCÈS] Tous les tests de Tools ont réussi avec succès !
  ```

---

### Partie 4 : Ajout d'une Memory (Questions 12 & 13)
- Utilisation de `ConversationBufferMemory` pour mémoriser l'historique conversationnel.
- **Test avec questions successives :**
  ```powershell
  python partie4_memory.py
  ```
  - **Question 1 :** *« Bonjour, je m'appelle Alice et j'habite à Paris. »*
  - **Question 2 :** *« Quel est mon prénom et où est-ce que j'habite ? »*
  - **Réponse de l'agent :** `Votre prénom est Alice et vous habitez Paris.`
  - **Validation :** L'agent restitue parfaitement les données conservées dans le tampon de mémoire.

---

### Parties 5 & 6 : Création de l'Agent et Tests pratiques (Questions 14 à 20)
L'agent ReAct a été instancié via `initialize_agent(..., agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION, memory=memory, verbose=True)` combinant le LLM, les deux outils et la mémoire tampon.

Exécution du script complet :
```powershell
python partie5_6_agent.py
```

#### Synthèse des tests validés :

1. **Question 16 (Calcul simple) :**
   - *Entrée :* *« Calcule 12 + 8 »*
   - *Raisonnement ReAct :*
     ```text
     Thought: Do I need to use a tool? Yes
     Action: addition
     Action Input: 12 + 8
     Observation: 20
     ```
   - *Réponse finale :* `Le résultat de 12 + 8 est 20.`

2. **Question 17 (Sollicitation de la mémoire) :**
   - *Entrée :* *« Rappelle-moi le calcul précédent et son résultat. »*
   - *Raisonnement ReAct :* Pas besoin de réexécuter d'outil, consultation directe de l'historique.
   - *Réponse finale :* `Le calcul que vous aviez demandé était 12 + 8, et le résultat était 20.`

3. **Question 18 (Conversion de température) :**
   - *Entrée :* *« Convertis 25°C en Fahrenheit. »*
   - *Réponse finale :* `25 °C correspond à 77 °F.`

4. **Question 19 (Série de 3 questions liées) :**
   - Q19.1 : *« J'ai un projet de recherche en robotique qui s'appelle RoboPulse. »*
   - Q19.2 : *« Ce projet a débuté il y a 3 ans et a une équipe de 4 ingénieurs. »*
   - Q19.3 : *« Résume-moi les informations de mon projet que je viens de te donner. »*
   - *Réponse finale :* L'agent synthétise fidèlement les 3 tours de parole (Nom: RoboPulse, Ancienneté: 3 ans, Équipe: 4 ingénieurs).

5. **Question 20 (Chaînage multi-outils) :**
   - *Entrée :* *« Calcule 5 + 7 puis convertis le résultat en Fahrenheit si c'était une température en Celsius. »*
   - *Raisonnement ReAct en deux étapes consécutives :*
     1. `Action: addition` avec `Action Input: 5, 7` $\rightarrow$ `Observation: 12`
     2. `Action: celsius_to_fahrenheit` avec `Action Input: 12` $\rightarrow$ `Observation: 53.6°F`
   - *Réponse finale :* `Le calcul 5 + 7 donne 12. Si l’on considère ce résultat comme une température en degrés Celsius, cela correspond à 53,6 °F.`
