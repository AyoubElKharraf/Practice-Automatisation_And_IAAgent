# Automatisation et agents IA — Travaux pratiques

Ce dépôt rassemble progressivement les travaux pratiques et les exercices que je réalise dans le domaine de l'automatisation et de l'intelligence artificielle. L'objectif est de maîtriser les notions étudiées en les mettant en application : expérimenter différentes approches, écrire des programmes, tester les résultats et documenter les étapes ainsi que les concepts appris.

Chaque TP est organisé dans son propre dossier et accompagné, lorsque c'est utile, d'un guide expliquant les objectifs, les notions, les commandes et les résultats obtenus. Le dépôt évoluera au fil des exercices.

## Travaux pratiques

| Dossier | Sujet | Contenu |
|---|---|---|
| [`TP1 - RPA/`](./TP1%20-%20RPA/) | Automatisation RPA avec Python | Lecture de données Excel, automatisation d'un formulaire avec Selenium, Playwright et PyAutoGUI, et envoi d'un email de test. |
| [`TP2 - RPA/`](./TP2%20-%20RPA/) | Traitement automatisé des factures (RPA) | Pipeline complet en Python : extraction Regex, structuration Pandas, prise de décision par seuil, export Excel, classement automatique, notifications SMTP et journal d'audit. |
| [`TP3 - Automatisation Python - API/`](./TP3%20-%20Automatisation%20Python%20-%20API/) | Automatisation par scripts Python et API | Scripts d'automatisation en Python et communication avec une API (requêtes HTTP avec `requests`, réponses JSON, gestion des erreurs). |
| [`TP4 - Web Scraping/`](./TP4%20-%20Web%20Scraping/) | Web Scraping et automatisation ETL | Extraction de données de livres avec Requests et BeautifulSoup, nettoyage avec Pandas, export en CSV et Excel dans un seul script ETL. |
| [`TP5 - LLM/`](./TP5%20-%20LLM/) | Découverte pratique d'un LLM et analyse d'attention | Tokenisation BPE, embeddings & similarité cosinus, génération autorégressive (logits/Softmax/top-k/top-p) et visualisation des poids d'attention multi-têtes (GPT-2). |
| [`TP_TEST/`](./TP_TEST/) | Bot RPA intelligent de veille marché et emploi | Bot de veille automatisé sur le marché et l'emploi, qui réunit les techniques des TP précédents. |

## Structure du dépôt

```text
.
├── TP1 - RPA/
├── TP2 - RPA/
├── TP3 - Automatisation Python - API/
├── TP4 - Web Scraping/
├── TP5 - LLM/
├── TP_TEST/
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Installation (commune à tous les TP)

Les dépendances de tous les TP sont listées dans [`requirements.txt`](./requirements.txt).

### Windows / PowerShell

Depuis la racine du dépôt :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Pour Playwright (TP1), installer aussi les navigateurs :

```powershell
python -m playwright install
```

---

## TP1 — RPA avec Python

Le dossier [`TP1 - RPA/`](./TP1%20-%20RPA/) contient les scripts et le guide du TP d'automatisation d'un formulaire à partir d'Excel avec Selenium, Playwright et PyAutoGUI.

### Exécution rapide

Depuis la racine du dépôt, avec l'environnement virtuel activé :

```powershell
Copy-Item ".\TP1 - RPA\contacts.example.xlsx" ".\TP1 - RPA\contacts.xlsx"
python ".\TP1 - RPA\tp1.py"
```

> Les chemins sont entre guillemets car les noms de dossiers contiennent des espaces.

---

## TP5 — LLM et analyse d'attention

Le dossier [`TP5 - LLM/`](./TP5%20-%20LLM/) contient le script et l'analyse complète de découverte pratique d'un LLM (GPT-2) : tokenisation BPE, embeddings statiques/contextuels, similarités cosinus, génération autorégressive et visualisation des poids d'attention multi-têtes.

### Exécution rapide

Depuis la racine du dépôt, avec l'environnement virtuel activé :

```powershell
python ".\TP5 - LLM\tp5_llm.py"
```

---

## Sécurité

Les identifiants (mot de passe d'application Gmail, clés d'API) ne doivent **jamais** être écrits dans le code ni poussés sur GitHub. Ils se placent dans un fichier `.env` local, déjà exclu du dépôt par le `.gitignore`.
