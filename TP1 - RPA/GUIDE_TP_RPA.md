# Guide progressif — TP RPA avec Python

Ce guide évolue avec le TP : après chaque étape terminée et vérifiée, son résultat, les notions utilisées et les commandes utiles sont ajoutés ici.

## Objectif du TP

Le programme lit des contacts dans un classeur Excel, remplit un formulaire et peut envoyer un email personnalisé pour chaque ligne. Le TP demande aussi d'essayer l'automatisation avec Selenium et Playwright. PyAutoGUI est présenté dans les indications comme une autre manière de simuler la saisie.

**État actuel :** Excel, le formulaire local avec Selenium, Playwright et PyAutoGUI, ainsi que l'envoi et la réception d'un email de test ont été vérifiés. Le mot de passe d'application temporaire a été révoqué après l'essai. Le classeur personnel `contacts.xlsx` est local et ignoré par Git. Le dépôt contient un modèle fictif `contacts.example.xlsx`.

## Étape 1 — Préparer le fichier Excel — terminée

Le fichier local `contacts.xlsx` doit se trouver dans le même dossier que `tp1.py`. Pour le créer sans publier de données personnelles, copie le modèle `contacts.example.xlsx` puis remplace ses données localement. Il contient les colonnes que le programme attend :

| Nom | Email | Message |
|---|---|---|
| Alice | alice@example.com | Bonjour Alice, ceci est un message de test. |
| Karim | karim@example.com | Bonjour Karim, ceci est un message de test. |
| Sara | sara@example.com | Bonjour Sara, ceci est un message de test. |

Le modèle `contacts.example.xlsx` utilise des adresses fictives et sert uniquement à tester la lecture et le formulaire. Elles ne peuvent pas recevoir d'emails.

### Préparer l'environnement après avoir cloné le dépôt

