"""
Générateur automatique de factures multidiscipline & Système de sauvegarde isolée.
Spécialement conçu pour le TP RPA - Automatisation du traitement des factures.

Disciplines couvertes :
    - Santé (Pharmacie, Clinique, Analyses, Radiologie, Soins dentaires)
    - Finance & Assurance (Banque, Assurance multirisque, Mutuelle, Prêt)
    - Énergie & Eau (ONEE Électricité, Lydec, Redal, Amendis, Gaz)
    - Télécom & Tech (Maroc Telecom, Inwi, Orange, AWS, Microsoft 365, Cloud)
    - Éducation & Formation (Université, École d'ingénieurs, E-learning, Certifications)
    - Logement & Immobilier (Syndic de copropriété, Loyer professionnel, Maintenance)
    - Transport & Mobilité (ONCF Al Boraq, CTM Messagerie, Carburant, Télépéage Jawaz)
    - Commerce & Fournitures (Fournitures de bureau, Électronique, Consommables)

Fonctionnalités :
    1. Génération de factures au format PDF professionnel et/ou format texte .txt
    2. Sauvegarde automatique dans un répertoire isolé (ex: Sauvegardes_Factures/)
       avec sous-dossier horodaté et miroir 'Derniere_Sauvegarde'
    3. Production d'un manifeste récapitulatif (manifest.json) pour audit et traçabilité
    4. Restauration / Réutilisation des factures sauvegardées à tout moment
    5. Contrôle d'intégrité par empreinte SHA256
"""

