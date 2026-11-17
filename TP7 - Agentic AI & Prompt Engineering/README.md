# TP7 — Assistant pédagogique Master IA

Ce dossier prépare les éléments demandés dans le TP7 : configuration de l’agent, prompts, ressources de démonstration, workflow et protocole de tests.

## Contenu

- [Rapport de réalisation](rapport_tp7.md) : configuration, exemples de réponses, tests, limites et étapes de validation.
- [Prompt système final](prompts/prompt_systeme.md)
- [Prompts de workflow et de classification](prompts/)
- [Ressources de démonstration](knowledge_base/)
- [Guide de démonstration pour le professeur](guide_demo_professeur.md)

## Limite de provenance

Le seul document pédagogique du module disponible dans le dépôt est le sujet du TP7. Aucun descriptif officiel du module, support de cours, calendrier, FAQ ou consigne de TP source n’est présent. Les trois fichiers de `knowledge_base/` sont donc des fixtures fictives explicitement marquées comme telles pour illustrer la recherche documentaire, les versions contradictoires et les tests. Ils ne doivent pas être présentés comme des documents officiels ni utilisés pour répondre à de vraies questions étudiantes.

La création d’un agent dans une plateforme externe, le chargement de fichiers, l’exécution avec un modèle et l’obtention d’un lien partageable ne peuvent pas être attestés à partir du dépôt. Le rapport les distingue des exemples reproductibles rédigés ici.

## Prototype local exécutable

Le concept peut être exécuté localement sans clé API avec [agent_local.py](agent_local.py).
Le moteur charge les fichiers Markdown de `knowledge_base/`, recherche les passages utiles,
privilégie les versions récentes, signale les absences et contradictions, classe les demandes,
gère une mémoire filtrée et expose le workflow en étapes.

Lancer les tests depuis ce dossier :

```powershell
python -m unittest -v test_agent_local.py
```

Cette implémentation est volontairement déterministe et ne remplace pas un modèle génératif.
Lorsque les documents officiels seront fournis, ils pourront remplacer les fixtures `DEMO_*.md`
sans modifier le workflow.

## Mode interactif

Lancer l'agent comme un environnement interactif :

```powershell
python agent_cli.py
```

Le mode recommandé pour ce projet est le moteur local, sans clé API :

```powershell
python agent_cli.py --local
```

Il est déterministe, traçable et utilise uniquement les documents présents dans
`knowledge_base/`.

L'invite `agent >>>` permet de saisir les questions. La commande `exit` quitte
l'agent et rend la main au terminal, comme `exit()` dans l'interpréteur Python.
La commande `json` active ou désactive la réponse JSON.

## Utiliser Groq

Le moteur local reste le comportement par défaut. Pour utiliser Groq, configurez
`GROQ_API_KEY` dans PowerShell puis lancez :

```powershell
python agent_cli.py --groq
```

La clé n'est jamais écrite dans le dépôt. Le modèle peut être remplacé par une
variable d'environnement `GROQ_MODEL`; par défaut, l'adaptateur utilise
`allam-2-7b`.

## Utiliser Gemini

Configurez la clé Gemini sans la partager :

```powershell
$env:GEMINI_API_KEY="NOUVELLE_CLE_GEMINI"
python agent_cli.py --gemini
```

Le modèle peut être changé avec `GEMINI_MODEL`. L'adaptateur utilise par défaut
`gemini-3.8-flash`.

## Utiliser OpenAI

Configurez la clé OpenAI sans la partager :

```powershell
$env:OPENAI_API_KEY="NOUVELLE_CLE_OPENAI"
python agent_cli.py --openai
```

Le modèle peut être changé avec `OPENAI_MODEL`; par défaut, l'adaptateur utilise
`gpt-5.4`.

## Fichier `.env`

Les clés peuvent être placées localement dans `.env`, qui est ignoré par Git :

```powershell
Copy-Item .env.example .env
```

Puis renseignez la clé du fournisseur choisi dans `.env` et lancez directement
`python agent_cli.py --gemini`, `python agent_cli.py --groq` ou
`python agent_cli.py --openai`. Ne partagez jamais `.env` et ne committez jamais
de clé API. Le projet charge automatiquement ce fichier sans dépendance externe.
