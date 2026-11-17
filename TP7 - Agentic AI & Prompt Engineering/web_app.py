"""Interface web locale de l'Assistant pédagogique — Master IA."""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from agent_local import LocalAgent
from env_loader import load_dotenv
from groq_agent import GroqAgent


ROOT = Path(__file__).parent
EXAMPLES = [
    "Quels thèmes sont abordés dans le module ?",
    "Explique-moi ce qu'est un agent IA.",
    "Quel est le numéro de salle ?",
    "La séance de démonstration est-elle maintenue ?",
    "Je n'arrive pas à accéder au support et je ne sais pas si la séance est maintenue.",
    "Quelle est la date de l'examen final ?",
    "Présentez-vous.",
]


def _page() -> str:
    examples = json.dumps(EXAMPLES, ensure_ascii=False)
    return """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Assistant pédagogique — Master IA</title>
  <style>
    :root { color-scheme: light; --ink:#172033; --muted:#667085; --line:#e6eaf0;
      --blue:#2563eb; --soft:#eef4ff; --bg:#f6f8fc; }
    * { box-sizing:border-box; }
    body { margin:0; color:var(--ink); background:var(--bg);
      font:15px/1.55 Inter,Segoe UI,Arial,sans-serif; }
    header { color:white; padding:28px 7vw 34px;
      background:linear-gradient(120deg,#172554,#2563eb); }
    header h1 { margin:0 0 6px; font-size:clamp(24px,4vw,38px); }
    header p { margin:0; opacity:.86; }
    main { width:min(1120px,92vw); margin:-18px auto 40px; }
    .panel { background:white; border:1px solid var(--line); border-radius:18px;
      box-shadow:0 12px 35px #17255412; }
    .examples { padding:20px; margin-bottom:18px; }
    .examples h2 { margin:0 0 12px; font-size:17px; }
    .chips { display:flex; flex-wrap:wrap; gap:9px; }
    .chip { border:1px solid #cbd8f8; background:var(--soft); color:#1e40af;
      border-radius:999px; padding:8px 13px; cursor:pointer; }
    .chip:hover { background:#dbe8ff; }
    .workspace { display:grid; grid-template-columns:1fr 310px; gap:0; min-height:520px; }
    .chat { padding:24px; border-right:1px solid var(--line); }
    .messages { min-height:330px; max-height:520px; overflow:auto; padding:4px; }
    .message { margin:0 0 15px; padding:14px 16px; border-radius:14px; white-space:pre-wrap; }
    .user { margin-left:12%; background:#e9efff; }
    .assistant { margin-right:12%; background:#f7f8fa; border:1px solid var(--line); }
    .empty { color:var(--muted); text-align:center; padding:100px 20px; }
    form { display:flex; gap:10px; margin-top:18px; }
    textarea { flex:1; resize:vertical; min-height:48px; max-height:140px;
      border:1px solid #cdd5e1; border-radius:12px; padding:12px; font:inherit; }
    button.primary { border:0; border-radius:12px; background:var(--blue); color:white;
      padding:0 20px; font-weight:600; cursor:pointer; }
    button:disabled { opacity:.55; cursor:wait; }
    .side { padding:22px; background:#fbfcfe; border-radius:0 18px 18px 0; }
    .side h2 { margin:0 0 16px; font-size:17px; }
    .field { margin-bottom:18px; }
    label { display:block; font-size:13px; color:var(--muted); margin-bottom:6px; }
    select { width:100%; padding:10px; border:1px solid #cdd5e1; border-radius:10px;
      background:white; font:inherit; }
    .meta { border-top:1px solid var(--line); padding-top:14px; color:var(--muted);
      font-size:13px; }
    .meta strong { color:var(--ink); }
    .error { color:#b42318; background:#fff1f0; border:1px solid #f5c2c0;
      padding:10px; border-radius:10px; }
    @media (max-width:760px) {
      .workspace { display:block; }
      .chat { border-right:0; }
      .side { border-radius:0 0 18px 18px; }
      .user,.assistant { margin-left:0; margin-right:0; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Assistant pédagogique — Master IA</h1>
    <p>Recherche documentaire, classification, sources et gestion des limites.</p>
  </header>
  <main>
    <section class="panel examples">
      <h2>Ajouter un document à la session</h2>
      <p class="meta">Formats texte acceptés : .md, .txt, .json, .csv. Le fichier reste en mémoire
        pendant cette session et n'est pas envoyé vers un serveur externe par le moteur local.</p>
      <input id="file" type="file" accept=".md,.txt,.json,.csv,text/plain,text/markdown">
      <span id="upload-status" class="meta"></span>
    </section>
    <section class="panel examples">
      <h2>Requêtes d'exemple à tester</h2>
      <div id="examples" class="chips"></div>
    </section>
    <section class="panel workspace">
      <div class="chat">
        <div id="messages" class="messages">
          <div id="empty" class="empty">Choisissez une requête ci-dessus ou écrivez votre question.</div>
        </div>
        <form id="form">
          <textarea id="question" placeholder="Écrivez votre question..." required></textarea>
          <button class="primary" type="submit">Envoyer</button>
        </form>
      </div>
      <aside class="side">
        <h2>Configuration</h2>
        <div class="field">
          <label for="backend">Moteur</label>
          <select id="backend">
            <option value="local">Local — sans API</option>
            <option value="groq">Groq — API</option>
          </select>
        </div>
        <div class="field">
          <label for="format">Format</label>
          <select id="format">
            <option value="normal">Réponse pédagogique</option>
            <option value="json">JSON structuré</option>
          </select>
        </div>
        <div id="meta" class="meta">Les sources et la catégorie apparaîtront ici.</div>
      </aside>
    </section>
  </main>
  <script>
    const examples = __EXAMPLES__;
    const messages = document.querySelector('#messages');
    const empty = document.querySelector('#empty');
    const question = document.querySelector('#question');
    const form = document.querySelector('#form');
    const meta = document.querySelector('#meta');
    const file = document.querySelector('#file');
    const uploadStatus = document.querySelector('#upload-status');
    document.querySelector('#examples').innerHTML = examples.map((text, i) =>
      `<button class="chip" type="button" data-index="${i}">${text}</button>`).join('');
    document.querySelectorAll('.chip').forEach(button => button.onclick = () => {
      question.value = examples[button.dataset.index]; question.focus();
    });
    file.onchange = async () => {
      const selected = file.files[0];
      if (!selected) return;
      const allowed = ['.md', '.txt', '.json', '.csv'];
      const extension = selected.name.slice(selected.name.lastIndexOf('.')).toLowerCase();
      if (!allowed.includes(extension)) {
        uploadStatus.textContent = 'Format refusé. Utilisez .md, .txt, .json ou .csv.';
        file.value = ''; return;
      }
      if (selected.size > 2 * 1024 * 1024) {
        uploadStatus.textContent = 'Fichier trop volumineux (maximum : 2 Mo).';
        file.value = ''; return;
      }
      uploadStatus.textContent = 'Import en cours...';
      try {
        const content = await selected.text();
        const response = await fetch('/api/upload', {
          method:'POST', headers:{'Content-Type':'application/json'},
          body:JSON.stringify({name:selected.name, content})
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Import impossible');
        uploadStatus.textContent = `${data.name} ajouté (${data.sections} section(s)).`;
      } catch (error) {
        uploadStatus.textContent = `Erreur : ${error.message}`;
      } finally { file.value = ''; }
    };
    function addMessage(text, kind) {
      empty?.remove();
      const item = document.createElement('div');
      item.className = `message ${kind}`;
      item.textContent = text;
      messages.appendChild(item);
      messages.scrollTop = messages.scrollHeight;
    }
    form.onsubmit = async event => {
      event.preventDefault();
      const text = question.value.trim();
      if (!text) return;
      addMessage(text, 'user'); question.value = '';
      const button = form.querySelector('button'); button.disabled = true;
      meta.textContent = 'Analyse, recherche et vérification en cours...';
      try {
        const response = await fetch('/api/respond', {
          method:'POST', headers:{'Content-Type':'application/json'},
          body:JSON.stringify({question:text, backend:document.querySelector('#backend').value,
            json_output:document.querySelector('#format').value === 'json'})
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Erreur serveur');
        addMessage(data.display, 'assistant');
        meta.innerHTML = `<strong>Catégorie :</strong> ${data.category}<br>
          <strong>Source :</strong> ${data.source || 'Aucune source disponible'}<br>
          <strong>Escalade :</strong> ${data.escalation ? 'Oui' : 'Non'}`;
      } catch (error) {
        addMessage(`Erreur : ${error.message}`, 'assistant');
        meta.innerHTML = '<div class="error">La réponse n’a pas pu être obtenue.</div>';
      } finally { button.disabled = false; }
    };
  </script>
</body>
</html>""".replace("__EXAMPLES__", examples)