Depuis la racine du dépôt, dans PowerShell :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .\TP1\contacts.example.xlsx .\TP1\contacts.xlsx
```

Le dossier `.venv` est l'environnement Python local : il contient les bibliothèques installées et n'est pas partagé sur GitHub. Le classeur copié s'appelle `contacts.xlsx`, nom que les scripts utilisent ; ce fichier local est également ignoré car il peut contenir des données personnelles.

### Notions

- **`.xlsx`** : format de classeur utilisé par Microsoft Excel et d'autres tableurs.
- **Ligne d'en-têtes** : première ligne du tableau, ici `Nom`, `Email`, `Message`. Le programme s'appuie sur ces noms exacts pour retrouver les données.
- **Ligne de données** : une ligne par contact ; le programme traitera chaque ligne.

## Étape 2 — Lire Excel avec pandas — terminée et vérifiée

La fonction `lire_donnees_excel` de `tp1.py` exécute `pd.read_excel(path)`, affiche le résultat et renvoie un DataFrame.

### Notions

- **pandas** : bibliothèque Python pratique pour lire et manipuler des tableaux de données.
- **DataFrame** : tableau pandas composé de lignes et de colonnes.
- **`read_excel`** : lit un classeur Excel et construit un DataFrame. Pour le format `.xlsx`, pandas utilise le moteur `openpyxl`.
- **`head()`** : affiche les premières lignes ; c'est un contrôle rapide que les colonnes et les données ont été lues.

### Résultat observé

La lecture du classeur a renvoyé les colonnes `Nom`, `Email`, `Message` et **3 lignes**. Les trois noms et leurs messages étaient visibles.

### Commande de vérification (PowerShell)

Depuis le dossier du TP, cette commande relit le fichier sans ouvrir le navigateur ni envoyer d'email :

```powershell
python -c "import pandas as pd; df = pd.read_excel(r'TP1\contacts.xlsx'); print(df.head()); print('Lignes:', len(df)); print('Colonnes:', list(df.columns))"
```

## Étape 3 — Remplir le formulaire avec Selenium — terminée et testée localement

Comme l'énoncé ne fournit pas d'URL de formulaire, un formulaire de démonstration a été créé dans `formulaire_test.html`. Selenium ouvre ce fichier local, saisit chaque contact et clique sur le bouton de validation. Le formulaire affiche une confirmation dans le navigateur et n'envoie aucune donnée à un serveur.

Dans `tp1.py`, `FORM_URL` est construit à partir de l'emplacement du fichier HTML. Les champs sont trouvés par leurs attributs HTML `name` : `nom`, `email` et `message`. Le bouton est trouvé par son attribut `id`, `submit`.

### Notions

- **RPA** (*Robotic Process Automation*) : automatisation par logiciel de tâches répétitives, comme recopier des données d'un tableau vers un formulaire.
- **Selenium** : outil qui pilote un navigateur et permet de cibler les éléments d'une page web.
- **DOM** (*Document Object Model*) : représentation structurée du contenu HTML d'une page. Cibler un élément du DOM est généralement plus précis que cliquer à des coordonnées d'écran.
- **Sélecteur** : règle pour retrouver un élément. `By.NAME, "nom"` cherche un élément dont l'attribut HTML est `name="nom"` ; `By.ID, "submit"` cherche `id="submit"`.
- **WebDriver** : objet Selenium qui commande le navigateur. `webdriver.Chrome()` démarre une session Chrome.
- **`WebDriverWait`** : attend qu'une condition devienne vraie, ici que le message de confirmation soit visible. C'est plus fiable qu'une pause de durée fixe pour vérifier une action.
- **Soumission** : action qui valide un formulaire. Une première tentative avec la touche Entrée dans la zone de message n'a pas validé le formulaire ; le test a montré qu'il fallait cliquer sur le vrai bouton.

### Sécurité du test

`RPA_ENVOYER_EMAILS` vaut `false` par défaut, donc les tests n'envoient pas de courriels. Le script ne permet l'envoi que si cette variable vaut explicitement `true`. Ne l'active pas avant d'avoir remplacé les adresses d'exemple par des destinataires autorisés et configuré les identifiants SMTP localement.

### Commande de test (PowerShell)

Depuis le dossier du TP :

```powershell
python .\TP1\tp1.py
```

Cette commande a été exécutée avec succès : le programme a lu les 3 contacts, a rempli et validé le formulaire local pour chacun, et a terminé sans envoyer d'emails. Les dépendances utilisées dans l'environnement du projet sont `pandas`, `openpyxl` et `selenium`.

## Étape 4 — Email automatique — envoi test exécuté

La fonction `envoyer_email` construit un message personnalisé avec `MIMEMultipart` et `MIMEText`, puis se connecte au serveur SMTP avec `SMTP_SSL` sur le port 465. Le test réel a été exécuté avec une seule ligne et la console a affiché `[OK] Email envoyé` puis `[TERMINÉ]`. Cela confirme que le serveur SMTP a accepté l'envoi ; vérifie aussi la boîte de réception et le dossier spam du destinataire pour confirmer sa réception.

### Notions et protections

- **SMTP** (*Simple Mail Transfer Protocol*) : protocole qui permet à un programme de remettre un email à un serveur de messagerie.
- **SSL/TLS** : chiffrement de la connexion au serveur SMTP. `SMTP_SSL("smtp.gmail.com", 465)` établit ici une connexion chiffrée dès le départ.
- **MIME** : format qui structure un email avec un expéditeur, un destinataire, un objet et un corps lisible.
- **Mot de passe d'application** : identifiant spécifique que Google peut fournir pour certaines applications lorsque la validation en deux étapes est activée. Ne le mets pas dans le code, dans le classeur, dans le guide ou dans un message de chat.
- **Variables d'environnement** : paramètres locaux lus par le programme sans inscrire les valeurs secrètes dans le fichier Python. Le script lit `RPA_SMTP_EMAIL` et `RPA_SMTP_APP_PASSWORD`.
- **Barrières d'envoi** : l'envoi reste désactivé par défaut ; si activé sans identifiants, le script s'arrête explicitement. Il refuse aussi de démarrer si le classeur contient encore des adresses réservées aux exemples (`example.com`, `example.org`, `example.net`).

**Sécurité :** le mot de passe d'application utilisé pour l'essai a été exposé dans le texte d'une invite PowerShell. Il a ensuite été révoqué ; la page Google a confirmé qu'aucun mot de passe d'application n'était actif. Les variables d'environnement de la session ont aussi été supprimées. Ne réutilise jamais cet ancien mot de passe.

### Préparation locale d'un email de test

Pour un prochain test, après avoir révoqué l'ancien mot de passe d'application, crée-en un nouveau et garde-le secret. Avant d'activer l'envoi :

1. Dans `contacts.xlsx`, garde **une seule ligne de contact**, avec ta propre adresse de test (ou celle d'une personne qui t'a autorisé à la recevoir). Le script envoie un email à chaque ligne.
2. Pour Gmail, utilise un mot de passe d'application créé depuis ton compte avec la validation en deux étapes activée. N'utilise pas ton mot de passe Gmail habituel.
3. Dans une fenêtre PowerShell locale, depuis le dossier du TP, saisis ces commandes. La saisie du mot de passe d'application est masquée. Ne mets jamais le secret à l'intérieur des guillemets de la commande `Read-Host` : ceux-ci ne sont que le texte d'invite affiché.

```powershell
$env:RPA_SMTP_EMAIL = Read-Host "Adresse Gmail expéditrice"
$secure = Read-Host "Mot de passe d'application Gmail (saisie masquée)" -AsSecureString
$env:RPA_SMTP_APP_PASSWORD = ([System.Net.NetworkCredential]::new("", $secure).Password -replace '\s','')
$env:RPA_ENVOYER_EMAILS = "true"
python .\TP1\tp1.py
```

Ne tape jamais le mot de passe à l'intérieur des guillemets du `Read-Host` : saisis-le seulement à l'invite masquée. Le classeur doit contenir un seul destinataire autorisé. La dernière commande envoie un vrai email.

Cette commande envoie réellement un email : ne l'exécute que lorsque le classeur ne contient que le destinataire contrôlé et que Gmail est correctement configuré. Les variables d'environnement ne sont disponibles que dans cette fenêtre PowerShell. Après le test, ferme cette fenêtre pour supprimer ces variables de son environnement.

### Résultats des vérifications de protection et d'envoi

Le programme a été lancé avec `RPA_ENVOYER_EMAILS=true`, des valeurs SMTP temporaires de test et le classeur contenant encore `example.com`. Il s'est arrêté avec l'erreur attendue en listant les adresses d'exemple, avant le démarrage du navigateur et sans connexion au serveur SMTP. Le test normal suivant a aussi confirmé que Selenium fonctionne toujours lorsque l'envoi est désactivé.

Lors du test réel suivant, le classeur n'avait plus qu'un contact et le programme a affiché `[OK] Email envoyé` et `[TERMINÉ]`. Le mot de passe d'application ayant été exposé dans le texte de l'invite PowerShell, il doit être révoqué même si l'envoi a réussi.

Après l'envoi, les variables d'environnement `RPA_SMTP_EMAIL`, `RPA_SMTP_APP_PASSWORD` et `RPA_ENVOYER_EMAILS` ont été supprimées de la session PowerShell avec `Remove-Item Env:...`. Cette suppression locale ne révoque pas le mot de passe d'application chez Google.

Le destinataire a confirmé que l'email est arrivé. La vérification de réception est donc terminée. Le mot de passe d'application utilisé pour cet essai a ensuite été révoqué : la page Google affichait qu'aucun mot de passe d'application n'était actif.

### Révoquer le mot de passe d'application exposé

1. Ouvre [la page officielle des mots de passe d'application Google](https://myaccount.google.com/apppasswords) en étant connecté au compte expéditeur.
2. Si Google le demande, reconnecte-toi au compte.
3. Repère le mot de passe créé pour le TP (le nom affiché peut être celui que tu avais choisi).
4. Choisis **Supprimer** / l'icône de corbeille pour cette entrée, puis confirme la révocation.
5. N'utilise plus ce mot de passe. Comme les variables PowerShell ont aussi été supprimées, l'application ne pourra plus le relire de cette session. Si un nouveau test est nécessaire plus tard, crée un nouveau mot de passe et saisis-le de manière masquée, sans jamais l'inscrire dans le texte d'une commande.

## Étape 5 — Comparer les outils — en cours

- **Playwright** : version locale terminée et testée dans `tp_playwright.py`. Elle lit le même Excel, ouvre le même formulaire local, saisit les trois contacts et vérifie le message de confirmation. Aucun email n'est envoyé.
- **PyAutoGUI** : version créée dans `tp_pyautogui.py`, lancée et confirmée visuellement par l'utilisateur. Le navigateur affichait le dernier contact (Sara) et le message de confirmation.
- **Validation finale** : vérifier les résultats de chaque outil et distinguer clairement le test local de l'envoi réel d'emails.

### Notions Playwright

- **Playwright** : bibliothèque d'automatisation de navigateur, comme Selenium, mais avec sa propre API.
- **Browser** : le processus du navigateur démarré par Playwright. Ici, `playwright.chromium.launch(channel="chrome")` utilise Chrome installé sur l'ordinateur.
- **Page** : un onglet du navigateur piloté par Playwright.
- **Locator** : recherche d'un élément sur la page. `[name="nom"]` est un sélecteur CSS qui retrouve le champ dont l'attribut `name` vaut `nom` ; `#submit` retrouve l'élément dont l'`id` vaut `submit`.
- **`fill()`** : remplace le contenu d'un champ par la valeur donnée.
- **Mode headless** : navigateur exécuté sans fenêtre visible. Le script vérifie tout de même la confirmation avant de continuer.
- **`wait_for(state="visible")`** : attend que le message de confirmation soit visible ; si la validation ne se produit pas, Playwright signale une erreur plutôt que de déclarer le test réussi.

