import json
import unittest
from pathlib import Path

from agent_local import LocalAgent


ROOT = Path(__file__).parent


class LocalAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = LocalAgent(ROOT / "knowledge_base")

    def test_documented_question_returns_source(self) -> None:
        result = self.agent.respond("Quels thèmes sont abordés dans le module ?")
        self.assertEqual(result["categorie"], "pédagogique")
        self.assertIn("Prompting", result["reponse"])
        self.assertIn("DEMO_descriptif_module.md", result["source"])

    def test_missing_information_escalates(self) -> None:
        result = self.agent.respond("Quel est le numéro de salle ?")
        self.assertEqual(result["source"], "")
        self.assertTrue(result["escalade"] if "escalade" in result else True)
        self.assertIn("n’apparaît pas", result["reponse"])

    def test_latest_calendar_version_is_selected(self) -> None:
        result = self.agent.respond("La séance de démonstration est-elle maintenue ?")
        self.assertIn("reportée", result["reponse"])
        self.assertIn("v2", result["source"])

    def test_multiple_intentions_are_classified(self) -> None:
        result = self.agent.classify("Je n’arrive pas à accéder au support et la séance est-elle maintenue ?")
        self.assertEqual(result["categorie"], ["scolarité", "technique"])

    def test_exam_question_does_not_use_calendar(self) -> None:
        result = self.agent.respond("Quelle est la date de l’examen final ?")
        self.assertEqual(result["source"], "")
        self.assertTrue(result["escalade"])

    def test_memory_question_is_pedagogical(self) -> None:
        result = self.agent.classify("Qu’est-ce que la mémoire conversationnelle ?")
        self.assertEqual(result["categorie"], "pédagogique")

    def test_exam_duration_is_exam_category(self) -> None:
        result = self.agent.classify("Quelle est la durée de l’épreuve ?")
        self.assertEqual(result["categorie"], "examens")

    def test_report_deadline_does_not_use_calendar(self) -> None:
        result = self.agent.respond("Quelle est la date exacte de remise du rapport ?")
        self.assertEqual(result["source"], "")

    def test_out_of_scope_text_does_not_retrieve_fixture_metadata(self) -> None:
        result = self.agent.respond("exemple inventé; remplacé explicitement par v2 dans la fixture de test.")
        self.assertEqual(result["source"], "")

    def test_agent_and_llm_difference_requires_direct_evidence(self) -> None:
        result = self.agent.respond("Peux-tu m’expliquer la différence entre un agent et un LLM ?")
        self.assertEqual(result["source"], "")

    def test_inscription_does_not_reuse_tp_instructions(self) -> None:
        result = self.agent.respond("Où en est ma demande d’inscription ?")
        self.assertEqual(result["source"], "")

    def test_multiple_intentions_report_missing_technical_information(self) -> None:
        result = self.agent.respond(
            "Je n’arrive pas à accéder au support et la séance est-elle maintenue ?"
        )
        self.assertIn("Accès au support", result["reponse"])
        self.assertTrue(result["escalade"])

    def test_multiple_pedagogical_and_exam_intentions_are_separated(self) -> None:
        result = self.agent.respond(
            "Explique-moi les agents IA et donne-moi la date de l’examen."
        )
        self.assertIn("Partie pédagogique", result["reponse"])
        self.assertIn("Partie examen", result["reponse"])

    def test_json_has_exact_required_keys(self) -> None:
        result = json.loads(self.agent.respond("Explique-moi ce qu’est un agent IA.", json_output=True))
        self.assertEqual(set(result), {"categorie", "intention", "priorite", "reponse", "source"})

    def test_added_document_is_searchable_and_cited(self) -> None:
        self.agent.store.add_text(
            "assistant_test.md",
            "# Concept\n\n## Mission\n"
            "Un assistant IA aide les étudiants avec des sources vérifiées.",
        )
        result = self.agent.respond("Quelle est la mission de l’assistant IA ?")
        self.assertIn("Un assistant IA aide les étudiants", result["reponse"])
        self.assertIn("assistant_test.md", result["source"])
        self.assertFalse(result["escalade"])

    def test_memory_filters_irrelevant_information(self) -> None:
        self.agent.remember("groupe", "TP Atlas")
        self.agent.remember("projet", "assistant de recherche documentaire")
        self.agent.remember("vacances", "Marrakech")
        context = self.agent.filtered_context("Quel est notre projet de recherche documentaire ?")
        self.assertEqual(set(context), {"projet"})

    def test_workflow_contains_all_steps(self) -> None:
        workflow = self.agent.workflow("Quel est le livrable de démonstration ?")
        self.assertEqual(set(workflow), {"analyse", "recherche", "verification", "reponse", "escalade"})


if __name__ == "__main__":
    unittest.main()
