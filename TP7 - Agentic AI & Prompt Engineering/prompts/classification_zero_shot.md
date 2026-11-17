# Classification Zero-Shot

Classe la demande étudiante sans exemples dans une ou plusieurs catégories parmi : pédagogique, scolarité, technique, examens, autre. Rends catégorie, intention et priorité (basse/normale/haute). Base-toi sur l’objet de chaque intention, pas sur un mot isolé. Une demande d’accès à un fichier est technique; une question de calendrier de séance est scolarité, sauf indication qu’il s’agit d’un examen. Si plusieurs intentions distinctes sont présentes, conserve toutes leurs catégories. Si le contexte manque, indique l’ambiguïté au lieu de supposer.