class AgentHandler(BaseHTTPRequestHandler):
    agent_local: LocalAgent
    agent_groq: GroqAgent | None

    def _send(self, status: HTTPStatus, body: str, content_type: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/":
            self._send(HTTPStatus.OK, _page(), "text/html")
        else:
            self._send(HTTPStatus.NOT_FOUND, "Page introuvable", "text/plain")

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        if route == "/api/upload":
            self._upload()
            return
        if route != "/api/respond":
            self._send(HTTPStatus.NOT_FOUND, "Route introuvable", "text/plain")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            question = str(data.get("question", "")).strip()
            backend = data.get("backend", "local")
            json_output = bool(data.get("json_output", False))
            if not question:
                raise ValueError("La question ne peut pas être vide.")
            if backend == "groq":
                if self.agent_groq is None:
                    raise RuntimeError(
                        "Le backend Groq n’est pas activé. "
                        "Relancez l’interface avec : python web_app.py --groq --port 8765"
                    )
                result = self.agent_groq.respond(question, json_output=json_output)
            else:
                result = self.agent_local.respond(question, json_output=json_output)
            if isinstance(result, str):
                display = result
                category = "JSON"
                source = ""
                escalation = False
            else:
                display = result["reponse"]
                category = str(result["categorie"])
                source = result["source"]
                escalation = result["escalade"]
            self._send(HTTPStatus.OK, json.dumps({
                "display": display,
                "category": category,
                "source": source,
                "escalation": escalation,
            }, ensure_ascii=False), "application/json")
        except (ValueError, json.JSONDecodeError, RuntimeError) as error:
            self._send(HTTPStatus.BAD_REQUEST, json.dumps({"error": str(error)}, ensure_ascii=False), "application/json")

    def _upload(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 2 * 1024 * 1024:
                raise ValueError("Le fichier dépasse la limite de 2 Mo.")
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            name = Path(str(data.get("name", ""))).name
            content = str(data.get("content", ""))
            extension = Path(name).suffix.lower()
            if extension not in {".md", ".txt", ".json", ".csv"}:
                raise ValueError("Format refusé. Utilisez .md, .txt, .json ou .csv.")
            if not name or not content.strip():
                raise ValueError("Le fichier est vide ou son nom est absent.")
            self.agent_local.store.add_text(name, content)
            if self.agent_groq is not None:
                self.agent_groq.local.store.add_text(name, content)
            sections = len(self.agent_local.store._documents[-1][2])
            self._send(HTTPStatus.OK, json.dumps({
                "name": name, "sections": sections,
            }, ensure_ascii=False), "application/json")
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as error:
            self._send(HTTPStatus.BAD_REQUEST, json.dumps({"error": str(error)}, ensure_ascii=False), "application/json")

    def log_message(self, format: str, *args: object) -> None:
        return


def run() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Interface web de l'Assistant pédagogique")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--local", action="store_true", help="Utiliser le moteur local")
    parser.add_argument("--groq", action="store_true", help="Activer le backend Groq")
    args = parser.parse_args()
    AgentHandler.agent_local = LocalAgent(ROOT / "knowledge_base")
    AgentHandler.agent_groq = GroqAgent(ROOT / "knowledge_base") if args.groq else None
    try:
        server = ThreadingHTTPServer((args.host, args.port), AgentHandler)
    except PermissionError:
        print(
            f"Le port {args.port} est déjà utilisé ou interdit. "
            f"Essayez : python web_app.py --local --port 8765"
        )
        return
    except OSError as error:
        print(f"Impossible d'ouvrir le port {args.port} : {error}")
        return
    print(f"Interface disponible sur http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