### Notions PyAutoGUI

- **PyAutoGUI** : bibliothèque qui envoie des actions de clavier et de souris au bureau, comme le ferait une personne.
- **Focus / premier plan** : fenêtre qui reçoit actuellement les frappes du clavier. Contrairement à Selenium et Playwright, PyAutoGUI ne cible pas les champs par leur nom HTML : il dépend de la fenêtre active et de l'ordre de navigation.
- **`hotkey("ctrl", "l")`** : raccourci du navigateur pour sélectionner la barre d'adresse. Le script y saisit l'URL locale avant de commencer.
- **`press("tab")`** : déplace le focus vers le contrôle suivant. Sur notre page de test, les champs et le bouton sont placés dans l'ordre Nom → Email → Message → Valider.
- **`write(...)`** : simule la frappe du texte caractère par caractère.
- **`FAILSAFE`** : sécurité PyAutoGUI ; déplacer la souris dans un coin de l'écran interrompt l'automatisation.
- **Limite importante** : les frappes peuvent être envoyées à une mauvaise fenêtre si le navigateur n'est pas celui qui vient d'être ouvert ou s'il perd le focus. C'est pourquoi cette variante est plus sensible à l'état du bureau, et la confirmation doit être regardée à l'écran.

### Commande de test PyAutoGUI (PowerShell)

