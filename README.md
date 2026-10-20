# Automatisation et agents IA — Travaux pratiques

Ce dépôt rassemble progressivement les travaux pratiques et les exercices que je réalise dans le domaine de l'automatisation et de l'intelligence artificielle. L'objectif est de maîtriser les notions étudiées en les mettant en application : expérimenter différentes approches, écrire des programmes, tester les résultats et documenter les étapes ainsi que les concepts appris.

Chaque TP est organisé dans son propre dossier et accompagné, lorsque c'est utile, d'un guide expliquant les objectifs, les notions, les commandes et les résultats obtenus. Le dépôt évoluera au fil des exercices.

## Travaux pratiques

| Dossier | Sujet | Contenu |
|---|---|---|
| [`TP1/`](./TP1/) | Automatisation RPA avec Python | Lecture de données Excel, automatisation d'un formulaire avec Selenium, Playwright et PyAutoGUI, et envoi d'un email de test. |
| [`TP2/`](./TP2/) | Traitement automatisé des factures (RPA) | Pipeline complet en Python : extraction Regex, structuration Pandas, prise de décision par seuil, export Excel, classement automatique, notifications SMTP et journal d'audit. |

---

## TP1 — RPA avec Python

Le dossier [`TP1/`](./TP1/) contient les scripts et le guide du TP d'automatisation d'un formulaire à partir d'Excel avec Selenium, Playwright et PyAutoGUI.

### Installation et exécution rapide (Windows / PowerShell)

Depuis la racine du dépôt :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .\TP1\contacts.example.xlsx .\TP1\contacts.xlsx
python .\TP1\tp1.py
