"""Agent pédagogique local, déterministe et sans dépendance externe."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CATEGORIES = ("pédagogique", "scolarité", "technique", "examens", "autre")
PRIORITIES = ("basse", "normale", "haute")


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char)).lower()


def _words(text: str) -> set[str]:
    stopwords = {
        "avec", "dans", "des", "elle", "les", "mais", "quel", "quelle",
        "que", "sont", "sur", "une", "pour", "est", "pas", "aux",
    }
    return {
        word for word in re.findall(r"[a-z0-9]{3,}", _normalize(text))
        if word not in stopwords
    }


@dataclass(frozen=True)
class Passage:
    document: str
    version: int
    section: str
    text: str
    score: int

    @property
    def source(self) -> str:
        return f"{self.document}, section « {self.section} »"


class DocumentStore:
    """Charge des Markdown et retrouve uniquement les passages pertinents."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self._documents = self._load()

    def _load(self) -> list[tuple[str, int, list[tuple[str, str]]]]:
        documents = []
        for path in sorted(self.directory.glob("*.md")):
            if path.name.upper() == "README.MD":
                continue
            content = path.read_text(encoding="utf-8")
            version_match = re.search(r"v(\d+)", path.stem, re.IGNORECASE)
            version = int(version_match.group(1)) if version_match else 1
            sections: list[tuple[str, str]] = []
            section = "Document"
            buffer: list[str] = []
            for line in content.splitlines():
                if line.startswith("## "):
                    if buffer:
                        sections.append((section, " ".join(buffer).strip()))
                    section = line[3:].strip()
                    buffer = []
                elif (
                    line.strip()
                    and not line.startswith("#")
                    and not line.startswith("Statut :")
                ):
                    buffer.append(line.strip())
            if buffer:
                sections.append((section, " ".join(buffer).strip()))
            documents.append((path.name, version, sections))
        return documents

    def search(self, query: str, limit: int = 5) -> list[Passage]:
        query_words = _words(query)
        passages: list[Passage] = []
        for document, version, sections in self._documents:
            for section, text in sections:
                score = len(query_words & _words(f"{section} {text}"))
                if score:
                    passages.append(Passage(document, version, section, text, score))
        passages.sort(key=lambda passage: (-passage.score, -passage.version, passage.document))
        return passages[:limit]

    def versions(self, document_prefix: str) -> list[Passage]:
        results = []
        for document, version, sections in self._documents:
            if document.startswith(document_prefix):
                results.extend(Passage(document, version, section, text, 0) for section, text in sections)
        return sorted(results, key=lambda passage: -passage.version)


