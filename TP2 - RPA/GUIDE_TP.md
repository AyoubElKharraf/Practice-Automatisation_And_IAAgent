# Guide du TP2 — Automatisation du traitement des factures

Ce guide évolue au fur et à mesure des étapes. Les résultats ci-dessous distinguent les vérifications réellement effectuées de celles qui restent à faire.

## 1. Énoncé résumé

Le document `TP 2.pdf` demande de développer en Python un petit robot RPA qui :

1. prépare un dossier `Factures` avec au moins cinq factures contenant un numéro, un fournisseur, une date et un montant ;
2. parcourt ce dossier, lit les factures et rassemble les informations dans un `DataFrame` Pandas ;
3. classe chaque facture comme **Normal** si le montant est inférieur ou égal à 1 000 MAD, et **À contrôler** s'il dépasse 1 000 MAD ;
4. produit `rapport_factures.xlsx` avec les informations extraites et le statut ;
5. déplace les factures normales dans `Factures/Traitees/` et celles à contrôler dans `Factures/A_controler/` ;
6. envoie un email au responsable pour chaque facture à contrôler ;
7. traite les cas de fichier illisible, d'information manquante et de montant incorrect ;
8. ajoute dans `log.txt` les opérations effectuées avec leur date et heure.

La validation demandée porte sur l'extraction, le rapport Excel, le classement, les notifications et les erreurs.

## 2. État de départ constaté

Au départ, les fichiers présents dans le dossier du TP étaient :

- `TP 2.pdf` : énoncé d'une page ;
- `tp2.py` : script Python déjà commencé ;
- `tests/test_tp2.py` : tests unitaires ajoutés à l'étape 1 ;
- `GUIDE_TP.md` : ce guide, ajouté pendant l'étape de prise de connaissance.

Au début du TP, le script contenait déjà une chaîne de traitement complète : création de sept factures d'exemple, extraction avec des expressions régulières, décision par seuil, export Excel, déplacement des fichiers, tentative de notification email et journalisation.

Points observés pendant les vérifications :

- les paramètres email sont maintenant lus depuis des variables d'environnement, et un envoi est ignoré si une des trois valeurs requises manque ;
- l'exécution de `main()` peut créer des fichiers, déplacer des factures et tenter d'envoyer de vrais emails ;
- les dates sont extraites sous forme de texte et ne sont pas validées comme dates ;
- après classement, les factures valides ne sont plus à la racine de `Factures` ; le script ne les retraitera pas au prochain lancement. Les deux factures invalides restent à la racine.

Après réalisation du TP, sept factures d'exemple se trouvent sous `Factures/` : cinq ont été classées, et deux exemples invalides sont restés à la racine pour illustrer les erreurs.

## 3. Ordre de travail proposé

| Étape | Objectif | Pourquoi dans cet ordre ? |
|---|---|---|
| 0. Comprendre le TP et établir ce guide | Résumer la consigne, inventorier le code et les risques | Éviter de supposer les attentes et préserver les fichiers existants. **Terminé.** |
| 1. Vérifier les fonctions sans effet externe | Tester l'extraction, les erreurs et la règle des 1 000 MAD avec des données sûres | On valide les bases avant les actions qui modifient des fichiers. **Terminé.** |
| 2. Vérifier le flux complet en environnement temporaire | Contrôler le rapport, le classement et les journaux ; neutraliser les emails | Tester la chaîne entière sans toucher aux factures de l'utilisateur ni contacter un destinataire. **Terminé.** |
| 3. Vérifier le contenu des notifications | Simuler le serveur SMTP et contrôler le message sans l'expédier | Le test couvre la dernière fonction non encore exercée, sans effet externe. **Terminé.** |
| 4. Compléter les cas d'erreur et corriger les écarts confirmés | Vérifier aussi l'accès à un fichier illisible ; corriger uniquement si un test révèle un défaut | Cela couvre explicitement tous les cas d'erreur cités dans le sujet. **Terminé.** |
| 5. Exécuter le robot sur les exemples du TP | Créer et classer les factures dans `Factures/`, générer le rapport et le journal | Confirmer le résultat dans le véritable dossier TP, sans envoyer d'email. **Terminé.** |
| 6. Faire le bilan | Lister ce qui a été exécuté, les limites et les commandes de relance | Ne déclarer comme réussi que ce qui a été effectivement vérifié. **Terminé.** |

