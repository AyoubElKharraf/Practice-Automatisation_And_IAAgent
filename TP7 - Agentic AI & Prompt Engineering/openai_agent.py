"""Adaptateur OpenAI Responses API pour l'Assistant pédagogique."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from agent_local import LocalAgent


class OpenAIAgent:
    endpoint = "https://api.openai.com/v1/responses"

    def __init__(
        self,
        knowledge_base: str | Path,
        model: str | None = None,
    ) -> None:
        self.local = LocalAgent(knowledge_base)
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY est absente. Configurez-la dans PowerShell avant --openai."
            )
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-5.4")
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
            f"Question étudiante : {request}\n\n"
            f"Passages récupérés et validés :\n{context}\n\n"
            f"{output_instruction}"
        )
        payload = json.dumps({
            "model": self.model,
            "instructions": self.system_prompt,
            "input": prompt,
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
            detail = ""
            try:
                error_body = json.loads(error.read().decode("utf-8"))
                detail = error_body.get("error", {}).get("message", "")
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                pass
            suffix = f" Détail OpenAI : {detail}" if detail else ""
            raise RuntimeError(f"OpenAI a refusé la requête ({error.code}).{suffix}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"Impossible de joindre OpenAI : {error.reason}") from error
        except TimeoutError as error:
            raise RuntimeError("OpenAI n'a pas répondu dans le délai imparti.") from error
        try:
            content = body["output_text"]
        except (KeyError, TypeError) as error:
            raise RuntimeError("Réponse OpenAI invalide : output_text absent.") from error
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
            raise RuntimeError("OpenAI n'a pas retourné un JSON valide.") from error
        required = {"categorie", "intention", "priorite", "reponse", "source"}
        if set(result) != required:
            raise RuntimeError("Le JSON OpenAI ne contient pas exactement les cinq clés requises.")
        return content
