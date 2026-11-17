"""Interface web locale pour le TP6 et conversation avec l'agent."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from partie5_6_agent import create_agent_react


PROJECT_DIR = Path(__file__).resolve().parent
HOST = "127.0.0.1"
SCRIPTS = (
    ("Partie 1", "partie1_env.py"),
    ("Partie 2", "partie2_llm.py"),
    ("Partie 4", "partie4_memory.py"),
    ("Parties 5-6", "partie5_6_agent.py"),
)
RUN_LOCK = threading.Lock()
CHAT_LOCK = threading.Lock()
CHAT_AGENT = None


class RateLimitExceeded(RuntimeError):
    """Indique que le quota de génération du fournisseur est atteint."""


class InvalidApiKey(RuntimeError):
    """Indique que la clé du fournisseur est invalide ou révoquée."""


class ModelNotAllowed(RuntimeError):
    """Indique que le modèle n'est pas autorisé pour le projet."""


def is_rate_limit_error(message: str) -> bool:
    lowered = message.lower()
    return "rate_limit_exceeded" in lowered or "tokens per day" in lowered


def is_invalid_key_error(message: str) -> bool:
    lowered = message.lower()
    return "invalid_api_key" in lowered or "invalid api key" in lowered


def is_model_permission_error(message: str) -> bool:
    lowered = message.lower()
    return "model_permission_blocked" in lowered


def rate_limit_message() -> str:
    return (
        "Quota Groq atteint (limite quotidienne de tokens). "
        "Attendez le délai indiqué par Groq ou utilisez une autre clé/modèle."
    )


def invalid_key_message() -> str:
    return (
        "Clé API Groq invalide ou révoquée. "
        "Créez une nouvelle clé dans la console Groq, remplacez GROQ_API_KEY "
        "dans .env, puis redémarrez l'interface."
    )


def model_permission_message() -> str:
    return (
        "Le modèle configuré n'est pas autorisé par le projet Groq. "
        "Dans Project > Limits, autorisez le modèle indiqué dans .env "
        "ou supprimez la restriction du projet pour hériter des modèles de l'organisation."
    )


def run_script(title: str, script: str) -> dict[str, object]:
    started = time.perf_counter()
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        process = subprocess.run(
            [sys.executable, "-u", script],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creation_flags,
            check=False,
        )
        output = process.stdout
        if process.stderr:
            output += "\n[stderr]\n" + process.stderr
        if process.returncode != 0 and is_rate_limit_error(output):
            output = rate_limit_message()
        elif process.returncode != 0 and is_invalid_key_error(output):
            output = invalid_key_message()
        elif process.returncode != 0 and is_model_permission_error(output):
            output = model_permission_message()
        return {
            "title": title,
            "script": script,
            "success": process.returncode == 0,
            "return_code": process.returncode,
            "duration": round(time.perf_counter() - started, 1),
            "output": output.strip(),
        }
    except OSError as error:
        return {
            "title": title,
            "script": script,
            "success": False,
            "return_code": -1,
            "duration": round(time.perf_counter() - started, 1),
            "output": f"Impossible de lancer le script : {error}",
        }


def run_all() -> list[dict[str, object]]:
    with ThreadPoolExecutor(max_workers=len(SCRIPTS)) as executor:
        futures = [
            executor.submit(run_script, title, script)
            for title, script in SCRIPTS
        ]
        return [future.result() for future in futures]


def get_chat_agent():
    global CHAT_AGENT
    if CHAT_AGENT is None:
        CHAT_AGENT = create_agent_react()
    return CHAT_AGENT


def chat_with_agent(message: str) -> str:
    if not message.strip():
        raise ValueError("Le message ne peut pas être vide.")
    try:
        with CHAT_LOCK:
            result = get_chat_agent().invoke({"input": message.strip()})
    except Exception as error:
        if is_rate_limit_error(str(error)) or type(error).__name__ == "RateLimitError":
            raise RateLimitExceeded(rate_limit_message()) from error
        if is_invalid_key_error(str(error)) or type(error).__name__ == "AuthenticationError":
            raise InvalidApiKey(invalid_key_message()) from error
        if is_model_permission_error(str(error)):
            raise ModelNotAllowed(model_permission_message()) from error
        raise
    return str(result["output"])


