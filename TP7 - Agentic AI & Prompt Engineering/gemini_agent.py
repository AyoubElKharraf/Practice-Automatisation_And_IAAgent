"""Adaptateur Gemini optionnel pour l'Assistant pédagogique."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from agent_local import LocalAgent


class GeminiAgent:
    def __init__(
        self,
        knowledge_base: str | Path,
        model: str | None = None,
    ) -> None:
        self.local = LocalAgent(knowledge_base)
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY est absente. Configurez-la dans PowerShell avant --gemini."
            )
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
        self.endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        self.system_prompt = (
            Path(__file__).parent / "prompts" / "prompt_systeme.md"
        ).read_text(encoding="utf-8")

    def respond(self, request: str, json_output: bool = False) -> dict[str, Any] | str:
        classification, passages = self.local.retrieve(request)
        context = "\n\n".join(
            f"[{passage.source}]\n{passage.text}" for passage in passages[:5]
        )
        context = context or (
            "Aucun passage pertinent. Tu dois indiquer que l'information est "
            "absente et ne rien inventer."
        )
        output_instruction = (
            "Retourne uniquement un objet JSON valide avec exactement les clés "
            "categorie, intention, priorite, reponse et source."
            if json_output
            else "Réponds avec les rubriques Réponse directe, Explication / étapes, "
            "Source documentaire et Information manquante / suite."
        )
        prompt = (
            f"{self.system_prompt}\n\n"
            f"Question étudiante : {request}\n\n"
            f"Passages récupérés et validés :\n{context}\n\n"
            f"{output_instruction}"
        )
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1},
        }).encode("utf-8")
        request_data = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        body: dict[str, Any] | None = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request_data, timeout=60) as response:
                    body = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as error:
                if error.code == 503 and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                detail = ""
                try:
                    error_body = json.loads(error.read().decode("utf-8"))
                    detail = error_body.get("error", {}).get("message", "")
                except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                    pass
                suffix = f" Détail Gemini : {detail}" if detail else ""
                raise RuntimeError(
                    f"Gemini a refusé la requête ({error.code}).{suffix}"
                ) from error
            except urllib.error.URLError as error:
                raise RuntimeError(f"Impossible de joindre Gemini : {error.reason}") from error
            except TimeoutError as error:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(
                    "Gemini n'a pas répondu dans le délai imparti après trois tentatives."
                ) from error
        if body is None:
            raise RuntimeError("Gemini n'a retourné aucune réponse.")
        try:
            content = body["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError("Réponse Gemini invalide : contenu absent.") from error
        if not json_output:
            return {
                "categorie": classification["categorie"],
                "intention": request,
                "priorite": classification["priorite"],
                "reponse": content,
                "source": "; ".join(passage.source for passage in passages[:5]),
                "information_manquante": "Voir la réponse du modèle.",
            }
        try:
            result = json.loads(content)
        except json.JSONDecodeError as error:
            raise RuntimeError("Gemini n'a pas retourné un JSON valide.") from error
        required = {"categorie", "intention", "priorite", "reponse", "source"}
        if set(result) != required:
            raise RuntimeError("Le JSON Gemini ne contient pas exactement les cinq clés requises.")
        return content
