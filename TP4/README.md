# TP 4 — Web Scraping and ETL Automation
**Filière :** Masters IADS – M2I, S3  
**Module :** Automation & Agentic AI  
**Encadrante :** Prof. Imane Lahbari  

---

## 🎯 Objectif
Développer un pipeline automatisé en Python permettant :
1. **E (Extract)** : Extraire les informations de livres depuis [Books to Scrape](http://books.toscrape.com/).
2. **T (Transform)** : Nettoyer et transformer les données avec **Pandas**.
3. **L (Load)** : Exporter les données nettoyées sous formats **CSV** et **Excel (.xlsx)** et vérifier la cohérence.
4. **Automatisation** : Exécution robuste de bout en bout sans intervention manuelle.

---

## 📂 Fichiers du projet
- [`etl_books.py`](file:///c:/Users/DELL/Documents/Master/Master_M2I/SEMESTRE%203/Automatisation%20IA_Agent/TPs/TP4/etl_books.py) : Script principal contenant l'ensemble du pipeline ETL.
- [`livres.csv`](file:///c:/Users/DELL/Documents/Master/Master_M2I/SEMESTRE%203/Automatisation%20IA_Agent/TPs/TP4/livres.csv) : Fichier de sortie CSV.
- [`livres.xlsx`](file:///c:/Users/DELL/Documents/Master/Master_M2I/SEMESTRE%203/Automatisation%20IA_Agent/TPs/TP4/livres.xlsx) : Fichier de sortie Excel.
- [`TP ETL& Web Scraping.pdf`](file:///c:/Users/DELL/Documents/Master/Master_M2I/SEMESTRE%203/Automatisation%20IA_Agent/TPs/TP4/TP%20ETL&%20Web%20Scraping.pdf) : Énoncé officiel du TP.

---

## 🚀 Exécution

Pour lancer le pipeline complet :
```bash
python etl_books.py
```

### Options de pagination
Par défaut, le script extrait la première page (20 livres). Si vous souhaitez scraper plusieurs pages ou l'ensemble du catalogue (50 pages / 1000 livres) :
```python
# Dans etl_books.py :
run_etl_pipeline(max_pages=5)   # Pour 5 pages (100 livres)
run_etl_pipeline(max_pages=None) # Pour tout le site (1000 livres)
```

---

## 🔍 Correspondance avec les questions du TP

### Partie 1 — Extraction des données
- Utilisation de `requests.Session()` avec timeout et vérification des codes HTTP (`raise_for_status()`).
- Parsing HTML via `BeautifulSoup`.
- Extraction des 4 champs :
  - **Titre** : extrait depuis l'attribut `title` de `<h3> <a title="...">`.
  - **Prix** : extrait depuis la classe `.price_color`.
  - **Disponibilité** : extrait depuis la classe `.instock.availability`.
  - **Note** : extrait depuis la classe CSS de `.star-rating` (One, Two, Three, Four, Five).

### Partie 2 — Nettoyage et transformation (Pandas)
- Chargement dans un `DataFrame`.
- Suppression des doublons via `drop_duplicates()`.
- Suppression des lignes avec titre ou prix manquant via `dropna(subset=['titre', 'prix'])`.
- Nettoyage du prix par expression régulière `r"(\d+(\.\d+)?)"` et conversion en `float`.
- Mapping de la note textuelle en valeur numérique (sur 5).
- Réorganisation des colonnes : `["titre", "prix", "note_sur_5", "disponibilite"]`.

### Partie 3 — Exportation des résultats
- Export CSV via `to_csv('livres.csv', index=False, encoding='utf-8-sig')`.
- Export Excel via `to_excel('livres.xlsx', index=False, engine='openpyxl')`.
- Validation automatique de cohérence entre le CSV et le fichier Excel (`df_csv.equals(df_xlsx)`).

### Partie 4 — Automatisation du processus
- Regroupement des étapes dans une fonction unifiée `run_etl_pipeline()`.
- Gestion des erreurs réseau et exceptions (`try / except`).
- Affichage des métriques :
  - Nombre de livres extraits.
  - Nombre de livres conservés après nettoyage.
- Exécution autonome sans intervention manuelle.