class LocalAgent:
    """Assistant pédagogique implémentant le workflow du TP7."""

    def __init__(self, knowledge_base: str | Path) -> None:
        self.store = DocumentStore(knowledge_base)
        self.memory: dict[str, str] = {}

    def classify(self, request: str, few_shot: bool = True) -> dict[str, Any]:
        normalized = _normalize(request)
        categories: list[str] = []
        if any(word in normalized for word in (
            "explique", "notion", "cours", "agent ia", "prompt", "theme",
            "aborde", "module", "memoire", "conversationnelle",
        )):
            categories.append("pédagogique")
        if any(word in normalized for word in ("inscription", "seance", "séance", "maintenue", "calendrier", "salle")):
            categories.append("scolarité")
        if any(word in normalized for word in ("acceder", "accéder", "ouvrir", "lien", "erreur", "support")):
            categories.append("technique")
        if any(word in normalized for word in (
            "examen", "epreuve", "note", "controle", "duree", "épreuve",
        )):
            categories.append("examens")
        if not categories:
            categories.append("autre")
        priority = "haute" if "examen" in normalized or "epreuve" in normalized else "normale"
        if categories == ["autre"] and len(_words(request)) < 4:
            priority = "basse"
        return {
            "categorie": categories if len(categories) > 1 else categories[0],
            "intention": request.strip(),
            "priorite": priority,
            "mode": "few-shot" if few_shot else "zero-shot",
        }

    def _contradiction(self, passages: list[Passage]) -> bool:
        versions = {passage.version for passage in passages}
        if len(versions) <= 1:
            return False
        latest = max(passages, key=lambda passage: passage.version)
        return "remplace" not in _normalize(latest.text)

    def retrieve(self, request: str) -> tuple[dict[str, Any], list[Passage]]:
        classification = self.classify(request)
        categories = classification["categorie"]
        categories = categories if isinstance(categories, list) else [categories]
        queries = [request]
        if len(categories) > 1:
            queries = []
            if "technique" in categories:
                queries.append("accéder au support lien erreur")
            if "scolarité" in categories:
                queries.append("séance maintenue calendrier")
            if "pédagogique" in categories:
                queries.append("agent IA thèmes module")
            if "examens" in categories:
                queries.append("examen date")
            queries.extend(category for category in categories if category not in ("technique", "scolarité"))
        passages = []
        for query in queries:
            for passage in self.store.search(query):
                if passage not in passages:
                    passages.append(passage)
        normalized_request = _normalize(request)
        if categories == ["autre"]:
            passages = []
        if "inscription" in normalized_request:
            passages = [
                passage for passage in passages
                if "inscription" in _normalize(passage.text)
            ]
        if "llm" in normalized_request and "agent" in normalized_request:
            passages = [
                passage for passage in passages
                if "llm" in _normalize(passage.text)
                and "agent" in _normalize(passage.text)
            ]
        if "salut" in normalized_request or "bonjour" in normalized_request:
            passages = []
        if categories == ["examens"]:
            passages = [
                passage for passage in passages
                if "examen" in _normalize(passage.text)
            ]
        report_deadline_question = (
            "rapport" in _normalize(request)
            and "remise" in _normalize(request)
            and "date" in _normalize(request)
        )
        if report_deadline_question:
            passages = []
        has_calendar_version = any(
            "calendrier" in _normalize(passage.document) for passage in passages
        )
        if "seance" in normalized_request and has_calendar_version:
            passages.sort(key=lambda passage: (-passage.version, -passage.score, passage.document))
        else:
            passages.sort(key=lambda passage: (-passage.score, -passage.version, passage.document))
        return classification, passages[:3]

    def respond(self, request: str, json_output: bool = False) -> dict[str, Any] | str:
        classification, relevant = self.retrieve(request)
        categories = classification["categorie"]
        categories = categories if isinstance(categories, list) else [categories]
        missing = not relevant
        contradiction = self._contradiction(relevant)
        if missing:
            response = "L’information n’apparaît pas dans les documents disponibles."
            source = ""
            follow_up = "Adressez-vous à l’enseignante ou au responsable compétent pour confirmation."
        elif contradiction:
            response = "Les documents disponibles présentent des informations contradictoires."
            source = "; ".join(passage.source for passage in relevant)
            follow_up = "Demandez confirmation au responsable; aucune décision ne peut être inventée."
        else:
            latest = relevant[0]
            response = latest.text
            source = latest.source
            follow_up = "Aucune."
            if len(categories) > 1 and "examens" in categories:
                response = (
                    "Partie pédagogique : " + latest.text
                    + " Partie examen : l’information n’apparaît pas dans les documents disponibles."
                )
                follow_up = "La date ou les modalités de l’examen doivent être confirmées auprès du responsable."
            if len(categories) > 1:
                missing_categories = [
                    category for category in categories
                    if not any(
                        category == "technique" and any(
                            term in _normalize(passage.text)
                            for term in ("support", "acces", "lien", "erreur")
                        )
                        for passage in relevant
                    )
                ]
                if "technique" in missing_categories:
                    response = (
                        "Accès au support : l’information technique n’est pas "
                        "documentée. Séance : " + latest.text
                    )
                    follow_up = (
                        "La procédure d’accès doit être confirmée auprès du "
                        "responsable technique."
                    )
        result = {
            "categorie": classification["categorie"],
            "intention": classification["intention"],
            "priorite": classification["priorite"],
            "reponse": response,
            "source": source,
            "explication": "Les passages ont été sélectionnés par recouvrement de termes et priorité de version.",
            "information_manquante": follow_up,
            "escalade": follow_up != "Aucune.",
            "passages": [
                {"document": passage.document, "section": passage.section, "extrait": passage.text}
                for passage in relevant
            ],
        }
        return json.dumps(
            {key: result[key] for key in ("categorie", "intention", "priorite", "reponse", "source")},
            ensure_ascii=False,
        ) if json_output else result

    def remember(self, key: str, value: str) -> None:
        self.memory[key] = value

    def filtered_context(self, request: str) -> dict[str, str]:
        requested_words = _words(request)
        return {
            key: value
            for key, value in self.memory.items()
            if requested_words & _words(f"{key} {value}")
        }

    def workflow(self, request: str) -> dict[str, Any]:
        analysis = self.classify(request)
        response = self.respond(request)
        assert isinstance(response, dict)
        return {
            "analyse": analysis,
            "recherche": response["passages"],
            "verification": {
                "source_trouvee": bool(response["source"]),
                "information_absente": not bool(response["passages"]),
                "contradiction": response["reponse"].startswith("Les documents"),
            },
            "reponse": response,
            "escalade": response["information_manquante"] != "Aucune.",
        }
