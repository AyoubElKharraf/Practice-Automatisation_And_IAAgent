"""Interface graphique pour exécuter les parties du TP6 en parallèle."""

from __future__ import annotations

import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from tkinter import scrolledtext, ttk


PROJECT_DIR = Path(__file__).resolve().parent
SCRIPTS = (
    ("Partie 1", "partie1_env.py"),
    ("Partie 2", "partie2_llm.py"),
    ("Partie 4", "partie4_memory.py"),
    ("Parties 5-6", "partie5_6_agent.py"),
)


@dataclass(frozen=True)
class ExecutionResult:
    title: str
    script: str
    return_code: int
    output: str
    duration: float


class TP6Interface(tk.Tk):
    """Fenêtre de pilotage et de suivi des scripts du TP6."""

    def __init__(self) -> None:
        super().__init__()
        self.title("TP6 • Agentic AI — Console d'exécution")
        self.geometry("1180x760")
        self.minsize(900, 600)
        self.configure(bg="#0f172a")

        self.events: queue.Queue[ExecutionResult | tuple[str, str]] = queue.Queue()
        self.cards: dict[str, tuple[tk.Label, tk.Label, scrolledtext.ScrolledText]] = {}
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=len(SCRIPTS))

        self._configure_style()
        self._build_header()
        self._build_dashboard()
        self.after(100, self._consume_events)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Run.TButton", font=("Segoe UI", 11, "bold"), padding=(18, 10))
        style.configure("Header.TLabel", background="#0f172a", foreground="#f8fafc")
        style.configure("Muted.TLabel", background="#0f172a", foreground="#94a3b8")

    def _build_header(self) -> None:
        header = tk.Frame(self, bg="#0f172a")
        header.pack(fill="x", padx=28, pady=(24, 12))

        title = tk.Label(
            header,
            text="TP6  /  Agentic AI",
            font=("Segoe UI", 24, "bold"),
            bg="#0f172a",
            fg="#f8fafc",
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            header,
            text="Exécution parallèle • LLM • mémoire conversationnelle • outils",
            font=("Segoe UI", 11),
            bg="#0f172a",
            fg="#94a3b8",
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        actions = tk.Frame(header, bg="#0f172a")
        actions.pack(fill="x", pady=(18, 0))
        self.run_button = ttk.Button(
            actions,
            text="▶  Exécuter toutes les parties",
            style="Run.TButton",
            command=self._start_execution,
        )
        self.run_button.pack(side="left")

        self.status = tk.Label(
            actions,
            text="Prêt à lancer",
            font=("Segoe UI", 10),
            bg="#0f172a",
            fg="#38bdf8",
        )
        self.status.pack(side="left", padx=18)

    def _build_dashboard(self) -> None:
        container = tk.Frame(self, bg="#0f172a")
        container.pack(fill="both", expand=True, padx=28, pady=(8, 24))

        for column in range(2):
            container.columnconfigure(column, weight=1)
        for row in range(2):
            container.rowconfigure(row, weight=1)

        for index, (title, script) in enumerate(SCRIPTS):
            card = tk.Frame(
                container,
                bg="#1e293b",
                highlightbackground="#334155",
                highlightthickness=1,
            )
            card.grid(
                row=index // 2,
                column=index % 2,
                sticky="nsew",
                padx=(0 if index % 2 == 0 else 8, 8 if index % 2 == 0 else 0),
                pady=(0 if index < 2 else 8, 8 if index < 2 else 0),
            )
            card.rowconfigure(2, weight=1)
            card.columnconfigure(0, weight=1)

            title_label = tk.Label(
                card,
                text=title,
                font=("Segoe UI", 13, "bold"),
                bg="#1e293b",
                fg="#f8fafc",
                anchor="w",
            )
            title_label.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 2))

            state_label = tk.Label(
                card,
                text=f"{script}  •  En attente",
                font=("Segoe UI", 9),
                bg="#1e293b",
                fg="#94a3b8",
                anchor="w",
            )
            state_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

            output = scrolledtext.ScrolledText(
                card,
                wrap=tk.WORD,
                height=11,
                state="disabled",
                font=("Cascadia Mono", 9),
                bg="#0f172a",
                fg="#cbd5e1",
                insertbackground="#f8fafc",
                relief="flat",
                padx=10,
                pady=8,
            )
            output.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
            self.cards[script] = (title_label, state_label, output)

    def _start_execution(self) -> None:
        if self.running:
            return

        self.running = True
        self.run_button.configure(state="disabled")
        self.status.configure(text="Exécution en cours…", fg="#fbbf24")
        for _, script in SCRIPTS:
            _, state, output = self.cards[script]
            state.configure(text=f"{script}  •  En cours…", fg="#fbbf24")
            output.configure(state="normal")
            output.delete("1.0", tk.END)
            output.insert(tk.END, "Démarrage du script…\n")
            output.configure(state="disabled")

        for title, script in SCRIPTS:
            self.executor.submit(self._run_script, title, script)

    def _run_script(self, title: str, script: str) -> None:
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
            result = ExecutionResult(
                title=title,
                script=script,
                return_code=process.returncode,
                output=output.strip(),
                duration=time.perf_counter() - started,
            )
            self.events.put(result)
        except OSError as error:
            self.events.put(
                ExecutionResult(
                    title=title,
                    script=script,
                    return_code=-1,
                    output=f"Impossible de lancer le script : {error}",
                    duration=time.perf_counter() - started,
                )
            )

    def _consume_events(self) -> None:
        completed = 0
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break

            if isinstance(event, ExecutionResult):
                completed += 1
                _, state, output = self.cards[event.script]
                success = event.return_code == 0
                state.configure(
                    text=(
                        f"{event.script}  •  {'Terminé avec succès' if success else 'Échec'}"
                        f"  •  {event.duration:.1f}s"
                    ),
                    fg="#4ade80" if success else "#f87171",
                )
                output.configure(state="normal")
                output.delete("1.0", tk.END)
                output.insert(tk.END, event.output or "(Aucune sortie)")
                output.configure(state="disabled")

        if completed:
            remaining = sum(
                1
                for _, script in SCRIPTS
                if "En cours" in self.cards[script][1].cget("text")
            )
            if remaining == 0:
                successes = sum(
                    1
                    for _, script in SCRIPTS
                    if "succès" in self.cards[script][1].cget("text")
                )
                self.running = False
                self.run_button.configure(state="normal")
                self.status.configure(
                    text=f"Terminé • {successes}/{len(SCRIPTS)} scripts réussis",
                    fg="#4ade80" if successes == len(SCRIPTS) else "#fbbf24",
                )

        self.after(100, self._consume_events)

    def _close(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.destroy()


if __name__ == "__main__":
    TP6Interface().mainloop()
