import tempfile
import unittest
from email import message_from_string
from email.header import decode_header, make_header
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import tp2


class ExtractionFactureTests(unittest.TestCase):
    def test_extrait_une_facture_valide(self):
        contenu = (
            "Numero: F001\n"
            "Fournisseur: ABC Distribution\n"
            "Date: 01/10/2026\n"
            "Montant: 500 MAD\n"
        )

        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "F001.txt"
            chemin.write_text(contenu, encoding="utf-8")

            facture = tp2.extraire_facture(str(chemin))

        self.assertEqual(facture["N°"], "F001")
        self.assertEqual(facture["Fournisseur"], "ABC Distribution")
        self.assertEqual(facture["Date"], "01/10/2026")
        self.assertEqual(facture["Montant"], 500.0)

    def test_signale_un_fichier_illisible(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "illisible.txt"
            chemin.write_bytes(b"\xff")

            with self.assertRaisesRegex(ValueError, "Fichier illisible"):
                tp2.extraire_facture(str(chemin))

    def test_signale_une_information_manquante(self):
        contenu = (
            "Numero: F001\n"
            "Fournisseur: ABC Distribution\n"
            "Montant: 500 MAD\n"
        )

        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "incomplete.txt"
            chemin.write_text(contenu, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Information manquante"):
                tp2.extraire_facture(str(chemin))

    def test_signale_un_montant_vide(self):
        contenu = (
            "Numero: F001\n"
            "Fournisseur: ABC Distribution\n"
            "Date: 01/10/2026\n"
            "Montant: \n"
        )

        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "empty-amount.txt"
            chemin.write_text(contenu, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Montant manquant"):
                tp2.extraire_facture(str(chemin))

    def test_signale_un_montant_invalide(self):
        contenu = (
            "Numero: F001\n"
            "Fournisseur: ABC Distribution\n"
            "Date: 01/10/2026\n"
            "Montant: abc MAD\n"
        )

        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "invalid.txt"
            chemin.write_text(contenu, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Montant incorrect"):
                tp2.extraire_facture(str(chemin))


class DecisionFactureTests(unittest.TestCase):
    def test_applique_le_seuil_inclusif_de_mille_mad(self):
        factures = pd.DataFrame({"Montant": [500.0, 1000.0, 1000.01]})

        resultat = tp2.appliquer_decision(factures)

        self.assertEqual(
            resultat["Statut"].tolist(),
            ["Normal", "Normal", "À contrôler"],
        )


class FluxCompletTemporaireTests(unittest.TestCase):
    def test_genere_rapport_classe_factures_et_neutralise_email(self):
        with tempfile.TemporaryDirectory() as dossier_temporaire:
            racine = Path(dossier_temporaire)
            dossier_factures = racine / "Factures"
            dossier_traitees = dossier_factures / "Traitees"
            dossier_a_controler = dossier_factures / "A_controler"
            rapport = racine / "rapport_factures.xlsx"
            journal = racine / "log.txt"

            with (
                patch.object(tp2, "DOSSIER_FACTURES", str(dossier_factures)),
                patch.object(tp2, "DOSSIER_TRAITEES", str(dossier_traitees)),
                patch.object(tp2, "DOSSIER_A_CONTROLER", str(dossier_a_controler)),
                patch.object(tp2, "RAPPORT_EXCEL", str(rapport)),
                patch.object(tp2, "LOG_FILE", str(journal)),
                patch.object(tp2, "envoyer_notification") as notifier,
            ):
                tp2.main()

            self.assertTrue(rapport.is_file())
            self.assertTrue(journal.is_file())
            self.assertEqual(
                sorted(path.name for path in dossier_traitees.iterdir()),
                ["F001.txt", "F003.txt", "F005.txt"],
            )
            self.assertEqual(
                sorted(path.name for path in dossier_a_controler.iterdir()),
                ["F002.txt", "F004.txt"],
            )
            self.assertEqual(
                sorted(path.name for path in dossier_factures.glob("*.txt")),
                ["F006.txt", "F007.txt"],
            )
            self.assertEqual(notifier.call_count, 2)

            resultat_excel = pd.read_excel(rapport)
            self.assertEqual(len(resultat_excel), 5)
            self.assertEqual(
                resultat_excel["Statut"].tolist(),
                ["Normal", "À contrôler", "Normal", "À contrôler", "Normal"],
            )


class NotificationFactureTests(unittest.TestCase):
    def test_construit_le_message_sans_contacter_un_serveur_reel(self):
        with tempfile.TemporaryDirectory() as dossier_temporaire:
            journal = Path(dossier_temporaire) / "log.txt"

            with (
                patch.object(tp2, "LOG_FILE", str(journal)),
                patch.object(tp2, "SMTP_EMAIL", "robot@example.test"),
                patch.object(tp2, "SMTP_APP_PASSWORD", "test-password"),
                patch.object(tp2, "RESPONSABLE_EMAIL", "responsable@example.test"),
                patch.object(tp2.smtplib, "SMTP_SSL") as smtp_ssl,
            ):
                serveur = smtp_ssl.return_value.__enter__.return_value
                tp2.envoyer_notification("F002", "Tech Solutions", 1500.0)

            smtp_ssl.assert_called_once_with("smtp.gmail.com", 465)
            serveur.login.assert_called_once()
            serveur.sendmail.assert_called_once()

            expediteur, destinataire, contenu = serveur.sendmail.call_args.args
            message = message_from_string(contenu)
            partie_texte = message.get_payload(0)
            corps = partie_texte.get_payload(decode=True).decode(
                partie_texte.get_content_charset()
            )
            sujet = str(make_header(decode_header(message["Subject"])))

            self.assertEqual(expediteur, "robot@example.test")
            self.assertEqual(destinataire, "responsable@example.test")
            self.assertEqual(message["To"], "responsable@example.test")
            self.assertEqual(sujet, "Facture à contrôler : F002")
            self.assertIn("Numéro : F002", corps)
            self.assertIn("Fournisseur : Tech Solutions", corps)
            self.assertIn("Montant : 1500.0 MAD", corps)

    def test_ignore_l_envoi_si_la_configuration_est_absente(self):
        with tempfile.TemporaryDirectory() as dossier_temporaire:
            journal = Path(dossier_temporaire) / "log.txt"

            with (
                patch.object(tp2, "LOG_FILE", str(journal)),
                patch.object(tp2, "SMTP_EMAIL", ""),
                patch.object(tp2, "SMTP_APP_PASSWORD", ""),
                patch.object(tp2, "RESPONSABLE_EMAIL", ""),
                patch.object(tp2.smtplib, "SMTP_SSL") as smtp_ssl,
            ):
                tp2.envoyer_notification("F002", "Tech Solutions", 1500.0)

            smtp_ssl.assert_not_called()
            self.assertIn("configuration email absente", journal.read_text("utf-8"))


if __name__ == "__main__":
    unittest.main()
