"""Adaptateur Groq optionnel pour l'Assistant pédagogique."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from agent_local import LocalAgent


class GroqAgent:
    endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(
        self,
        knowledge_base: str | Path,
        model: str | None = None,
    ) -> None:
        self.local = LocalAgent(knowledge_base)
        self.api_key = os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY est absente. Configurez-la dans PowerShell avant --groq."
            )
        self.model = model or os.environ.get("GROQ_MODEL", "allam-2-7b")
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
        user_content = (
            f"Question étudiante : {request}\n\n"
            f"Passages récupérés et validés :\n{context}\n\n"
            f"{output_instruction}"
        )
        payload = json.dumps({
            "model": self.model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_content},
            ],
        }).encode("utf-8")
        request_data = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request_data, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            error_detail = ""
            try:
                error_body = json.loads(error.read().decode("utf-8"))
                error_detail = error_body.get("error", {}).get("message", "")
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                pass
            suffix = f" Détail Groq : {error_detail}" if error_detail else ""
            if error.code in (401, 403):
                suffix += (
                    " La clé est présente mais refusée par Groq : révoquez-la, "
                    "créez une clé active, acceptez les Model Terms du modèle "
                    "et vérifiez l'accès API du compte."
                )
            raise RuntimeError(
                f"Groq a refusé la requête ({error.code}).{suffix}"
            ) from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"Impossible de joindre Groq : {error.reason}") from error
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError("Réponse Groq invalide : contenu absent.") from error
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
            raise RuntimeError("Groq n'a pas retourné un JSON valide.") from error
        required = {"categorie", "intention", "priorite", "reponse", "source"}
        if set(result) != required:
            raise RuntimeError("Le JSON Groq ne contient pas exactement les cinq clés requises.")
        return content