Depuis le dossier du TP :

```powershell
python .\TP1\tp_pyautogui.py
```

Le script utilise uniquement le formulaire local, ne contient aucune étape d'envoi d'email et demande de vérifier la confirmation dans le navigateur. La commande est sortie avec le code `0`, puis l'utilisateur a confirmé avoir vu le dernier contact et la confirmation. `pyautogui` a été ajouté à l'environnement virtuel du projet.

### Commande de test Playwright (PowerShell)

Depuis le dossier du TP :

```powershell
python .\TP1\tp_playwright.py
```

La commande a réussi : les trois lignes ont été traitées et chacune a affiché la confirmation du formulaire local. La bibliothèque `playwright` a été ajoutée à l'environnement Python du projet. La version de Selenium reste disponible dans `tp1.py`.

## Journal des étapes

| Étape | État | Résultat |
|---|---|---|
| 1. Préparer Excel | Terminée | Le classeur local contient les colonnes attendues. Le dépôt publie uniquement `contacts.example.xlsx`, un modèle à données fictives ; le classeur personnel `contacts.xlsx` est exclu par `.gitignore`. |
| 2. Lire Excel | Terminée | pandas a lu les trois lignes et les en-têtes attendus. |
| 3. Automatiser le formulaire | Terminée | Selenium a validé les trois entrées sur la page locale ; aucune donnée n'a été envoyée sur Internet. |
| 4. Envoyer des emails | Terminée pour un test | Le script a affiché `[OK] Email envoyé`, le destinataire a confirmé la réception, les variables locales ont été supprimées et la page Google confirme qu'aucun mot de passe d'application n'est encore actif. |
| 5. Tester les variantes et valider | Variantes locales terminées | Selenium, Playwright et PyAutoGUI ont tous rempli le formulaire local ; la confirmation PyAutoGUI a été vérifiée visuellement. |