import argparse
import hashlib
import json
import os
import random
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ----------------------------------------------------------------------
# CATALOGUE DE DONNÉES PAR DISCIPLINE DE VIE
# ----------------------------------------------------------------------
CATALOGUE_DISCIPLINES = {
    "sante": {
        "nom_affiche": "Santé",
        "prefixe": "SAN",
        "couleur_rgb": (0.08, 0.48, 0.42),
        "fournisseurs": [
            "Pharmacie Centrale de Rabat",
            "Clinique Internationale Agdal",
            "Laboratoire d'Analyses Ibn Sina",
            "Centre de Radiologie & Imagerie Al Azhar",
            "Cabinet Dentaire Dr. Amrani",
            "Cabinet d'Ophtalmologie Vision Plus",
            "Polyclinique Médicale de Fès",
            "Pharmacie Al Manar Tanger",
        ],
        "prestations": [
            "Achat médicaments et dispositifs médicaux",
            "Hospitalisation et soins ambulatoires",
            "Bilan sanguin complet et sérologie",
            "Imagerie par résonance magnétique (IRM)",
            "Soins dentaires et détartrage spécialisé",
            "Examen ophtalmologique et correction visuelle",
            "Consultation cardiologie et échographie",
        ],
        "fourchettes_prix": {
            "normal": (120.0, 950.0),       # <= 1000 MAD
            "a_controler": (1200.0, 4800.0) # > 1000 MAD
        }
    },
    "finance": {
        "nom_affiche": "Finance & Assurance",
        "prefixe": "FIN",
        "couleur_rgb": (0.12, 0.24, 0.45),
        "fournisseurs": [
            "Attijariwafa Bank - Centre Entreprises",
            "Banque Populaire Régionale",
            "RMA Royale Marocaine d'Assurance",
            "Wafa Assurance Entreprise",
            "Sanlam Maroc Assurances",
            "Bank of Africa (BMCE)",
            "CIH Bank Services Pro",
        ],
        "prestations": [
            "Frais de gestion de compte et tenue de dossier",
            "Prime annuelle assurance responsabilité civile pro",
            "Cotisation mutuelle santé complémentaire groupe",
            "Commission sur virement bancaire international",
            "Échéance mensualité leasing matériel informatique",
            "Assurance multirisque locaux professionnels",
        ],
        "fourchettes_prix": {
            "normal": (250.0, 980.0),
            "a_controler": (1500.0, 8500.0)
        }
    },
    "energie": {
        "nom_affiche": "Énergie & Eau",
        "prefixe": "ENG",
        "couleur_rgb": (0.80, 0.40, 0.08),
        "fournisseurs": [
            "ONEE - Branche Électricité",
            "Lydec - Service Eau et Énergie Casablanca",
            "Redal - Distribution Rabat Salé Témara",
            "Amendis Tanger Tétouan",
            "Afriquia Gaz Distribution",
            "TotalEnergies Gaz Industriel",
        ],
        "prestations": [
            "Consommation électrique basse tension - Mensuel",
            "Distribution eau potable et assainissement liquide",
            "Livraison gaz propane / butane pour chauffage",
            "Maintenance préventive compteur moyenne tension",
            "Raccordement et abonnement réseau énergétique",
        ],
        "fourchettes_prix": {
            "normal": (180.0, 890.0),
            "a_controler": (1300.0, 5200.0)
        }
    },
    "telecom": {
        "nom_affiche": "Télécom & Cloud",
        "prefixe": "TEL",
        "couleur_rgb": (0.22, 0.28, 0.68),
        "fournisseurs": [
            "Maroc Telecom (IAM) - Fibre Pro",
            "Inwi Entreprises B2B",
            "Orange Maroc Télécommunications",
            "Amazon Web Services (AWS) EMEA",
            "Microsoft Cloud Maroc",
            "OVHcloud Hébergement Dédié",
        ],
        "prestations": [
            "Abonnement Fibre Optique Dédiée 500 Mbps",
            "Flotte mobile forfaits illimités 5G",
            "Consommation cloud calcul EC2 et stockage S3",
            "Licences SaaS Microsoft 365 Business Standard",
            "Hébergement serveurs et certificat SSL annuel",
            "Solution téléphonie VoIP IPBX mensuel",
        ],
        "fourchettes_prix": {
            "normal": (199.0, 950.0),
            "a_controler": (1400.0, 6800.0)
        }
    },
    "education": {
        "nom_affiche": "Éducation & Formation",
        "prefixe": "EDU",
        "couleur_rgb": (0.14, 0.38, 0.72),
        "fournisseurs": [
            "Université Mohammed V - Formation Continue",
            "École Nationale Supérieure d'Informatique (ENSIAS)",
            "Institut Marocain des Hautes Études",
            "Udemy Business Enterprise",
            "Coursera Campus Global",
            "Centre International de Langues & Certifications",
        ],
        "prestations": [
            "Frais d'inscription séminaire Agentic AI & RPA",
            "Certification professionnelle Cloud & DevOps",
            "Programme exécutif Data Science & IA appliquée",
            "Abonnement annuel plateforme d'apprentissage e-learning",
            "Documentation académique et manuels spécialisés",
            "Atelier pratique automatisation des processus",
        ],
        "fourchettes_prix": {
            "normal": (350.0, 900.0),
            "a_controler": (1800.0, 7500.0)
        }
    },
    "logement": {
        "nom_affiche": "Logement & Immobilier",
        "prefixe": "LOG",
        "couleur_rgb": (0.28, 0.32, 0.40),
        "fournisseurs": [
            "Syndic Résidence Les Jardins d'Agdal",
            "Société Foncière & Immobilière Marocaine",
            "Atlas Sécurité & Gardiennage SARL",
            "Schindler Ascenseurs Maroc",
            "Services Nettoyage & Entretien Pro",
        ],
        "prestations": [
            "Cotisation mensuelle syndic et conciergerie",
            "Loyer mensuel bureaux professionnels",
            "Contrat de gardiennage et télésurveillance",
            "Maintenance préventive ascenseur et sécurité incendie",
            "Travaux de plomberie et réfection des locaux",
        ],
        "fourchettes_prix": {
            "normal": (300.0, 900.0),
            "a_controler": (1600.0, 9000.0)
        }
    },
    "transport": {
        "nom_affiche": "Transport & Logistique",
        "prefixe": "TRP",
        "couleur_rgb": (0.72, 0.18, 0.18),
        "fournisseurs": [
            "ONCF - Ligne Grande Vitesse Al Boraq",
            "CTM - Messagerie Express et Colis",
            "TotalEnergies Marketing Maroc",
            "Afriquia Stations de Carburant",
            "Autoroutes du Maroc (ADM) - Télépéage Jawaz",
            "Aramex Maroc Logistique",
        ],
        "prestations": [
            "Billets de déplacement professionnel Al Boraq",
            "Expédition de plis et fret express sécurisé",
            "Carte carburant flotte véhicules de société",
            "Recharge compte télépéage autoroutier Jawaz",
            "Transport logistique matériel et livraison sur site",
        ],
        "fourchettes_prix": {
            "normal": (150.0, 850.0),
            "a_controler": (1100.0, 3900.0)
        }
    },
    "commerce": {
        "nom_affiche": "Commerce & Fournitures",
        "prefixe": "COM",
        "couleur_rgb": (0.20, 0.46, 0.28),
        "fournisseurs": [
            "Librairie Papeterie Nationale de Rabat",
            "Marjane Achats Entreprises",
            "Electroplanet Équipement Bureautique",
            "Office Dépôt Maroc",
            "Carrefour Market Professionnel",
        ],
        "prestations": [
            "Fournitures de bureau, papier et consommables",
            "Matériel informatique périphérique (claviers, écrans)",
            "Approvisionnement espace réfectoire et pause-café",
            "Cartouches et toners pour imprimantes multifonctions",
            "Mobilier ergonomique et accessoires de bureau",
        ],
        "fourchettes_prix": {
            "normal": (120.0, 880.0),
            "a_controler": (1250.0, 4200.0)
        }
    },
}

