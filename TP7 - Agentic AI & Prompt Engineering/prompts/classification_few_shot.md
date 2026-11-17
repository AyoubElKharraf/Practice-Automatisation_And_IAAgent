# Classification Few-Shot

Classe chaque intention dans une ou plusieurs catégories parmi : pédagogique, scolarité, technique, examens, autre. Renvoie aussi l’intention et priorité basse/normale/haute. Classe selon le besoin réel, et non un terme isolé. Sépare les intentions multiples.

Exemples :

- « Peux-tu m’expliquer la différence entre un agent et un LLM ? » → pédagogique, comprendre une notion, normale.
- « Où en est ma demande d’inscription ? » → scolarité, suivi administratif, normale.
- « Le lien du support renvoie une erreur 403. » → technique, résoudre un problème d’accès, normale.
- « Quelle est la date de l’examen final ? » → examens, connaître la date d’une épreuve, haute.
- « Peux-tu recommander un club de randonnée ? » → autre, recommandation hors module, basse.
- « Je n’arrive pas à ouvrir le support et la séance est-elle maintenue ? » → technique + scolarité, accès au support et confirmation de séance, normale.

Ne fabrique aucune information de réponse ou source. Si des faits du module sont demandés, réponds uniquement avec des passages récupérés; sinon indique qu’il faut vérifier auprès du responsable.
