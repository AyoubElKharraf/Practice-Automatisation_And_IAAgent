# Workflow en prompts successifs

## Étape 1 — Analyser

Extrais chaque intention distincte. Pour chaque intention, donne la catégorie, la question à résoudre, les précisions manquantes et une priorité. N’apporte pas encore de réponse factuelle.

## Étape 2 — Rechercher

À partir des intentions, cherche dans la base documentaire uniquement les passages directement pertinents. Retourne pour chaque passage : identifiant/titre du document, version ou date si disponible, section/page, extrait exact et intention concernée. Si rien ne correspond, le dire.

## Étape 3 — Vérifier

Pour chaque intention, vérifie que l’extrait soutient réellement la réponse. Compare les dates et versions. Signale toute contradiction, absence ou ambiguïté; n’infère pas une décision administrative.

## Étape 4 — Répondre

Rédige une réponse par intention selon le format du prompt système. Cite les sources vérifiées. En l’absence d’information ou en cas de contradiction non résolue, explique la limite et oriente vers le responsable compétent. Ne prétends pas avoir effectué une action.