# ----------------------------------------------------------------------
# DOSSIERS PAR DÉFAUT
# ----------------------------------------------------------------------
DOSSIER_DESTINATION_DEFAUT = "Factures"
DOSSIER_SAUVEGARDE_DEFAUT = "Sauvegardes_Factures"


def calculer_sha256(chemin_fichier: Path) -> str:
    """Calcule l'empreinte SHA-256 d'un fichier."""
    h = hashlib.sha256()
    with open(chemin_fichier, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generer_facture_donnees(
    index: int,
    cle_discipline: str,
    forcer_statut: Optional[str] = None,
    date_fixe: Optional[str] = None,
) -> Dict:
    """
    Génère les métadonnées d'une facture pour une discipline donnée.
    """
    discipline = CATALOGUE_DISCIPLINES[cle_discipline]
    prefixe = discipline["prefixe"]
    numero = f"{prefixe}-2026-{index:04d}"

    fournisseur = random.choice(discipline["fournisseurs"])
    prestation = random.choice(discipline["prestations"])

    # Détermination du statut de montant : Normal (<= 1000 MAD) ou À contrôler (> 1000 MAD)
    if forcer_statut:
        statut_cible = forcer_statut
    else:
        # Répartition équilibrée
        statut_cible = "a_controler" if random.random() < 0.45 else "normal"

    min_p, max_p = discipline["fourchettes_prix"][statut_cible]
    montant_valeur = round(random.uniform(min_p, max_p), 2)

    if date_fixe:
        date_str = date_fixe
    else:
        # Date sur les 45 derniers jours
        jour_offset = random.randint(1, 45)
        date_obj = datetime.now() - timedelta(days=jour_offset)
        date_str = date_obj.strftime("%d/%m/%Y")

    return {
        "numero": numero,
        "fournisseur": fournisseur,
        "date": date_str,
        "montant": montant_valeur,
        "discipline_cle": cle_discipline,
        "discipline_nom": discipline["nom_affiche"],
        "prestation": prestation,
        "statut_attendu": "Normal" if montant_valeur <= 1000.0 else "À contrôler",
    }


def formater_contenu_facture(donnees: Dict) -> str:
    """
    Formate le contenu texte d'une facture.
    Le format est 100% compatible avec l'extracteur du TP2 :
        Numero: ...
        Fournisseur: ...
        Date: ...
        Montant: ... MAD
    Avec enrichissement (Discipline et Prestation).
    """
    contenu = [
        f"Numero: {donnees['numero']}",
        f"Fournisseur: {donnees['fournisseur']}",
        f"Date: {donnees['date']}",
        f"Montant: {donnees['montant']:.2f} MAD",
        f"Discipline: {donnees['discipline_nom']}",
        f"Prestation: {donnees['prestation']}",
    ]
    return "\n".join(contenu) + "\n"


def generer_facture_pdf(donnees: Dict, chemin_pdf: Path) -> Path:
    """
    Génère une facture sous forme de document PDF élégant et professionnel avec PyMuPDF.
    Intègre les coordonnées du fournisseur, le tableau de prestation HT/TVA/TTC en MAD,
    ainsi que le bloc de métadonnées standardisées pour extraction RPA infaillible.
    """
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # Format A4 standard

    cle = donnees.get("discipline_cle", "sante")
    couleur_primaire = CATALOGUE_DISCIPLINES.get(cle, {}).get("couleur_rgb", (0.12, 0.24, 0.45))
    couleur_fond_clair = (0.95, 0.96, 0.98)

    # 1. Bannière d'en-tête supérieure
    page.draw_rect(fitz.Rect(0, 0, 595, 75), color=couleur_primaire, fill=couleur_primaire)
    page.insert_text((40, 46), "FACTURE COMMERCIALE", fontname="helv", fontsize=20, color=(1, 1, 1))
    nom_disc = donnees.get("discipline_nom", "GÉNÉRAL").upper()
    page.insert_text((400, 46), nom_disc, fontname="helv", fontsize=12, color=(0.92, 0.92, 0.92))

    # 2. Bloc Émetteur / Fournisseur (gauche)
    y_top = 105
    page.insert_text((40, y_top), donnees["fournisseur"], fontname="helv", fontsize=13, color=couleur_primaire)
    page.insert_text((40, y_top + 18), f"Discipline: {donnees['discipline_nom']}", fontname="helv", fontsize=10, color=(0.3, 0.3, 0.3))
    page.insert_text((40, y_top + 32), "Adresse: Boulevard Hassan II, Maroc", fontname="helv", fontsize=9, color=(0.4, 0.4, 0.4))
    page.insert_text((40, y_top + 45), "I.C.E. : 002145893000084 | R.C. : 48921", fontname="helv", fontsize=9, color=(0.4, 0.4, 0.4))

    # 3. Bloc Référence Facture (droite)
    page.draw_rect(fitz.Rect(350, 92, 555, 172), color=couleur_fond_clair, fill=couleur_fond_clair)
    page.draw_rect(fitz.Rect(350, 92, 555, 172), color=(0.85, 0.88, 0.92), width=1)
    page.insert_text((365, 112), f"Numero: {donnees['numero']}", fontname="helv", fontsize=11, color=(0.1, 0.1, 0.1))
    page.insert_text((365, 130), f"Date: {donnees['date']}", fontname="helv", fontsize=10, color=(0.2, 0.2, 0.2))
    page.insert_text((365, 148), "Devise: MAD (Dirham)", fontname="helv", fontsize=9, color=(0.3, 0.3, 0.3))
    statut_libelle = "À contrôler" if donnees["montant"] > 1000 else "Normal"
    page.insert_text((365, 164), f"Statut: {statut_libelle}", fontname="helv", fontsize=9, color=couleur_primaire)

    # 4. Bloc Destinataire / Client
    page.draw_rect(fitz.Rect(40, 185, 555, 235), color=couleur_fond_clair, fill=couleur_fond_clair)
    page.insert_text((55, 203), "Facturé à : Master M2I - Service Automatisation & IA Agent", fontname="helv", fontsize=10, color=(0.15, 0.15, 0.15))
    page.insert_text((55, 221), "Adresse   : Campus Universitaire, Maroc", fontname="helv", fontsize=9, color=(0.35, 0.35, 0.35))

    # 5. Tableau des Prestations
    y_table = 260
    page.draw_rect(fitz.Rect(40, y_table, 555, y_table + 24), color=couleur_primaire, fill=couleur_primaire)
    page.insert_text((50, y_table + 16), "Réf.", fontname="helv", fontsize=9, color=(1, 1, 1))
    page.insert_text((110, y_table + 16), "Description de la prestation", fontname="helv", fontsize=9, color=(1, 1, 1))
    page.insert_text((380, y_table + 16), "Qté", fontname="helv", fontsize=9, color=(1, 1, 1))
    page.insert_text((430, y_table + 16), "P.U. (MAD)", fontname="helv", fontsize=9, color=(1, 1, 1))
    page.insert_text((500, y_table + 16), "Total HT", fontname="helv", fontsize=9, color=(1, 1, 1))

    y_row = y_table + 24
    montant_total = donnees["montant"]
    montant_ht = round(montant_total / 1.20, 2)
    montant_tva = round(montant_total - montant_ht, 2)

    page.draw_rect(fitz.Rect(40, y_row, 555, y_row + 30), color=(0.90, 0.92, 0.95), width=0.5)
    page.insert_text((50, y_row + 18), "REF-01", fontname="helv", fontsize=9, color=(0.2, 0.2, 0.2))
    page.insert_text((110, y_row + 18), donnees["prestation"], fontname="helv", fontsize=9, color=(0.1, 0.1, 0.1))
    page.insert_text((385, y_row + 18), "1", fontname="helv", fontsize=9, color=(0.2, 0.2, 0.2))
    page.insert_text((435, y_row + 18), f"{montant_ht:.2f}", fontname="helv", fontsize=9, color=(0.2, 0.2, 0.2))
    page.insert_text((505, y_row + 18), f"{montant_ht:.2f}", fontname="helv", fontsize=9, color=(0.2, 0.2, 0.2))

    # 6. Bloc Récapitulatif & Total TTC
    y_totaux = y_row + 45
    page.draw_rect(fitz.Rect(330, y_totaux, 555, y_totaux + 85), color=couleur_fond_clair, fill=couleur_fond_clair)
    page.draw_rect(fitz.Rect(330, y_totaux, 555, y_totaux + 85), color=(0.85, 0.88, 0.92), width=1)
    page.insert_text((345, y_totaux + 20), f"Sous-total HT :  {montant_ht:.2f} MAD", fontname="helv", fontsize=9, color=(0.3, 0.3, 0.3))
    page.insert_text((345, y_totaux + 38), f"TVA (20%)      :  {montant_tva:.2f} MAD", fontname="helv", fontsize=9, color=(0.3, 0.3, 0.3))
    page.draw_line(fitz.Point(345, y_totaux + 48), fitz.Point(540, y_totaux + 48), color=(0.8, 0.8, 0.8), width=1)
    page.insert_text((345, y_totaux + 68), f"Montant: {montant_total:.2f} MAD", fontname="helv", fontsize=13, color=couleur_primaire)

    # 7. Bloc de Métadonnées Standardisées pour Robots RPA
    y_bloc_rpa = y_totaux + 105
    page.draw_rect(fitz.Rect(40, y_bloc_rpa, 555, y_bloc_rpa + 95), color=(0.97, 0.98, 0.99), fill=(0.97, 0.98, 0.99))
    page.draw_rect(fitz.Rect(40, y_bloc_rpa, 555, y_bloc_rpa + 95), color=(0.82, 0.85, 0.90), width=0.8)
    page.insert_text((55, y_bloc_rpa + 16), "BLOC TECHNIQUE STANDARDISÉ RPA (EXTRACTION AUTOMATIQUE)", fontname="helv", fontsize=8, color=(0.4, 0.4, 0.4))
    page.insert_text((55, y_bloc_rpa + 32), f"Numero: {donnees['numero']}", fontname="helv", fontsize=9, color=(0.2, 0.2, 0.2))
    page.insert_text((55, y_bloc_rpa + 46), f"Fournisseur: {donnees['fournisseur']}", fontname="helv", fontsize=9, color=(0.2, 0.2, 0.2))
    page.insert_text((55, y_bloc_rpa + 60), f"Date: {donnees['date']}", fontname="helv", fontsize=9, color=(0.2, 0.2, 0.2))
    page.insert_text((55, y_bloc_rpa + 74), f"Discipline: {donnees['discipline_nom']}", fontname="helv", fontsize=9, color=(0.2, 0.2, 0.2))
    page.insert_text((55, y_bloc_rpa + 88), f"Montant: {montant_total:.2f} MAD", fontname="helv", fontsize=9, color=(0.2, 0.2, 0.2))

    # 8. Pied de page
    page.draw_line(fitz.Point(40, 800), fitz.Point(555, 800), color=(0.8, 0.8, 0.8), width=0.8)
    page.insert_text((130, 816), "Facture dématérialisée - Projet RPA Automatisation IA Agent (Master M2I)", fontname="helv", fontsize=8, color=(0.5, 0.5, 0.5))

    doc.save(chemin_pdf)
    doc.close()
    return chemin_pdf


def generer_factures(
    nb_factures: int = 16,
    disciplines: Optional[List[str]] = None,
    dossier_destination: str = DOSSIER_DESTINATION_DEFAUT,
    dossier_sauvegarde: str = DOSSIER_SAUVEGARDE_DEFAUT,
    format_facture: str = "both",  # "pdf", "txt", ou "both"
    inclure_anomalies: bool = False,
    sauvegarder_automatique: bool = True,
) -> Tuple[List[Dict], str]:
    """
    Génère des factures multidiscipline dans le dossier de destination,
    puis crée une sauvegarde isolée complète dans le dossier de sauvegarde.

    Arguments :
        nb_factures : nombre de factures à générer
        disciplines : liste des disciplines (ex: ['sante', 'finance']) ou None pour toutes
        dossier_destination : dossier où déposer les factures de travail
        dossier_sauvegarde : répertoire isolé pour archiver les factures
        format_facture : 'pdf', 'txt' ou 'both' (les deux)
        inclure_anomalies : générer des cas d'erreurs pour tester la robustesse
        sauvegarder_automatique : enregistrer immédiatement dans la sauvegarde isolée

    Retourne :
        (liste_des_factures_generees, chemin_dossier_sauvegarde_session)
    """
    os.makedirs(dossier_destination, exist_ok=True)

    if not disciplines:
        cles_disponibles = list(CATALOGUE_DISCIPLINES.keys())
    else:
        cles_disponibles = [
            c.lower().strip() for c in disciplines if c.lower().strip() in CATALOGUE_DISCIPLINES
        ]
        if not cles_disponibles:
            raise ValueError(
                f"Aucune discipline valide. Choix possibles : {list(CATALOGUE_DISCIPLINES.keys())}"
            )

    factures_crees = []

    # Distribution équitable entre les disciplines
    for i in range(1, nb_factures + 1):
        cle_discipline = cles_disponibles[(i - 1) % len(cles_disponibles)]
        donnees = generer_facture_donnees(index=i, cle_discipline=cle_discipline)

        fichiers_generes = []

        # Génération TXT si demandé
        if format_facture in ("txt", "both"):
            nom_txt = f"{donnees['numero']}.txt"
            chemin_txt = Path(dossier_destination) / nom_txt
            contenu = formater_contenu_facture(donnees)
            chemin_txt.write_text(contenu, encoding="utf-8")
            fichiers_generes.append(nom_txt)
            donnees["fichier_txt"] = nom_txt

        # Génération PDF si demandé
        if format_facture in ("pdf", "both"):
            nom_pdf = f"{donnees['numero']}.pdf"
            chemin_pdf = Path(dossier_destination) / nom_pdf
            generer_facture_pdf(donnees, chemin_pdf)
            fichiers_generes.append(nom_pdf)
            donnees["fichier_pdf"] = nom_pdf

        donnees["fichier"] = fichiers_generes[0] if fichiers_generes else f"{donnees['numero']}.txt"
        donnees["fichiers"] = fichiers_generes
        factures_crees.append(donnees)

    # Ajout d'anomalies de test si demandé
    if inclure_anomalies:
        anomalie_1 = Path(dossier_destination) / "ERR-MANQUANT.txt"
        anomalie_1.write_text(
            "Numero: ERR-001\nFournisseur: Clinique Test\nDate: 01/10/2026\nMontant:\n",
            encoding="utf-8",
        )
        anomalie_2 = Path(dossier_destination) / "ERR-INVALIDE.txt"
        anomalie_2.write_text(
            "Numero: ERR-002\nFournisseur: Banque Test\nDate: 02/10/2026\nMontant: non-chiffre MAD\n",
            encoding="utf-8",
        )

    chemin_backup_session = ""
    if sauvegarder_automatique:
        chemin_backup_session = sauvegarder_factures(
            dossier_source=dossier_destination,
            dossier_backup_racine=dossier_sauvegarde,
            metadonnees_factures=factures_crees,
        )

    return factures_crees, chemin_backup_session


def sauvegarder_factures(
    dossier_source: str,
    dossier_backup_racine: str,
    metadonnees_factures: Optional[List[Dict]] = None,
    nom_session: Optional[str] = None,
) -> str:
    """
    Sauvegarde l'ensemble des factures (.pdf et .txt) d'un dossier source vers un répertoire isolé.
    Crée :
        1. Un sous-dossier horodaté 'session_YYYYMMDD_HHMMSS'
        2. Un miroir stable 'Derniere_Sauvegarde'
        3. Un fichier 'manifest.json' récapitulant les factures, empreintes SHA256 et montants
    """
    p_source = Path(dossier_source)
    p_backup_racine = Path(dossier_backup_racine)

    if not p_source.exists():
        raise FileNotFoundError(f"Le dossier source {dossier_source} n'existe pas.")

    horodatage = datetime.now()
    session_id = nom_session or f"session_{horodatage.strftime('%Y%m%d_%H%M%S')}"

    dossier_session = p_backup_racine / session_id
    dossier_miroir = p_backup_racine / "Derniere_Sauvegarde"

    os.makedirs(dossier_session, exist_ok=True)
    os.makedirs(dossier_miroir, exist_ok=True)

    # Récupération de tous les fichiers .txt et .pdf à la racine du dossier source
    extensions_valides = {".txt", ".pdf"}
    fichiers_source = [
        f for f in p_source.iterdir() if f.is_file() and f.suffix.lower() in extensions_valides
    ]

    inventaire = []
    total_mad = 0.0
    par_discipline = {}
    factures_uniques = set()

    meta_par_stem = {}
    if metadonnees_factures:
        for m in metadonnees_factures:
            meta_par_stem[m.get("numero")] = m

    for f in sorted(fichiers_source):
        cible_session = dossier_session / f.name
        cible_miroir = dossier_miroir / f.name

        shutil.copy2(f, cible_session)
        shutil.copy2(f, cible_miroir)

        sha256_hash = calculer_sha256(cible_session)
        stem_facture = f.stem
        meta = meta_par_stem.get(stem_facture, {})

        montant = meta.get("montant", 0.0)
        disc = meta.get("discipline_nom", "Général")

        # Comptabilise le total et la discipline une seule fois par numéro de facture
        if stem_facture not in factures_uniques:
            total_mad += montant
            par_discipline[disc] = par_discipline.get(disc, 0) + 1
            factures_uniques.add(stem_facture)

        inventaire.append({
            "fichier": f.name,
            "format": f.suffix.lower().replace(".", ""),
            "sha256": sha256_hash,
            "numero": meta.get("numero", stem_facture),
            "fournisseur": meta.get("fournisseur", "Inconnu"),
            "discipline": disc,
            "date": meta.get("date", ""),
            "montant": montant,
            "statut_attendu": meta.get("statut_attendu", "Non déterminé"),
        })

    # Création du manifest.json
    manifest = {
        "session_id": session_id,
        "date_sauvegarde": horodatage.strftime("%Y-%m-%d %H:%M:%S"),
        "dossier_source_initial": str(p_source.resolve()),
        "nombre_fichiers": len(inventaire),
        "nombre_factures_uniques": len(factures_uniques),
        "total_montant_mad": round(total_mad, 2),
        "repartition_disciplines": par_discipline,
        "factures": inventaire,
    }

    manifest_json_session = dossier_session / "manifest.json"
    manifest_json_miroir = dossier_miroir / "manifest.json"

    with open(manifest_json_session, "w", encoding="utf-8") as f_out:
        json.dump(manifest, f_out, ensure_ascii=False, indent=2)

    with open(manifest_json_miroir, "w", encoding="utf-8") as f_out:
        json.dump(manifest, f_out, ensure_ascii=False, indent=2)

    return str(dossier_session.resolve())


def restaurer_sauvegarde(
    dossier_backup: str,
    dossier_destination: str = DOSSIER_DESTINATION_DEFAUT,
    format_cible: Optional[str] = None,  # None (tous), "pdf", "txt"
    ecraser: bool = True,
) -> int:
    """
    Restaure les factures (.pdf et .txt) depuis un répertoire de sauvegarde isolé
    vers le dossier de travail pour pouvoir les réutiliser après exécution du robot RPA.

    Retourne le nombre de fichiers restaurés.
    """
    p_backup = Path(dossier_backup)
    p_dest = Path(dossier_destination)

    # Si l'utilisateur pointe sur la racine des sauvegardes, utiliser la dernière sauvegarde
    if (p_backup / "Derniere_Sauvegarde").is_dir():
        p_backup = p_backup / "Derniere_Sauvegarde"

    if not p_backup.is_dir():
        raise FileNotFoundError(f"Dossier de sauvegarde introuvable : {p_backup}")

    os.makedirs(p_dest, exist_ok=True)

    extensions_valides = {".txt", ".pdf"}
    if format_cible == "pdf":
        extensions_valides = {".pdf"}
    elif format_cible == "txt":
        extensions_valides = {".txt"}

    fichiers = [
        f for f in p_backup.iterdir() if f.is_file() and f.suffix.lower() in extensions_valides
    ]
    nb_restaures = 0

    for f in fichiers:
        dest_fichier = p_dest / f.name
        if not dest_fichier.exists() or ecraser:
            shutil.copy2(f, dest_fichier)
            nb_restaures += 1

    return nb_restaures


def lister_sauvegardes(dossier_backup_racine: str = DOSSIER_SAUVEGARDE_DEFAUT) -> List[Dict]:
    """
    Scanne et liste les sauvegardes disponibles dans le répertoire de sauvegarde isolé.
    """
    p_racine = Path(dossier_backup_racine)
    if not p_racine.exists():
        return []

    resultats = []
    for item in sorted(p_racine.iterdir(), reverse=True):
        if item.is_dir() and item.name != "Derniere_Sauvegarde":
            manifest_file = item / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        resultats.append(data)
                except Exception:
                    pass
            else:
                nb_fichiers = len(list(item.glob("*.txt"))) + len(list(item.glob("*.pdf")))
                resultats.append({
                    "session_id": item.name,
                    "date_sauvegarde": "Inconnue",
                    "nombre_fichiers": nb_fichiers,
                    "nombre_factures_uniques": nb_fichiers,
                    "repartition_disciplines": {},
                })
    return resultats


# ----------------------------------------------------------------------
# CLI INTERFACE
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Générateur de factures multidiscipline (PDF & TXT) avec sauvegarde isolée (TP RPA)."
    )
    parser.add_argument(
        "--nb",
        type=int,
        default=16,
        help="Nombre de factures à générer (défaut: 16)",
    )
    parser.add_argument(
        "--disciplines",
        nargs="+",
        default=None,
        choices=list(CATALOGUE_DISCIPLINES.keys()),
        help="Disciplines ciblées (ex: sante finance telecom). Si omis, toutes sont utilisées.",
    )
    parser.add_argument(
        "--format",
        choices=["pdf", "txt", "both"],
        default="both",
        help="Format des factures à générer : 'pdf', 'txt' ou 'both' (défaut: both)",
    )
    parser.add_argument(
        "--dest",
        default=DOSSIER_DESTINATION_DEFAUT,
        help=f"Dossier de destination de travail (défaut: '{DOSSIER_DESTINATION_DEFAUT}')",
    )
    parser.add_argument(
        "--backup",
        default=DOSSIER_SAUVEGARDE_DEFAUT,
        help=f"Répertoire isolé de sauvegarde (défaut: '{DOSSIER_SAUVEGARDE_DEFAUT}')",
    )
    parser.add_argument(
        "--anomalies",
        action="store_true",
        help="Inclure des factures avec erreurs (montant manquant/invalide) pour tester la robustesse",
    )
    parser.add_argument(
        "--restaurer",
        action="store_true",
        help="Restaurer les factures sauvegardées vers le dossier de destination",
    )
    parser.add_argument(
        "--lister",
        action="store_true",
        help="Lister l'historique des sauvegardes isolées",
    )
    parser.add_argument(
        "--session",
        default=None,
        help="Nom de session spécifique à restaurer (optionnel, sinon la plus récente)",
    )

    args = parser.parse_args()

    # Action 1: Lister les sauvegardes
    if args.lister:
        sauvegardes = lister_sauvegardes(args.backup)
        print("\n=== HISTORIQUE DES SAUVEGARDES ISOLÉES ===")
        if not sauvegardes:
            print(f"Aucune sauvegarde trouvée dans '{args.backup}'.")
        else:
            for s in sauvegardes:
                nb = s.get("nombre_factures_uniques") or s.get("nombre_factures") or s.get("nombre_fichiers")
                print(
                    f"- Session : {s.get('session_id')} | "
                    f"Date : {s.get('date_sauvegarde')} | "
                    f"Factures : {nb} | "
                    f"Total : {s.get('total_montant_mad', 0):.2f} MAD"
                )
                if s.get("repartition_disciplines"):
                    print(f"  Disciplines : {dict(s.get('repartition_disciplines'))}")
        print()
        return

    # Action 2: Restaurer une sauvegarde
    if args.restaurer:
        source_restauration = (
            Path(args.backup) / args.session if args.session else Path(args.backup)
        )
        print(f"\n[Restauration] Source : {source_restauration} -> Destination : {args.dest}")
        nb = restaurer_sauvegarde(
            str(source_restauration),
            dossier_destination=args.dest,
            format_cible=None if args.format == "both" else args.format,
        )
        print(f"[Succès] {nb} fichier(s) restauré(s) dans '{args.dest}/' prêtes à être traitées !\n")
        return

    # Action 3: Génération et sauvegarde automatique
    print(f"\n[Génération] Création de {args.nb} factures multidiscipline (format: {args.format.upper()})...")
    factures, chemin_backup = generer_factures(
        nb_factures=args.nb,
        disciplines=args.disciplines,
        dossier_destination=args.dest,
        dossier_sauvegarde=args.backup,
        format_facture=args.format,
        inclure_anomalies=args.anomalies,
        sauvegarder_automatique=True,
    )

    print(f"[OK] Factures créées dans le dossier de travail : '{args.dest}/'")
    print(f"[OK] Sauvegarde isolée sécurisée créée dans    : '{chemin_backup}'")
    print(f"[OK] Miroir d'accès rapide disponible dans     : '{Path(args.backup) / 'Derniere_Sauvegarde'}'")

    # Résumé
    disciplines_compte = {}
    total_somme = 0.0
    nb_a_controler = 0
    for f in factures:
        d = f["discipline_nom"]
        disciplines_compte[d] = disciplines_compte.get(d, 0) + 1
        total_somme += f["montant"]
        if f["statut_attendu"] == "À contrôler":
            nb_a_controler += 1

    print("\n=== RÉSUMÉ DE LA GÉNÉRATION ===")
    print(f"Total factures : {len(factures)}")
    print(f"Total montant  : {total_somme:,.2f} MAD")
    print(f"Normaux (<= 1000 MAD)   : {len(factures) - nb_a_controler}")
    print(f"À contrôler (> 1000 MAD) : {nb_a_controler}")
    print("Répartition par discipline :")
    for d, c in disciplines_compte.items():
        print(f"  • {d:25s} : {c} facture(s)")
    print(
        f"\nAstuce : Après traitement par tp2.py (qui déplace les fichiers),\n"
        f"vous pourrez recharger ces factures à tout moment via :\n"
        f"  python generateur_factures.py --restaurer\n"
    )


if __name__ == "__main__":
    main()
