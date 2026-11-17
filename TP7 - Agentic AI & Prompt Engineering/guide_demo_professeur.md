# Guide de démonstration — Assistant pédagogique Master IA

## 1. Présentation du projet

L'agent est un assistant pédagogique pour les étudiants du Master IA. Il recherche
les informations dans une base documentaire, classe les demandes, cite ses sources,
signale les informations absentes ou contradictoires et conserve uniquement le
contexte utile.

Le projet fonctionne localement sans clé API. Les fichiers `DEMO_*.md` sont des
fixtures fictives de démonstration et ne constituent pas des documents officiels
du cours.

## 2. Lancer l'agent local

Depuis le dossier du projet :

```powershell
python agent_cli.py --local
```

L'invite apparaît :

```text
agent >>>
```

Une interface web est également disponible :

```powershell
python web_app.py
```

Ouvrir ensuite `http://127.0.0.1:8000`. Les requêtes d'exemple sont proposées
au-dessus de la zone de conversation.

L'interface web accepte également l'ajout temporaire de fichiers `.md`, `.txt`,
`.json` et `.csv`. Après import, posez une question portant sur le document :
l'agent recherche le passage utile et cite le fichier importé. Les PDF doivent
être convertis en texte avant import dans cette version.

Si le port 8000 est occupé, utiliser :

```powershell
python web_app.py --local --port 8765
```

Commandes disponibles :

```text
help    Afficher l'aide
json    Activer ou désactiver la sortie JSON
clear   Effacer l'écran
exit    Quitter l'agent
```

## 3. Questions à démontrer

### Question documentée

```text
Quels thèmes sont abordés dans le module ?
```

Résultat attendu : catégorie `pédagogique`, réponse sur le prompting, les outils,
la mémoire, la récupération documentaire et l'évaluation, avec la source
`DEMO_descriptif_module.md`.

### Question sans information disponible

```text
Quel est le numéro de salle ?
```

Résultat attendu : l'agent indique que l'information n'apparaît pas dans les
documents et propose de contacter le responsable. Il ne doit pas inventer un numéro.

### Question ambiguë

```text
La séance est-elle maintenue ?
```

Résultat attendu : l'agent utilise le calendrier disponible. La version v2 remplace
v1 et indique que la séance est reportée, sans inventer une date de remplacement.

### Document obsolète et version récente

```text
La séance de démonstration est-elle maintenue ?
```

Résultat attendu : priorité à `DEMO_calendrier_v2.md`, car v2 indique explicitement
qu'elle remplace v1.

### Demande multiple

```text
Je n'arrive pas à accéder au support et je ne sais pas si la séance est maintenue.
```

Résultat attendu :

- intention technique : aucune procédure d'accès n'est documentée ;
- intention scolarité : la version v2 indique un report ;
- escalade vers les responsables compétents ;
- aucune action non autorisée.

### Question d'examen non documentée

```text
Quelle est la date de l'examen final ?
```

Résultat attendu : catégorie `examens`, priorité `haute`, information absente et
aucune date inventée.

### Question hors périmètre

```text
Quel ordinateur dois-je acheter ?
```

Résultat attendu : catégorie `autre`, aucune source documentaire pertinente.

### Questions qui doivent éviter les faux positifs

```text
Peux-tu m'expliquer la différence entre un agent et un LLM ?
Où en est ma demande d'inscription ?
Quelle est la date exacte de remise du rapport ?
```

Résultat attendu : l'agent signale l'absence d'une preuve documentaire directement
pertinente. Il ne doit pas utiliser une consigne de TP ou un calendrier hors sujet.

## 4. Tester la sortie JSON

Dans l'agent, taper :

```text
json
```

Puis :

```text
Quels thèmes sont abordés dans le module ?
```

Le résultat doit être un objet JSON valide contenant exactement :

```json
{
  "categorie": "pédagogique",
  "intention": "Quels thèmes sont abordés dans le module ?",
  "priorite": "normale",
  "reponse": "...",
  "source": "..."
}
```

Pour revenir au format normal, taper de nouveau :

```text
json
```

## 5. Tester la mémoire et le filtrage du contexte

Le test Python suivant conserve uniquement l'information utile :

```powershell
python
```

```python
from agent_local import LocalAgent

agent = LocalAgent("knowledge_base")
agent.remember("groupe", "TP Atlas")
agent.remember("projet", "assistant de recherche documentaire")
agent.remember("vacances", "Marrakech")
print(agent.filtered_context("Quel est notre projet de recherche documentaire ?"))
```

Résultat attendu :

```python
{'projet': 'assistant de recherche documentaire'}
```

La destination de vacances n'est pas réutilisée car elle n'est pas pertinente.

## 6. Tester le workflow

```python
import pprint
pprint.pp(agent.workflow(
    "Je n'arrive pas à accéder au support et la séance est-elle maintenue ?"
))
```

Le workflow contient :

1. analyse et classification ;
2. recherche des passages ;
3. vérification des versions et des contradictions ;
4. formulation de la réponse ;
5. escalade si nécessaire.

## 7. Tests automatiques

```powershell
python -m unittest -v test_agent_local.py
```

Résultat attendu :

```text
Ran 16 tests
OK
```

## 8. Utilisation d'une API externe

Les clés API ne doivent jamais être écrites dans le code, le rapport ou ce fichier.
Elles ne doivent pas être envoyées dans une conversation.

Les variables peuvent être placées dans le fichier local `.env`, ignoré par Git,
à partir de `.env.example`. Ne jamais montrer ce fichier pendant la démonstration.

### OpenAI

```powershell
$env:OPENAI_API_KEY="CLE_NON_PARTAGEE"
python agent_cli.py --openai
```

Une erreur `429` avec « no credits remaining » signifie que la clé est reconnue,
mais que le compte API n'a plus de crédits. Il faut ajouter un moyen de paiement
ou revenir au moteur local.

### Gemini

```powershell
$env:GEMINI_API_KEY="CLE_NON_PARTAGEE"
python agent_cli.py --gemini
```

Une erreur `503` signifie généralement que le modèle est temporairement surchargé.
Un timeout signifie que le serveur n'a pas répondu dans le délai. Les solutions
sont :

1. attendre puis relancer ;
2. choisir un modèle disponible dans Google AI Studio ;
3. vérifier la connexion réseau vers
   `generativelanguage.googleapis.com` ;
4. vérifier que la clé appartient bien à l'API Gemini ;
5. revenir au mode local si le service reste indisponible.

Une erreur `403` indique plutôt un accès refusé ou une clé invalide. Il faut
révoquer la clé concernée, en créer une nouvelle et ne jamais la partager.

### Groq

```powershell
$env:GROQ_API_KEY="CLE_NON_PARTAGEE"
python agent_cli.py --groq
```

Une erreur `403` signifie que Groq refuse la clé ou l'accès au compte. Le moteur
local reste disponible avec `python agent_cli.py`.

## 9. Limites à présenter honnêtement

- Les fixtures `DEMO_*.md` sont fictives.
- Le moteur local est déterministe et ne remplace pas un modèle génératif.
- Aucun lien vers un agent déployé n'est encore fourni.
- Les réponses propres au vrai cours nécessitent les documents officiels.
- Une API externe dépend de la clé, des crédits, du modèle et de la disponibilité
  du fournisseur.
