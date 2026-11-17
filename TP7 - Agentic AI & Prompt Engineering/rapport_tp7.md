# TP7 — Création et configuration d’un agent IA

**Module :** IADS — M2I, S3 Automation & Agentic AI  
**Enseignante indiquée sur le sujet :** Prof. Imane Lahbari  
**Agent cible :** Assistant pédagogique — Master IA

## 1. État de réalisation et provenance

Le dépôt fournit le sujet `TP 7 Agent AI with prompt & contex eng.pdf`, mais ne fournit pas de descriptif officiel du module, de support de cours, de consigne de TP, de FAQ ni de calendrier. Aucun accès à une plateforme de création d’agent ou à une base documentaire externe n’est configuré dans ce dossier. En conséquence, ce rapport prépare une configuration et consigne des tests de conception sur des fixtures locales; il ne prétend pas qu’un agent externe a été créé, que des appels à un modèle ont été exécutés, ou que des documents officiels ont été indexés.

Les fichiers `DEMO_*.md` dans `knowledge_base/` sont des documents fictifs écrits pour rendre les scénarios de test vérifiables. Ils ne doivent pas être cités comme sources réelles du cours. Les mentions de « résultat obtenu » ci-dessous désignent le comportement attendu lors d’une simulation sur ces fixtures, pas la sortie observée d’un modèle distant. Les comparaisons Zero-Shot/Few-Shot sont des exemples d’analyse, sans exécution modèle vérifiable.

## 2. Configuration proposée (exercice 1)

- **Nom :** Assistant pédagogique — Master IA.
- **Description :** Assistant en français pour les étudiants de Master, répondant aux questions sur le module à partir des ressources pédagogiques fournies et signalant clairement les limites des sources.
- **Mission :** aider à comprendre le module, retrouver les consignes documentées, classer les demandes et orienter les cas administratifs ou non résolus.
- **Prompt système :** voir [prompts/prompt_systeme.md](prompts/prompt_systeme.md). Il précise rôle, public, tâches autorisées, limites, ton, langue, citations, ambiguïtés, contradictions et format de réponse.

### Exemples de réponses de conception

**Question documentée dans une fixture :** « Quel est l’objectif du module ? »

> **Réponse directe :** Dans la ressource de démonstration, l’objectif est de découvrir la conception d’agents IA, l’ingénierie des prompts et la gestion du contexte.  
> **Explication / étapes :** Le descriptif fictif cite aussi le prompting, les outils, la mémoire, la récupération documentaire et l’évaluation.  
> **Source documentaire :** `DEMO_descriptif_module.md`, sections « Public et objectif » et « Thèmes de démonstration ».  
> **Information manquante / suite :** Cette ressource est une fixture, pas le descriptif officiel du cours.

**Question hors périmètre :** « Quel ordinateur dois-je acheter ? »

> **Réponse directe :** Je ne peux pas recommander un modèle à partir des documents de ce module.  
> **Explication / étapes :** Cette demande ne porte pas sur les ressources pédagogiques disponibles.  
> **Source documentaire :** Aucune source disponible.  
> **Information manquante / suite :** Précisez vos usages et votre budget, ou consultez une source spécialisée.

**Question ambiguë :** « La séance est maintenue ? »

> **Réponse directe :** De quelle séance et de quelle date parlez-vous ?  
> **Explication / étapes :** La question ne précise pas la séance. Dans les fixtures, v1 et v2 diffèrent et v2 indique un report.  
> **Source documentaire :** `DEMO_calendrier_v1.md` et `DEMO_calendrier_v2.md`, section « Séance de démonstration » / « Mise à jour ».  
> **Information manquante / suite :** Confirmer la séance visée et vérifier le calendrier officiel auprès de l’enseignante.

## 3. Documents et gestion du contexte (exercice 2)

Les ressources disponibles dans cette configuration de démonstration sont :

1. `DEMO_descriptif_module.md` — thèmes fictifs du module.
2. `DEMO_consigne_tp.md` — exigences fictives du rapport de test.
3. `DEMO_calendrier_v1.md` — ancienne version fictive.
4. `DEMO_calendrier_v2.md` — version fictive mise à jour qui remplace explicitement v1.

Ce nombre satisfait le minimum pour une démonstration, mais pas l’objectif d’exploiter des ressources pédagogiques **fournies** : aucun document officiel n’a été retrouvé dans le dépôt.

### Quatre questions et preuves (fixtures uniquement)

