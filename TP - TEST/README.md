# TP3 : Bot RPA Intelligent de Veille Marché & Emploi
**Master M2I — Semestre 3 : Automatisation IA & Agent**

---

## 🎯 Objectifs Pédagogiques du TP

Ce TP a pour objectif de concevoir et déployer une solution complète de **Robotic Process Automation (RPA)** professionnelle en Python, combinant automatisation web dynamique, pipeline ETL, reporting décisionnel et système d'alerte proactif.

À l'issue de ce TP, vous maîtriserez :
1. **L'Automatisation Web & Scraping Robuste (Web RPA)** :
   - Pilotage d'un navigateur headless via **Playwright** (Chromium).
   - Gestion du DOM, sélecteurs CSS, temps d'attente dynamiques et résilience réseau.
   - Collecte multi-sources hybride (Navigateur + API REST).
2. **Le Traitement de Données & Scoring Métier (ETL Pipeline)** :
   - Nettoyage et standardisation des salaires hétérogènes (regex, conversion $ / €).
   - Détection automatique des compétences technologiques clés (*RPA, AI Agent, LLM, Playwright, Python...*).
   - Algorithme de scoring de compatibilité de profil (0 à 100%).
3. **La Génération de Tableaux de Bord Décisionnels (Spreadsheet Automation)** :
   - Création de classeurs Excel professionnels multi-onglets avec **OpenPyXL**.
   - Design corporate (palette Slate/Navy, cartes KPI, formatage zébré, liens cliquables).
   - Insertion automatique d'un **graphique natif Excel (BarChart)** représentant la demande du marché.
4. **La Gouvernance & Alerting RPA** :
   - Journalisation industrielle horodatée console et fichier (`logs/rpa_execution_YYYYMMDD.log`).
   - Déclenchement d'alertes instantanées selon des règles configurables.
   - Génération d'un digest email exécutif en HTML responsive (`reports/alert_notification.html`).

---

## 🏗️ Architecture du Projet

```text
TP3/
├── config.json                     # Paramétrage déclaratif (mots-clés, seuils, sources)
├── run_bot.py                      # Orchestrateur principal du cycle de vie RPA
├── test_bot.py                     # Tests unitaires et d'intégration automatisés
├── README.md                       # Documentation pédagogique et guide de laboratoire
│
├── bot/                            # Modules RPA spécialisés
│   ├── __init__.py                 # Initialiseur du package
│   ├── config.py                   # Chargement et validation typée des paramètres
│   ├── logger.py                   # Moteur de journalisation d'entreprise (Logs rotatifs)
│   ├── harvester.py                # Moissonneur robotique (Playwright + Requests + Fallback)
│   ├── data_processor.py           # Pipeline ETL, normalisation des salaires & Scoring
│   ├── excel_reporter.py           # Générateur Excel professionnel avec cartes KPI & graphiques
│   └── notifier.py                 # Moteur d'alertes & Digest HTML responsive
│
├── data/
│   ├── raw/                        # Snapshots JSON des extractions brutes
│   └── processed/                  # Jeux de données nettoyés et enrichis (CSV)
│
├── reports/                        # Livrables générés (Rapports .xlsx & Digests .html)
└── logs/                           # Fichiers journaux d'audit et captures d'écran d'erreurs
```

---

## ⚙️ Configuration du Bot (`config.json`)

Toutes les règles métiers sont découplées du code source pour respecter les bonnes pratiques RPA :

```json
{
  "search_settings": {
    "keywords": ["RPA", "AI Agent", "Python Developer", "Automation Engineer", "Data Scientist"],
    "location": "Remote",
    "sources": [ ... ],
    "max_results_per_source": 30
  },
  "alert_rules": {
    "min_salary_usd": 70000,
    "priority_keywords": ["AI Agent", "RPA", "Playwright", "LLM", "Automation"],
    "min_match_score": 70
  },
  "browser_settings": {
    "headless": true,
    "timeout_ms": 15000,
    "slow_mo_ms": 50
  }
}
```

---

## 🚀 Guide d'Exécution

### 1. Vérification des Tests Unitaires
Avant de lancer le robot complet, validez l'intégrité de tous les composants avec :
```bash
python test_bot.py
```

### 2. Exécution du Robot Orchestrateur
Lancez le pipeline complet de bout en bout :
```bash
python run_bot.py
```

### 3. Consultation des Résultats
Après l'exécution :
- **Rapport Excel** : Ouvrez le fichier généré dans `reports/Job_Market_Intelligence_Report_*.xlsx`.
  - Onglet 1 : *Executive Summary* (Cartes KPI & Top Opportunités).
  - Onglet 2 : *All Job Postings* (Tableau filtrable complet avec liens cliquables).
  - Onglet 3 : *Priority Alerts* (Opportunités urgentes respectant vos seuils).
  - Onglet 4 : *Skill Demand Analytics* (Fréquence des compétences & Graphique dynamique).
- **Digest HTML** : Ouvrez `reports/alert_notification.html` dans votre navigateur.
- **Journaux d'audit** : Consultez le fichier `logs/rpa_execution_*.log`.

---

## 🧠 Exercices Pratiques d'Approfondissement (Pour aller plus loin)

1. **Intégration d'un LLM pour le Matching Sémantique** :
   - Remplacer le calcul de score par mots-clés par un appel à un modèle (ex. Gemini ou un modèle local via Ollama) qui compare le texte de l'offre avec votre CV.
2. **Webhooks d'Alerte en Temps Réel** :
   - Dans `bot/notifier.py`, activer l'envoi d'un message JSON via un webhook Discord, Slack ou Microsoft Teams lorsque `is_alert == True`.
3. **Planification Automatique (Scheduler)** :
   - Configurer une tâche planifiée Windows (Task Scheduler) ou un cron job pour exécuter `run_bot.py` tous les matins à 08h00.