## 4. Notions à retenir

- **RPA** : automatiser une suite d'actions répétitives qui seraient autrement réalisées manuellement.
- **Expression régulière (`re`)** : motif utilisé ici pour retrouver les champs écrits dans les fichiers texte.
- **DataFrame Pandas** : tableau en mémoire, avec des lignes (factures) et des colonnes (numéro, fournisseur, etc.).
- **Seuil de décision** : règle métier qui transforme un montant en statut. La consigne inclut bien 1 000 MAD dans la catégorie **Normal**.
- **Journal (`log.txt`)** : historique horodaté utile pour comprendre ce que le programme a fait ou signaler une erreur.
- **Test isolé** : essai sur des données temporaires et contrôlées, pour ne pas déplacer les vrais fichiers ni contacter un destinataire.

## 5. Environnement et commandes

Dossier du TP sur cet ordinateur :

```powershell
Set-Location -LiteralPath 'C:\Users\DELL\Documents\Master\Master_M2I\SEMESTRE 3\Automatisation IA_Agent\TPs\TP2'
```

Dépendances mentionnées par le script (`pandas` et `openpyxl`) :

```powershell
& 'C:\Python314\python.exe' -m pip install pandas openpyxl
```

Cette commande est indiquée pour référence et **n'a pas été lancée dans le terminal**. L'interpréteur sélectionné est `C:\Python314\python.exe` (Python 3.14.7). Pandas est présent ; `openpyxl` a été installé dans cet environnement après l'échec du test intégré dû à son absence.

**Attention :** `tp2.py` peut déplacer les factures et envoyer de vrais emails si la configuration est définie. Il est maintenant configuré pour lire les variables d'environnement `TP2_SMTP_EMAIL`, `TP2_SMTP_APP_PASSWORD` et `TP2_RESPONSABLE_EMAIL`. Si l'une d'elles manque, le robot journalise que la notification est ignorée. Ne mets jamais le mot de passe dans le code ou le guide.

## 6. Journal de progression et vérifications

### Étape 0 — Prise de connaissance

- **Réussi :** lecture du script et de l'énoncé PDF ; les objectifs ci-dessus sont issus de ces fichiers.
- **Réussi :** diagnostic Pylance du fichier sans erreurs ni avertissements retournés (`items: []`).
- **Réussi :** vérification Git ciblée : `tp2.py` et `TP 2.pdf` sont des fichiers non suivis ; ils existaient avant l'ajout de ce guide. D'autres changements existent ailleurs dans le dépôt et ne sont pas concernés.
- **À la fin de cette étape :** aucune exécution du programme, aucun test fonctionnel et aucune installation de dépendance. À cet instant, aucune facture n'avait été déplacée et aucun email n'avait été envoyé.
- **Résultat à cette étape :** la prise de connaissance était terminée ; l'étape 1 a ensuite été réalisée et ses résultats sont consignés ci-dessous.

### Étape 1 — Tests unitaires sûrs