| Question | Réponse simulée | Document et passage justificatif |
|---|---|---|
| Quels thèmes sont abordés ? | Prompting, outils, mémoire, récupération documentaire et évaluation. | `DEMO_descriptif_module.md`, « Thèmes de démonstration ». |
| Que doit contenir le rapport de test ? | Résultat attendu, obtenu et statut; les réponses doivent citer leur source. | `DEMO_consigne_tp.md`, « Livrable de démonstration ». |
| Que dit la fixture la plus récente sur la séance ? | Elle est reportée; aucune date de remplacement n’est donnée. | `DEMO_calendrier_v2.md`, « Mise à jour ». v2 dit remplacer v1. |
| Quelle est la date de remplacement ? | Elle n’est pas indiquée. | `DEMO_calendrier_v2.md`, « Mise à jour ». Aucune date n’y figure. |

**Absence contrôlée :** à « Quel est le numéro de salle ? », la réponse de conception est « L’information n’apparaît pas dans les documents disponibles. » La source reste vide et l’étudiant est renvoyé vers la personne responsable.

**Sélection du contexte :** la consigne de recherche ne transmet que les extraits soutenant directement l’intention courante, leur titre/version/localisation et l’extrait exact. Les passages sans rapport sont exclus. Avant modification, un contexte entier (v1 et v2 inclus) peut laisser apparaître une contradiction sans priorité explicite; après modification, la vérification de version retient v2 parce que celle-ci déclare remplacer v1. La réponse reste limitée au fait « reportée » et ne crée pas de nouvelle date.

## 4. Techniques de prompting et tests de classification (exercice 3)

Les consignes figurent dans [classification_zero_shot.md](prompts/classification_zero_shot.md) et [classification_few_shot.md](prompts/classification_few_shot.md). Même jeu de cinq demandes pour comparer les deux variantes :

| Demande | Zero-Shot attendu | Few-Shot attendu | Analyse de conception |
|---|---|---|---|
| « Explique-moi ce qu’est un agent IA. » | pédagogique | pédagogique | Intention d’apprentissage explicite. |
| « Où en est mon inscription ? » | scolarité | scolarité | Suivi administratif. |
| « Le lien du support renvoie une erreur 403. » | technique | technique | Problème d’accès. |
| « Quelle est la date de l’examen final ? » | examens | examens | Question sur une épreuve. |
| « Peux-tu recommander un club de randonnée ? » | autre | autre | Hors module. |

Exemples Few-Shot distincts sont fournis pour les cinq catégories. La demande double d’accès au support et de maintien de séance doit donner `technique` + `scolarité`. Pour éviter de classer une demande à partir d’un mot isolé, la consigne indique de classer par intention. Aucune comparaison empirique entre modèles n’est revendiquée; il faudra relancer exactement les mêmes demandes avec le même modèle dans la plateforme choisie.

### Sorties JSON d’exemple

Les objets suivants illustrent le schéma demandé; ils n’ont pas été générés par un modèle. Ils sont valides JSON et contiennent chacun les cinq clés.

```json
{"categorie":"pédagogique","intention":"Comprendre la notion d’agent IA","priorite":"normale","reponse":"Je peux expliquer la notion à partir du support de cours. Aucun support officiel n’est encore chargé.","source":""}
{"categorie":"technique","intention":"Signaler une erreur 403 sur le support","priorite":"normale","reponse":"Le problème d’accès est identifié, mais aucune procédure de dépannage n’est documentée ici.","source":""}
{"categorie":["technique","scolarité"],"intention":"Accéder au support et vérifier le maintien de la séance","priorite":"normale","reponse":"Je ne peux confirmer ni l’accès ni le maintien sans source officielle; contactez l’enseignante ou le service compétent.","source":""}
```

## 5. Workflow, chaînage et escalade (exercice 4)

Prompts successifs : [prompts/workflow.md](prompts/workflow.md).

```text
Demande étudiante
  → 1. Extraire/classer chaque intention
  → 2. Rechercher seulement les passages correspondants
  → 3. Vérifier pertinence, dates, versions et contradictions
  → 4. Répondre avec source et limites
  → 5. Escalader vers un responsable si absent, contradictoire ou administratif
```

**Cas demandé :** « Je n’arrive pas à accéder au support du TP et je ne sais pas si la séance est maintenue. »

- Étape 1 : intention A, accès au support (`technique`); intention B, maintien de séance (`scolarité`).
- Étape 2 : la recherche sur la fixture peut retrouver les deux calendriers, mais aucun document ne donne une procédure d’accès au support.
- Étape 3 : v2 remplace explicitement v1 et indique un report; aucune date nouvelle n’est fournie. Les fixtures ne sont pas officielles.
- Étape 4 : répondre séparément : problème technique sans solution documentée; séance indiquée reportée uniquement dans la fixture.
- Étape 5 : demander confirmation à l’enseignante pour le calendrier réel et orienter vers le responsable technique pour l’accès. L’agent ne déclare pas avoir réparé le lien ni contacté ces personnes.