PAGE = r"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TP6 · Agentic AI</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0b1120;
      --panel: #111c33;
      --panel-2: #17233d;
      --border: #263858;
      --text: #f8fafc;
      --muted: #91a4c4;
      --blue: #38bdf8;
      --green: #4ade80;
      --red: #fb7185;
      --yellow: #fbbf24;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: radial-gradient(circle at 15% 0%, #172554 0, var(--bg) 42%);
      color: var(--text);
      font: 15px/1.5 Inter, ui-sans-serif, system-ui, sans-serif;
    }
    .shell { max-width: 1280px; margin: auto; padding: 42px 28px 56px; }
    .eyebrow { color: var(--blue); font-size: 12px; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; }
    h1 { margin: 8px 0 6px; font-size: clamp(30px, 5vw, 52px); letter-spacing: -.04em; }
    .intro { color: var(--muted); max-width: 720px; margin: 0; font-size: 16px; }
    .toolbar { display: flex; align-items: center; gap: 16px; margin: 30px 0 24px; }
    button {
      border: 0; border-radius: 12px; padding: 13px 20px; color: #082f49;
      background: linear-gradient(135deg, #7dd3fc, #38bdf8); cursor: pointer;
      font-weight: 800; box-shadow: 0 8px 24px #0284c733;
    }
    button:hover { filter: brightness(1.08); transform: translateY(-1px); }
    button:disabled { cursor: wait; opacity: .6; transform: none; }
    #summary { color: var(--muted); }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
    .card { overflow: hidden; border: 1px solid var(--border); border-radius: 16px; background: #111c33dd; box-shadow: 0 16px 40px #02061766; }
    .card-head { display: flex; justify-content: space-between; gap: 12px; padding: 18px 20px 14px; background: var(--panel-2); }
    .card h2 { margin: 0; font-size: 17px; }
    .meta { margin-top: 3px; color: var(--muted); font: 12px ui-monospace, monospace; }
    .badge { height: fit-content; border-radius: 99px; padding: 3px 9px; color: var(--muted); background: #243452; font-size: 12px; white-space: nowrap; }
    .badge.running { color: var(--yellow); background: #713f1233; }
    .badge.success { color: var(--green); background: #14532d55; }
    .badge.error { color: var(--red); background: #7f1d1d55; }
    .chat { margin: 24px 0; border: 1px solid var(--border); border-radius: 16px; overflow: hidden; background: #111c33dd; }
    .chat-head { display: flex; justify-content: space-between; align-items: center; padding: 18px 20px; background: var(--panel-2); }
    .chat-head h2 { margin: 0; font-size: 18px; }
    .chat-head p { margin: 3px 0 0; color: var(--muted); font-size: 13px; }
    .reset { padding: 8px 12px; color: var(--muted); background: #243452; box-shadow: none; font-size: 12px; }
    .messages { display: flex; flex-direction: column; gap: 12px; min-height: 160px; max-height: 430px; overflow-y: auto; padding: 20px; }
    .message { max-width: 82%; padding: 11px 14px; border-radius: 13px; white-space: pre-wrap; word-break: break-word; }
    .message.user { align-self: flex-end; color: #082f49; background: #7dd3fc; border-bottom-right-radius: 3px; }
    .message.agent { align-self: flex-start; color: #dbeafe; background: #223253; border-bottom-left-radius: 3px; }
    .message.system { align-self: center; color: var(--muted); font-size: 13px; }
    .chat-form { display: flex; gap: 10px; padding: 14px; border-top: 1px solid var(--border); background: var(--panel-2); }
    .chat-form input { flex: 1; min-width: 0; border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; outline: none; color: var(--text); background: var(--bg); font: inherit; }
    .chat-form input:focus { border-color: var(--blue); box-shadow: 0 0 0 3px #38bdf822; }
    .send { padding: 11px 16px; }
    pre { min-height: 190px; max-height: 330px; overflow: auto; margin: 0; padding: 16px 20px; color: #cbd5e1; background: var(--bg); font: 12px/1.6 "Cascadia Mono", Consolas, monospace; white-space: pre-wrap; word-break: break-word; }
    @media (max-width: 800px) { .shell { padding: 28px 16px; } .grid { grid-template-columns: 1fr; } .toolbar { align-items: flex-start; flex-direction: column; } }
  </style>
</head>
<body>
  <main class="shell">
    <div class="eyebrow">Master M2I · TP6</div>
    <h1>Agentic AI <span style="color: var(--blue)">/</span> Console</h1>
    <p class="intro">Lancez les parties du TP en parallèle et visualisez immédiatement les résultats du LLM, de la mémoire et des outils.</p>
    <div class="toolbar">
      <button id="run" onclick="runAll()">▶&nbsp; Exécuter toutes les parties</button>
      <span id="summary">Prêt à lancer</span>
    </div>
    <section class="chat">
      <div class="chat-head">
        <div>
          <h2>Conversation avec l’agent</h2>
          <p>L’agent conserve le contexte et choisit automatiquement la mémoire ou les outils.</p>
        </div>
        <button class="reset" onclick="resetChat()">Nouvelle conversation</button>
      </div>
      <div id="messages" class="messages">
        <div class="message system">Essayez : « Calcule 12 + 8 », puis « Rappelle-moi le résultat ».</div>
      </div>
      <form class="chat-form" onsubmit="sendMessage(event)">
        <input id="chat-input" autocomplete="off" placeholder="Écrivez votre demande à l’agent…" />
        <button id="send" class="send" type="submit">Envoyer</button>
      </form>
    </section>
    <section id="cards" class="grid"></section>
  </main>
  <script>
    const scripts = [
      ["Partie 1", "partie1_env.py"],
      ["Partie 2", "partie2_llm.py"],
      ["Partie 4", "partie4_memory.py"],
      ["Parties 5-6", "partie5_6_agent.py"]
    ];
    const cards = document.getElementById("cards");
    const summary = document.getElementById("summary");
    const button = document.getElementById("run");
    const messages = document.getElementById("messages");
    const chatInput = document.getElementById("chat-input");
    const sendButton = document.getElementById("send");

    function addMessage(text, role) {
      const message = document.createElement("div");
      message.className = `message ${role}`;
      message.textContent = text;
      messages.appendChild(message);
      messages.scrollTop = messages.scrollHeight;
    }

    async function sendMessage(event) {
      event.preventDefault();
      const text = chatInput.value.trim();
      if (!text || sendButton.disabled) return;
      addMessage(text, "user");
      chatInput.value = "";
      sendButton.disabled = true;
      chatInput.disabled = true;
      addMessage("L’agent réfléchit…", "system");
      const thinking = messages.lastElementChild;
      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({message: text})
        });
        const payload = await response.json();
        thinking.remove();
        if (!response.ok) throw new Error(payload.error || "Erreur serveur");
        addMessage(payload.response, "agent");
      } catch (error) {
        thinking.remove();
        addMessage(`Erreur : ${error.message}`, "system");
      } finally {
        sendButton.disabled = false;
        chatInput.disabled = false;
        chatInput.focus();
      }
    }

    async function resetChat() {
      await fetch("/api/chat/reset", {method: "POST"});
      messages.innerHTML = "";
      addMessage("Nouvelle conversation. La mémoire de l’agent a été réinitialisée.", "system");
      chatInput.focus();
    }

    function renderCards(results = {}) {
      cards.innerHTML = scripts.map(([title, script]) => {
        const result = results[script] || {};
        const state = result.success === true ? "success" : result.success === false ? "error" : "";
        const label = result.success === true ? `Réussi · ${result.duration}s` :
          result.success === false ? `Échec · ${result.duration}s` : "En attente";
        const output = result.output || "Aucun résultat pour le moment.";
        return `<article class="card">
          <div class="card-head">
            <div><h2>${title}</h2><div class="meta">${script}</div></div>
            <span class="badge ${state}">${label}</span>
          </div>
          <pre>${escapeHtml(output)}</pre>
        </article>`;
      }).join("");
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, char => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
      }[char]));
    }

    async function runAll() {
      button.disabled = true;
      summary.textContent = "Exécution parallèle en cours…";
      const running = Object.fromEntries(scripts.map(([, script]) => [script, {
        success: undefined, output: "Exécution en cours…"
      }]));
      renderCards(running);
      try {
        const response = await fetch("/api/run", { method: "POST" });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "Erreur serveur");
        const results = Object.fromEntries(payload.results.map(item => [item.script, item]));
        renderCards(results);
        const successful = payload.results.filter(item => item.success).length;
        summary.textContent = `Terminé · ${successful}/${payload.results.length} scripts réussis`;
      } catch (error) {
        summary.textContent = `Erreur : ${error.message}`;
      } finally {
        button.disabled = false;
      }
    }

    renderCards();
  </script>
</body>
</html>"""


class WebHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("Le corps de la requête doit être un JSON valide.") from error
        if not isinstance(payload, dict):
            raise ValueError("Le corps de la requête doit être un objet JSON.")
        return payload

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/":
            self._send(HTTPStatus.OK, "text/html; charset=utf-8", PAGE.encode("utf-8"))
        else:
            self._send(HTTPStatus.NOT_FOUND, "text/plain; charset=utf-8", b"Not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/chat":
            try:
                payload = self._read_json()
                message = payload.get("message")
                if not isinstance(message, str):
                    raise ValueError("Le champ 'message' est obligatoire.")
                response = chat_with_agent(message)
                body = json.dumps({"response": response}, ensure_ascii=False).encode("utf-8")
                self._send(HTTPStatus.OK, "application/json; charset=utf-8", body)
            except RateLimitExceeded as error:
                body = json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8")
                self._send(HTTPStatus.TOO_MANY_REQUESTS, "application/json; charset=utf-8", body)
            except InvalidApiKey as error:
                body = json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8")
                self._send(HTTPStatus.UNAUTHORIZED, "application/json; charset=utf-8", body)
            except ModelNotAllowed as error:
                body = json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8")
                self._send(HTTPStatus.FORBIDDEN, "application/json; charset=utf-8", body)
            except ValueError as error:
                body = json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8")
                self._send(HTTPStatus.BAD_REQUEST, "application/json; charset=utf-8", body)
            except Exception as error:
                body = json.dumps({"error": f"Erreur de l'agent : {error}"}, ensure_ascii=False).encode("utf-8")
                self._send(HTTPStatus.INTERNAL_SERVER_ERROR, "application/json; charset=utf-8", body)
            return

        if path == "/api/chat/reset":
            global CHAT_AGENT
            with CHAT_LOCK:
                CHAT_AGENT = None
            self._send(HTTPStatus.OK, "application/json", b'{"ok":true}')
            return

        if path != "/api/run":
            self._send(HTTPStatus.NOT_FOUND, "application/json", b'{"error":"Not found"}')
            return
        if not RUN_LOCK.acquire(blocking=False):
            body = json.dumps({"error": "Une exécution est déjà en cours."}).encode()
            self._send(HTTPStatus.CONFLICT, "application/json", body)
            return
        try:
            results = run_all()
            body = json.dumps({"results": results}, ensure_ascii=False).encode("utf-8")
            self._send(HTTPStatus.OK, "application/json; charset=utf-8", body)
        finally:
            RUN_LOCK.release()

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Lance l'interface web du TP6.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    server = ThreadingHTTPServer((HOST, args.port), WebHandler)
    url = f"http://{HOST}:{args.port}"
    print(f"Interface disponible sur {url}")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt de l'interface.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