- **Objectif :** vérifier séparément l'extraction, deux erreurs de données et la règle de décision, sans lancer `main()`.
- **Fichier ajouté :** `tests/test_tp2.py`. Les factures utilisées sont écrites dans des répertoires temporaires et supprimées par le mécanisme de test.
- **Notions :** `unittest` organise les vérifications ; `TemporaryDirectory` isole les fichiers de test ; la règle testée couvre 500 MAD, exactement 1 000 MAD et 1 000,01 MAD.
- **Environnement constaté :** interpréteur sélectionné `C:\Python314\python.exe` (Python 3.14.7) ; Pandas est importable (version 3.0.2 selon l'inventaire Pylance).
- **Commande exécutée :**

  ```powershell
  Set-Location -LiteralPath 'C:\Users\DELL\Documents\Master\Master_M2I\SEMESTRE 3\Automatisation IA_Agent\TPs\TP2'
  & 'C:\Python314\python.exe' -m unittest discover -s tests -v
  ```

- **Résultat vérifié à cette étape :** les quatre premiers tests réussissaient : extraction d'une facture valide, information manquante, montant invalide et seuil inclusif de 1 000 MAD (`Ran 4 tests ... OK`). La suite a ensuite été complétée ; son résultat final est rapporté plus bas.
- **Vérification de syntaxe :** Pylance n'a trouvé aucune erreur de syntaxe dans `tests/test_tp2.py`.
- **Limites :** le lanceur de tests intégré n'a pas détecté les tests ; la commande standard `unittest` les a trouvés et exécutés. Aucun test du rapport Excel, du déplacement réel, de l'envoi d'email ni du script complet n'a encore été réalisé.
- **Aucun effet externe :** `main()` n'a pas été appelé ; les factures du TP n'ont pas été touchées et aucun email n'a été envoyé.
- **Résultat :** cette première vérification est terminée.

### Étape 2 — Flux complet en répertoire temporaire

- **Objectif :** exécuter `main()` sur les sept factures d'exemple, en redirigeant les dossiers, le rapport et le journal dans un répertoire temporaire et en remplaçant l'envoi email par un simulacre.
- **Notions :** `unittest.mock.patch` remplace temporairement les chemins et la fonction email ; `TemporaryDirectory` supprime les fichiers de test en fin d'essai.
- **Échec initial observé :** l'export Excel a échoué avec `ModuleNotFoundError: No module named 'openpyxl'`. Cela a confirmé que le paquet manquait à l'interpréteur utilisé.
- **Action effectuée :** installation de `openpyxl` dans l'interpréteur sélectionné via l'outil d'installation Python ; aucun fichier du projet ni manifeste de dépendances n'a été modifié.
- **Commande de réinstallation si nécessaire :**

  ```powershell
  & 'C:\Python314\python.exe' -m pip install pandas openpyxl
  ```

  Cette commande est une instruction de reprise ; elle n'a pas été lancée dans le terminal.
- **Commande de test relancée :**

  ```powershell
  Set-Location -LiteralPath 'C:\Users\DELL\Documents\Master\Master_M2I\SEMESTRE 3\Automatisation IA_Agent\TPs\TP2'
  & 'C:\Python314\python.exe' -m unittest discover -s tests -v
  ```

- **Résultat vérifié :** les cinq tests réussissent (`Ran 5 tests ... OK`). Le test intégré vérifie le fichier Excel et ses cinq lignes/statuts, les cinq déplacements attendus, le maintien des deux factures invalides dans le dossier d'entrée et deux appels à la fonction email simulée.
- **Aucun effet externe :** aucun email réel n'a été envoyé. Les écritures et déplacements ont eu lieu uniquement dans le répertoire temporaire, supprimé en fin de test.
- **Limites :** le contenu détaillé du message email n'a pas encore été vérifié ; les dates n'ont pas été validées comme dates calendaires.
- **Résultat :** le flux intégré en zone temporaire est vérifié.

### Étape 3 — Notification email simulée

- **Objectif :** vérifier le destinataire, le sujet et le corps du message sans connexion SMTP réelle.
- **Notions :** `unittest.mock.patch` remplace `SMTP_SSL` par un objet fictif ; le test décode les en-têtes et la partie texte MIME avant de vérifier le contenu.
- **Essais intermédiaires :** le premier test a dû être corrigé car le corps était dans une partie MIME interne, puis car le sujet accentué était encodé conformément au format email. Ces erreurs concernaient la lecture du message par le test, pas une défaillance du code de notification.
- **Commande exécutée :**

  ```powershell
  Set-Location -LiteralPath 'C:\Users\DELL\Documents\Master\Master_M2I\SEMESTRE 3\Automatisation IA_Agent\TPs\TP2'
  & 'C:\Python314\python.exe' -m unittest discover -s tests -v
  ```

- **Résultat vérifié :** les six tests passent (`Ran 6 tests ... OK`). Le test vérifie le sujet décodé, le destinataire et les champs numéro/fournisseur/montant. Le faux serveur confirme que le code a construit un envoi, sans ouvrir de connexion réseau.
- **Vérification de syntaxe :** aucune erreur de syntaxe signalée par Pylance dans le fichier de test.
- **Limites :** la remise effective d'un email n'a volontairement pas été testée ; le sujet demande l'automatisation, mais un envoi réel nécessite une adresse et une configuration locales et ne sera fait qu'après accord explicite.
- **Résultat :** le message email est vérifié par simulation.

### Étape 4 — Cas d'erreur du sujet

- **Objectif :** vérifier les quatre situations attendues : fichier illisible, champ absent, montant vide et montant non numérique.
- **Méthode sûre :** le test du fichier illisible écrit des octets qui ne sont pas du texte UTF-8 dans un fichier temporaire ; cela reproduit une erreur de lecture sans modifier les droits d'accès Windows.
- **Résultat vérifié à ce moment :** les huit tests passaient (`Ran 8 tests ... OK`), dont les nouveaux tests pour le fichier illisible et le montant vide. La configuration des emails a ensuite été sécurisée ; cette modification est couverte par les tests finaux ci-dessous.
- **Vérification de syntaxe :** aucune erreur de syntaxe signalée par Pylance dans le fichier de test.
- **Limites restantes :** la date est extraite comme texte, sans validation calendaire ; le code SMTP réel n'a pas été contacté. L'énoncé ne demande pas explicitement de valider la date.
- **Aucun effet externe :** tous les fichiers de test ont été créés dans des répertoires temporaires ; aucun email n'a été envoyé.
- **Résultat :** les cas d'erreur énoncés sont testés.

### Étape 5 — Préparation et traitement dans le dossier TP2

- **Préparation :** le dossier `Factures/` était absent. Sept factures d'exemple y ont été créées : cinq avec des montants valides, une sans montant et une avec un montant incorrect.
- **Sécurité email :** les paramètres codés en dur ont été remplacés par les variables d'environnement `TP2_SMTP_EMAIL`, `TP2_SMTP_APP_PASSWORD` et `TP2_RESPONSABLE_EMAIL`. Si une valeur manque, le programme journalise l'avertissement et ne contacte pas le serveur SMTP.
- **Commande réellement exécutée dans PowerShell :**

  ```powershell
  Set-Location -LiteralPath 'C:\Users\DELL\Documents\Master\Master_M2I\SEMESTRE 3\Automatisation IA_Agent\TPs\TP2'
  $env:TP2_SMTP_EMAIL=''
  $env:TP2_SMTP_APP_PASSWORD=''
  $env:TP2_RESPONSABLE_EMAIL=''
  & 'C:\Python314\python.exe' '.\tp2.py'
  ```

  Les variables ont été laissées vides uniquement pour ce processus afin d'empêcher un envoi réel.
- **Résultats vérifiés dans le vrai dossier du TP :**
  - `rapport_factures.xlsx` a été produit et relu ; il contient cinq lignes avec les colonnes numéro, fournisseur, date, montant et statut ;
  - F001, F003 et F005 sont dans `Factures/Traitees/` ;
  - F002 et F004 sont dans `Factures/A_controler/` ;
  - F006 et F007 sont restées à la racine, avec les erreurs attendues journalisées ;
  - `log.txt` contient les opérations horodatées et les avertissements indiquant que les notifications ont été ignorées.
- **Vérification finale des tests :** après sécurisation de la configuration email, les neuf tests ont réussi (`Ran 9 tests ... OK`).
- **Configuration locale :** l'utilisateur a configuré les trois variables dans son terminal PowerShell ; leurs valeurs n'ont pas été communiquées dans le chat.
- **Notification F002 :** après autorisation explicite, l'utilisateur rapporte le message `[OK] Notification envoyée pour F002` après l'appel direct à `envoyer_notification("F002", "Tech Solutions", 1500.0)`, sans relancer le robot complet. Cela indique que l'appel SMTP aurait terminé sans exception ; la réception dans la boîte du destinataire n'a pas été vérifiée.
- **Notification F004 :** après une deuxième autorisation explicite, l'utilisateur rapporte aussi `[OK] Notification envoyée pour F004` après l'appel direct à `envoyer_notification("F004", "Fournisseur XYZ", 3200.0)`.
- **Vérification indépendante limitée :** la lecture de `log.txt` dans le dossier TP2 ne montre toujours que le premier lancement sans configuration (avertissements pour F002/F004) et aucune nouvelle ligne `[OK]` pour ces envois. Les messages de succès sont donc rapportés par l'utilisateur, mais ne sont pas corroborés par le journal présent dans le dossier. Ne pas relancer les emails ; vérifier la boîte du destinataire et le terminal d'origine si une confirmation supplémentaire est nécessaire.

## 7. Bilan final

### Terminé et vérifié

- L'énoncé a été lu et comparé au script existant.
- Neuf tests automatisés passent avec Python 3.14.7 : extraction valide, erreurs de lecture et de données, seuil de décision, flux complet temporaire, message email simulé et absence d'envoi si la configuration manque.
- Le robot a aussi été exécuté sur les exemples dans le vrai dossier TP2 : le rapport a été relu, les cinq factures valides classées, les erreurs consignées.
- Le test de notification a contrôlé le destinataire, le sujet et le contenu du message au moyen d'un faux serveur SMTP.
- Le script a été sécurisé pour ne pas contenir de mot de passe et pour ignorer la notification si la configuration email est incomplète.

### Modifications et environnement

- Ajout de `tests/test_tp2.py` et des sept factures d'exemple dans `Factures/` ; cinq sont maintenant classées dans les sous-dossiers.
- Création et mise à jour de `GUIDE_TP.md`.
- `tp2.py` a été modifié pour lire la configuration email localement sans valeur de secours codée en dur. `TP 2.pdf` n'a pas été modifié.
- Installation de `openpyxl` dans l'environnement `C:\Python314\python.exe` après l'erreur de dépendance constatée. Aucun fichier de dépendances du projet n'a été créé ou modifié.
- Création de `rapport_factures.xlsx` et `log.txt` à la racine du dossier TP2.
- Les résultats de test intégrés temporaires ont été supprimés automatiquement.

### Non testé ou non exécuté

- L'utilisateur rapporte que les deux emails réels (F002 et F004) ont affiché un succès SMTP. Les lignes correspondantes ne sont pas présentes dans le `log.txt` du dossier TP2, et la réception effective n'est pas confirmée.
- Les dates sont conservées comme texte et leur validité calendaire n'est pas vérifiée.
- La commande du lanceur intégré n'a pas trouvé les tests ; la découverte standard `unittest` fonctionne.

### Relancer les tests sûrs

Dans PowerShell :

```powershell
Set-Location -LiteralPath 'C:\Users\DELL\Documents\Master\Master_M2I\SEMESTRE 3\Automatisation IA_Agent\TPs\TP2'
& 'C:\Python314\python.exe' -m unittest discover -s tests -v
```

Si une autre installation Python est utilisée, installer les dépendances dans cet environnement avant les tests :

```powershell
& 'C:\Python314\python.exe' -m pip install pandas openpyxl
```

Ne lancer le script sur les factures réelles qu'après avoir sauvegardé le dossier et configuré localement les paramètres email ; ne placer aucun mot de passe ou secret dans le code ou ce guide.
<<<<<<< HEAD

## 7. Générateur automatique multidiscipline & Sauvegarde isolée

Le module [`generateur_factures.py`](file:///c:/Users/DELL/Documents/Master/Master_M2I/SEMESTRE%203/Automatisation%20IA_Agent/TPs/TP2/generateur_factures.py) a été ajouté pour générer dynamiquement des factures selon diverses disciplines de la vie quotidienne et assurer leur archivage sécurisé dans un répertoire isolé.

### Disciplines de vie couvertes

| Discipline | Préfixe | Exemples d'organismes | Types de prestations |
|---|---|---|---|
| **Santé** | `SAN` | Pharmacie Centrale, Clinique Agdal, Labo Ibn Sina | Médicaments, hospitalisation, bilan biologique, IRM |
| **Finance & Assurance** | `FIN` | Attijariwafa Bank, Banque Populaire, RMA, Wafa Assur. | Frais de gestion, assurance multirisque, mutuelle |
| **Énergie & Eau** | `ENG` | ONEE, Lydec, Redal, Amendis, Afriquia Gaz | Électricité basse tension, eau & assainissement, gaz |
| **Télécom & Cloud** | `TEL` | Maroc Telecom, Inwi, Orange, AWS, Microsoft Cloud | Fibre pro, flotte mobile 5G, compute & stockage Cloud |
| **Éducation & Formation** | `EDU` | Univ. Mohammed V, ENSIAS, Udemy Business, Coursera | Inscription séminaire RPA & IA, certifications |
| **Logement & Immobilier** | `LOG` | Syndic Les Jardins, Société Foncière, Schindler | Charges de copropriété, loyer bureau, ascenseurs |
| **Transport & Mobilité** | `TRP` | ONCF Al Boraq, CTM Messagerie, TotalEnergies, Jawaz | Billets grande vitesse, colis express, carburant |
| **Commerce & Fournitures** | `COM` | Librairie Papeterie Nationale, Electroplanet, Marjane | Fournitures de bureau, bureautique, consommables |

### Fonctionnement de la sauvegarde isolée (`Sauvegardes_Factures/`)

1. **Formats supportés (PDF & TXT)** : Le générateur peut produire des factures au format **PDF professionnel** (mise en page A4 avec coordonnées, tableau HT/TVA/TTC, badge de discipline et métadonnées d'extraction) ainsi qu'au format **texte (.txt)**.
2. **Isolation garantie** : Lorsque le robot RPA traite les factures, il déplace les fichiers de `Factures/` vers `Traitees/` et `A_controler/`. La sauvegarde isolée préserve une copie originale intacte.
3. **Horodatage & Manifeste** : Chaque exécution crée un sous-répertoire horodaté `session_YYYYMMDD_HHMMSS/` contenant les fichiers et un `manifest.json` avec la liste complète, montants, disciplines et empreintes SHA-256.
4. **Miroir rapide** : Le sous-dossier `Sauvegardes_Factures/Derniere_Sauvegarde/` pointe en permanence vers la dernière génération.
5. **Restauration en un clic** : Possibilité de recopier instantanément les factures sauvegardées (.pdf et .txt) vers `Factures/` pour rejouer le robot RPA.

### Traitement RPA des fichiers PDF (`tp2.py`)

Le robot RPA [`tp2.py`](file:///c:/Users/DELL/Documents/Master/Master_M2I/SEMESTRE%203/Automatisation%20IA_Agent/TPs/TP2/tp2.py) gère nativement l'extraction des factures **PDF** (via PyMuPDF / `fitz`) :
- Lecture et extraction automatique du Numéro, Fournisseur, Date, Montant MAD et Discipline depuis le flux texte du PDF.
- Prise de décision (seuil 1 000 MAD : `Normal` vs `À contrôler`).
- Inscription dans le rapport Excel `rapport_factures.xlsx`.
- Classement automatique des fichiers `.pdf` vers `Factures/Traitees/` ou `Factures/A_controler/`.

### Commandes utiles

```powershell
# 1. Générer des factures au format PDF (par défaut: PDF + TXT)
python generateur_factures.py --nb 12 --format pdf

# 2. Générer à la fois en PDF et en TXT
python generateur_factures.py --nb 16 --format both

# 3. Cibler des disciplines spécifiques (ex: santé et finance en PDF)
python generateur_factures.py --nb 10 --disciplines sante finance --format pdf

# 4. Lister l'historique des sauvegardes isolées
python generateur_factures.py --lister

# 5. Restaurer les factures sauvegardées dans le dossier Factures/
python generateur_factures.py --restaurer

# 6. Exécuter le robot RPA sur les factures (traite à la fois PDF et TXT)
python tp2.py
```

=======
>>>>>>> d5212afef4491b67020530c0c1999c569d1af755