La même règle couvre une recherche sans résultat et des documents contradictoires sans marqueur clair de remplacement : exposer la limite et escalader, sans arbitrage inventé.

## 6. Mémoire et filtrage du contexte (exercice 5)

Scénario de test fictif dans une conversation : « Groupe TP Atlas; projet : assistant de recherche documentaire. » Questions de suivi : « Quel est notre projet ? », puis « Quel groupe dois-je citer dans le compte rendu ? ». Résultats attendus : réutiliser ces deux éléments dans la conversation active. Ce test n’atteste aucune mémoire persistante de plateforme.

Résumé de session (5 éléments maximum) :

1. Groupe : TP Atlas (fictif).
2. Projet : assistant de recherche documentaire (fictif).
3. Objectif courant : préparer le rapport de TP7.
4. Les ressources de cours officielles ne sont pas présentes dans le dépôt.
5. Les fichiers `DEMO_*.md` sont fictifs et ne doivent pas servir de preuve réelle.

Dans une nouvelle conversation, ce résumé suffit à reprendre le travail de rapport sans historique antérieur, mais pas à répondre à des questions de cours non documentées. Pour le test de filtrage, on peut ajouter des préférences sans rapport (couleur préférée, destination de vacances); à la question sur le livrable, seuls le TP7 et les instructions du rapport sont pertinents. Les informations personnelles superflues ne sont pas réutilisées.

## 7. Évaluation finale (exercice 6)

Résultats de simulation fondés sur les fixtures et les règles ci-dessus, pas sur des réponses d’un agent exécuté.

| # | Cas | Résultat attendu | Résultat obtenu en simulation | Statut |
|---:|---|---|---|---|
| 1 | Question documentée : thèmes du module | Réponse avec extrait et source | Réponse appuyée par `DEMO_descriptif_module.md`; réserve fixture rappelée | réussi (simulation) |
| 2 | Information absente : salle | Dire que l’information manque, sans supposition | Absence signalée et orientation vers responsable | réussi (simulation) |
| 3 | Demande ambiguë : « La séance est maintenue ? » | Demander quelle séance; ne pas conclure sans contexte fiable | Clarification demandée; contradiction/version indiquée | réussi (simulation) |
| 4 | Document obsolète : calendrier v1 contre v2 | Privilégier la version explicitement plus récente | v2 retenue car elle remplace v1; date non inventée | réussi (simulation) |
| 5 | Demandes multiples : accès + séance | Traiter les deux intentions et sources séparément | `technique` + `scolarité`; limites distinctes et escalade | réussi (simulation) |
| 6 | Sortie JSON | JSON valide avec les cinq clés requises | Trois exemples structurés incluent les clés; génération modèle à vérifier | réussi (schéma seulement) |

### Améliorations apportées après revue de conception

1. **Risque de réponse supposée sur une information absente :** ajout d’une formule explicite d’absence, de la règle « aucune source = aucune affirmation factuelle » et de l’escalade au responsable.
2. **Risque de confusion entre versions :** ajout d’une étape dédiée à la date et au statut de remplacement; si le remplacement n’est pas explicite, l’agent présente la contradiction et demande confirmation.
3. **Risque de ne traiter qu’une partie d’une demande composite :** le workflow et les exemples imposent l’extraction d’intentions séparées.

Les cas 2, 4 et 5 ont été rejoués sur papier après modification et satisfont les critères simulés. Une véritable relance doit être réalisée dans la plateforme et consignée avec modèle, date et sorties brutes.

## 8. Accès à l’agent et éléments restant à valider

- **Accès/lien :** aucun agent externe n’a été créé; aucun lien partageable n’existe encore.
- **Prompt final :** [prompts/prompt_systeme.md](prompts/prompt_systeme.md).
- **Documents utilisés dans cette démonstration :** les quatre fixtures `DEMO_*.md`; elles ne sont pas officielles.
- **Workflow :** détaillé ci-dessus et dans [prompts/workflow.md](prompts/workflow.md).
- **À faire dans la plateforme de l’établissement :** charger au moins trois documents officiels, lancer les tests Zero-Shot puis Few-Shot avec le même modèle, vérifier réellement le JSON, le retrieval, la mémoire et le comportement face aux versions; conserver les sorties brutes et créer/partager l’agent si autorisé.
