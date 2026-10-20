import json
import tempfile
import unittest
from pathlib import Path

import generateur_factures
import tp2


class GenerateurFacturesTests(unittest.TestCase):
    def test_catalogue_contient_toutes_les_disciplines_requises(self):
        disciplines_attendues = {
            "sante",
            "finance",
            "energie",
            "telecom",
            "education",
            "logement",
            "transport",
            "commerce",
        }
        cles_catalogue = set(generateur_factures.CATALOGUE_DISCIPLINES.keys())
        self.assertTrue(
            disciplines_attendues.issubset(cles_catalogue),
            f"Manque des disciplines : {disciplines_attendues - cles_catalogue}",
        )

    def test_generation_donnees_respecte_format_et_seuils(self):
        for cle in ["sante", "finance", "energie", "telecom"]:
            donnees_norm = generateur_factures.generer_facture_donnees(
                index=1, cle_discipline=cle, forcer_statut="normal"
            )
            self.assertLessEqual(donnees_norm["montant"], 1000.0)
            self.assertEqual(donnees_norm["statut_attendu"], "Normal")

            donnees_ctrl = generateur_factures.generer_facture_donnees(
                index=2, cle_discipline=cle, forcer_statut="a_controler"
            )
            self.assertGreater(donnees_ctrl["montant"], 1000.0)
            self.assertEqual(donnees_ctrl["statut_attendu"], "À contrôler")

    def test_factures_txt_compatibles_avec_extracteur_tp2(self):
        with tempfile.TemporaryDirectory() as dossier_tmp:
            factures, _ = generateur_factures.generer_factures(
                nb_factures=6,
                disciplines=["sante", "finance"],
                dossier_destination=dossier_tmp,
                format_facture="txt",
                sauvegarder_automatique=False,
            )

            self.assertEqual(len(factures), 6)

            for f_meta in factures:
                chemin = Path(dossier_tmp) / f_meta["fichier"]
                self.assertTrue(chemin.exists())

                facture_extraite = tp2.extraire_facture(str(chemin))
                self.assertEqual(facture_extraite["N°"], f_meta["numero"])
                self.assertEqual(facture_extraite["Fournisseur"], f_meta["fournisseur"])
                self.assertEqual(facture_extraite["Date"], f_meta["date"])
                self.assertAlmostEqual(facture_extraite["Montant"], f_meta["montant"], places=2)

    def test_factures_pdf_generees_et_extraites_avec_succes(self):
        with tempfile.TemporaryDirectory() as dossier_tmp:
            factures, _ = generateur_factures.generer_factures(
                nb_factures=4,
                disciplines=["sante", "finance", "energie", "telecom"],
                dossier_destination=dossier_tmp,
                format_facture="pdf",
                sauvegarder_automatique=False,
            )

            self.assertEqual(len(factures), 4)

            for f_meta in factures:
                chemin_pdf = Path(dossier_tmp) / f"{f_meta['numero']}.pdf"
                self.assertTrue(chemin_pdf.exists())

                # Vérifie que le robot RPA (tp2.extraire_facture) extrait fidèlement le PDF
                facture_extraite = tp2.extraire_facture(str(chemin_pdf))
                self.assertEqual(facture_extraite["N°"], f_meta["numero"])
                self.assertEqual(facture_extraite["Fournisseur"], f_meta["fournisseur"])
                self.assertEqual(facture_extraite["Date"], f_meta["date"])
                self.assertAlmostEqual(facture_extraite["Montant"], f_meta["montant"], places=2)
                self.assertEqual(facture_extraite["Discipline"], f_meta["discipline_nom"])

    def test_sauvegarde_isolee_et_manifest_crees_avec_pdf_et_txt(self):
        with tempfile.TemporaryDirectory() as dossier_tmp:
            p_tmp = Path(dossier_tmp)
            dest_dir = p_tmp / "Factures_Travail"
            backup_dir = p_tmp / "Sauvegardes_Isolees"

            factures, chemin_backup = generateur_factures.generer_factures(
                nb_factures=4,
                dossier_destination=str(dest_dir),
                dossier_sauvegarde=str(backup_dir),
                format_facture="both",
                sauvegarder_automatique=True,
            )

            p_backup_session = Path(chemin_backup)
            self.assertTrue(p_backup_session.is_dir())

            # Vérifier la présence du manifest
            manifest_file = p_backup_session / "manifest.json"
            self.assertTrue(manifest_file.exists())

            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            # 4 factures x 2 formats = 8 fichiers au total
            self.assertEqual(manifest["nombre_fichiers"], 8)
            self.assertEqual(manifest["nombre_factures_uniques"], 4)
            self.assertGreater(manifest["total_montant_mad"], 0.0)

            # Vérifier la présence des fichiers .pdf et .txt dans le dossier isolé
            fichiers_backup_pdf = list(p_backup_session.glob("*.pdf"))
            fichiers_backup_txt = list(p_backup_session.glob("*.txt"))
            self.assertEqual(len(fichiers_backup_pdf), 4)
            self.assertEqual(len(fichiers_backup_txt), 4)

            # Vérifier également le dossier miroir 'Derniere_Sauvegarde'
            miroir_dir = backup_dir / "Derniere_Sauvegarde"
            self.assertTrue(miroir_dir.is_dir())
            self.assertEqual(len(list(miroir_dir.glob("*.pdf"))), 4)

    def test_restauration_depuis_sauvegarde_isolee(self):
        with tempfile.TemporaryDirectory() as dossier_tmp:
            p_tmp = Path(dossier_tmp)
            dest_dir = p_tmp / "Factures_Travail"
            backup_dir = p_tmp / "Sauvegardes_Isolees"

            # 1. Génération initiale (PDF + TXT)
            generateur_factures.generer_factures(
                nb_factures=3,
                dossier_destination=str(dest_dir),
                dossier_sauvegarde=str(backup_dir),
                format_facture="both",
                sauvegarder_automatique=True,
            )

            # 2. Simulation de l'action du robot RPA (suppression des fichiers du dossier de travail)
            for f in dest_dir.iterdir():
                if f.is_file():
                    f.unlink()
            self.assertEqual(len(list(dest_dir.iterdir())), 0)

            # 3. Restauration depuis la sauvegarde isolée
            nb_restaures = generateur_factures.restaurer_sauvegarde(
                dossier_backup=str(backup_dir),
                dossier_destination=str(dest_dir),
            )

            self.assertEqual(nb_restaures, 6)  # 3 PDF + 3 TXT
            self.assertEqual(len(list(dest_dir.glob("*.pdf"))), 3)
            self.assertEqual(len(list(dest_dir.glob("*.txt"))), 3)

    def test_lister_sauvegardes(self):
        with tempfile.TemporaryDirectory() as dossier_tmp:
            p_tmp = Path(dossier_tmp)
            dest_dir = p_tmp / "Factures_Travail"
            backup_dir = p_tmp / "Sauvegardes_Isolees"

            generateur_factures.generer_factures(
                nb_factures=3,
                dossier_destination=str(dest_dir),
                dossier_sauvegarde=str(backup_dir),
                format_facture="pdf",
            )

            liste = generateur_factures.lister_sauvegardes(str(backup_dir))
            self.assertGreaterEqual(len(liste), 1)
            self.assertEqual(liste[0]["nombre_fichiers"], 3)


if __name__ == "__main__":
    unittest.main()
