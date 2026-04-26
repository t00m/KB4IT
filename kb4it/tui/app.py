#!/usr/bin/env python
"""
KB4IT Terminal User Interface.

Launched automatically when kb4it is run with no arguments in a terminal.
Uses the Rich library for a menu-driven interactive experience.
"""

import argparse
import logging
import os
import sys
import threading
import time
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from kb4it.core.env import ENV
from kb4it.core.util import json_load, json_save

console = Console()

PROJECTS_FILE = Path(ENV["LPATH"]["ROOT"]) / "projects.json"


# ─── Project Registry ──────────────────────────────────────────────────────────

def load_projects() -> list[dict]:
    """Load project list from ~/.kb4it/projects.json."""
    if not PROJECTS_FILE.exists():
        return []
    try:
        data = json_load(str(PROJECTS_FILE))
        return data.get("projects", [])
    except Exception:
        return []


def save_projects(projects: list[dict]) -> None:
    """Persist project list to ~/.kb4it/projects.json."""
    PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    json_save(str(PROJECTS_FILE), {"projects": projects})


# ─── Theme / Apps Helpers ──────────────────────────────────────────────────────

def get_themes() -> list[dict]:
    """Return metadata dicts for all installed themes (global + local)."""
    themes = []
    seen_ids: set[str] = set()
    for scope, base in [
        ("global", ENV["GPATH"]["THEMES"]),
        ("local", ENV["LPATH"]["THEMES"]),
    ]:
        base_path = Path(base)
        if not base_path.exists():
            continue
        for entry in sorted(base_path.iterdir()):
            if not entry.is_dir():
                continue
            tfile = entry / "theme.json"
            if not tfile.exists():
                continue
            try:
                data = json_load(str(tfile))
                tid = data.get("id", entry.name)
                if tid in seen_ids:
                    continue
                seen_ids.add(tid)
                data["_scope"] = scope
                data["_path"] = str(entry)
                themes.append(data)
            except Exception:
                pass
    return themes


def get_apps(theme_name: str) -> list[str]:
    """Return app names available for the given theme."""
    apps = []
    for base in [ENV["GPATH"]["THEMES"], ENV["LPATH"]["THEMES"]]:
        apps_path = Path(base) / theme_name / "apps"
        if not apps_path.exists():
            continue
        for f in sorted(apps_path.glob("*.json")):
            apps.append(f.stem)
    return apps


# ─── UI Helpers ───────────────────────────────────────────────────────────────

def clear() -> None:
    console.clear()


def header() -> None:
    version = ENV["APP"]["version"]
    console.print(
        Panel(
            f"[bold white]KB4IT[/]  v{version}  —  Terminal User Interface",
            style="bold blue",
            box=box.DOUBLE_EDGE,
            padding=(0, 2),
        )
    )


def pause(msg: str = "Press Enter to continue...") -> None:
    console.input(f"\n[dim]{msg}[/]")


def pick_from_list(
    items: list,
    title: str,
    display_fn=None,
    allow_back: bool = True,
) -> int | None:
    """
    Show a numbered list and return the selected 0-based index,
    or None if the user chooses Back / there are no items.
    """
    if not items:
        console.print(f"[yellow]No {title.lower()} found.[/yellow]")
        pause()
        return None

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("#", style="bold cyan", width=4)
    table.add_column("Item")

    for i, item in enumerate(items, 1):
        label = display_fn(item) if display_fn else str(item)
        table.add_row(str(i), label)

    if allow_back:
        table.add_row("[dim]B[/dim]", "[dim]Back[/dim]")

    console.print(Panel(table, title=title, box=box.ROUNDED))

    choices = [str(i) for i in range(1, len(items) + 1)]
    if allow_back:
        choices += ["b", "B"]

    choice = Prompt.ask("Select", choices=choices)
    if choice.lower() == "b":
        return None
    return int(choice) - 1


# ─── Build Progress Tracking ──────────────────────────────────────────────────

class _BuildState:
    """Shared state between the build thread and the TUI progress bar."""

    def __init__(self) -> None:
        self.completed = 0
        self.total = 0
        self.done = threading.Event()
        self.error = False
        self._lock = threading.Lock()

    def on_doc_compiled(self, basename: str, rc: bool) -> None:
        """Called from Compiler.compilation_finished (in a worker thread)."""
        with self._lock:
            self.completed += 1


def _silence_console_log() -> list:
    """
    Remove StreamHandlers writing to stdout/stderr from the root logger
    so they don't interleave with the Rich progress bar.
    Returns the removed handlers so they can be restored later.
    """
    root = logging.getLogger()
    removed = []
    for h in list(root.handlers):
        if isinstance(h, logging.StreamHandler) and h.stream in (sys.stdout, sys.stderr):
            root.removeHandler(h)
            removed.append(h)
    return removed


def _restore_console_log(handlers: list) -> None:
    root = logging.getLogger()
    for h in handlers:
        root.addHandler(h)


def _run_build_thread(config_path: str, force: bool, state: _BuildState) -> None:
    """Build thread target: runs KB4IT and signals when done."""
    from kb4it.core.main import KB4IT
    from kb4it.services import compiler as compiler_mod

    compiler_mod.set_progress_callback(state.on_doc_compiled)
    removed_handlers = []
    try:
        params = argparse.Namespace(
            action="build",
            config=config_path,
            log_level="WARNING",
            force=force,
        )
        app = KB4IT(params)
        # Silence any console log handlers set up by KB4IT
        removed_handlers = _silence_console_log()
        app.run()
    except SystemExit:
        pass
    except Exception as exc:
        state.error = True
        # Print outside the Progress context; will appear once the bar closes
        console.print(f"\n[red]Build error:[/] {exc}")
    finally:
        compiler_mod.clear_progress_callback()
        _restore_console_log(removed_handlers)
        state.done.set()


def run_build(config_path: str, force: bool = False) -> None:
    """Run a KB4IT project build with a Rich live progress display."""
    # Approximate total from source file count
    try:
        repo = json_load(config_path)
        source_path = Path(repo.get("source", ""))
        approx_total = len(list(source_path.glob("*.adoc"))) if source_path.exists() else 0
    except Exception:
        approx_total = 0

    state = _BuildState()
    state.total = approx_total

    label = "[bold yellow]Force compiling[/]" if force else "[bold green]Compiling[/]"

    thread = threading.Thread(
        target=_run_build_thread,
        args=(config_path, force, state),
        daemon=True,
    )
    thread.start()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task_id = progress.add_task(label, total=approx_total or None)

        while not state.done.is_set():
            progress.update(
                task_id,
                completed=state.completed,
                total=state.total if state.total > 0 else None,
            )
            time.sleep(0.1)

        # Final update to show completion
        final_total = max(state.total, state.completed, 1)
        progress.update(
            task_id,
            completed=state.completed,
            total=final_total,
            description="[bold green]Done[/]" if not state.error else "[bold red]Failed[/]",
        )

    thread.join(timeout=5)

    if state.error:
        console.print("[red]Build failed — check the project log for details.[/red]")
    else:
        console.print(
            f"[green]Build complete.[/] {state.completed} document(s) compiled."
        )


# ─── Themes Menu ──────────────────────────────────────────────────────────────

def show_themes() -> None:
    clear()
    header()
    themes = get_themes()

    if not themes:
        console.print("[yellow]No themes found.[/yellow]")
        pause()
        return

    table = Table(title="Installed Themes", box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("ID", style="bold cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Version", justify="center")
    table.add_column("Description")
    table.add_column("Scope", style="dim", justify="center")

    for t in themes:
        table.add_row(
            t.get("id", "?"),
            t.get("name", "?"),
            t.get("version", "?"),
            t.get("description", ""),
            t.get("_scope", "?"),
        )

    console.print(table)
    pause()


# ─── Apps Menu ────────────────────────────────────────────────────────────────

def show_apps() -> None:
    clear()
    header()
    themes = get_themes()

    if not themes:
        console.print("[yellow]No themes installed.[/yellow]")
        pause()
        return

    idx = pick_from_list(
        themes,
        "Select Theme to List Apps",
        display_fn=lambda t: f"[bold]{t.get('id', '?')}[/]  —  {t.get('description', '')}",
    )
    if idx is None:
        return

    theme_id = themes[idx].get("id", "")
    clear()
    header()

    apps = get_apps(theme_id)
    if not apps:
        console.print(f"[yellow]No apps found for theme [bold]{theme_id}[/bold].[/yellow]")
    else:
        table = Table(
            title=f"Apps for theme '{theme_id}'",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold",
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("App Name", style="bold cyan")

        for i, app in enumerate(apps, 1):
            table.add_row(str(i), app)

        console.print(table)

    pause()


# ─── Create Project ───────────────────────────────────────────────────────────

def create_project() -> dict | None:
    """Wizard that initializes a new KB4IT repository and registers it."""
    clear()
    header()
    themes = get_themes()

    if not themes:
        console.print("[yellow]No themes installed — cannot create a project.[/yellow]")
        pause()
        return None

    console.print(Panel("[bold]Create a New Project[/]", box=box.ROUNDED, style="green"))

    # Select theme
    idx = pick_from_list(
        themes,
        "Choose a Theme",
        display_fn=lambda t: f"[bold]{t.get('id', '?')}[/]  —  {t.get('description', '')}",
    )
    if idx is None:
        return None

    theme_id = themes[idx].get("id", "")

    # Display name for the registry
    name = Prompt.ask("\nProject display name").strip()
    if not name:
        console.print("[red]Project name cannot be empty.[/red]")
        pause()
        return None

    # Directory where the repo will be initialised
    default_path = str(Path.home() / "Documents" / name.replace(" ", "_"))
    repo_path = Prompt.ask("Repository path", default=default_path)
    repo_path = os.path.expanduser(repo_path.strip())

    console.print(
        f"\nCreating project [bold]{name}[/] "
        f"with theme [cyan]{theme_id}[/] "
        f"at [dim]{repo_path}[/dim] …"
    )

    try:
        from kb4it.core.main import KB4IT

        params = argparse.Namespace(
            action="create",
            theme=theme_id,
            repo_path=repo_path,
            log_level="WARNING",
        )
        removed = _silence_console_log()
        try:
            app = KB4IT(params)
            app.run()
        except SystemExit:
            pass
        finally:
            _restore_console_log(removed)
    except Exception as exc:
        console.print(f"[red]Error creating project:[/] {exc}")
        pause()
        return None

    config_path = str(Path(repo_path) / "config" / "repo.json")
    if not Path(config_path).exists():
        console.print(
            f"[red]Project creation failed — config not found at[/]\n  {config_path}"
        )
        pause()
        return None

    console.print(f"[green]Project created![/]  Config: [dim]{config_path}[/dim]")
    pause()
    return {"name": name, "config": config_path}


# ─── Delete Project ───────────────────────────────────────────────────────────

def delete_project(projects: list[dict]) -> list[dict]:
    """Remove a project from the registry (files on disk are untouched)."""
    clear()
    header()

    if not projects:
        console.print("[yellow]No projects configured.[/yellow]")
        pause()
        return projects

    idx = pick_from_list(
        projects,
        "Delete Project from Registry",
        display_fn=lambda p: p["name"],
    )
    if idx is None:
        return projects

    project = projects[idx]
    confirmed = Confirm.ask(
        f"Remove [bold]{project['name']}[/] from the registry?\n"
        "  (Files on disk are NOT deleted)"
    )
    if confirmed:
        projects = [p for i, p in enumerate(projects) if i != idx]
        save_projects(projects)
        console.print(f"[green]Project '[bold]{project['name']}[/]' removed.[/green]")
    pause()
    return projects


# ─── Project Info ─────────────────────────────────────────────────────────────

def show_project_info(project: dict, config_path: str) -> None:
    clear()
    header()

    try:
        repo = json_load(config_path)
    except Exception as exc:
        console.print(f"[red]Cannot read config:[/] {exc}")
        pause()
        return

    table = Table(
        title=f"Project Info — {project['name']}",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold",
    )
    table.add_column("Key", style="bold cyan", no_wrap=True)
    table.add_column("Value")

    for k in sorted(repo.keys()):
        v = repo[k]
        if isinstance(v, list):
            v = ", ".join(str(x) for x in v)
        elif isinstance(v, dict):
            v = str(v)
        table.add_row(str(k), str(v))

    # Show config path as an extra row
    table.add_row("[dim]config_file[/dim]", f"[dim]{config_path}[/dim]")

    console.print(table)
    pause()


# ─── List Source Files ────────────────────────────────────────────────────────

def list_source_files(config_path: str) -> None:
    clear()
    header()

    try:
        repo = json_load(config_path)
        source_path = Path(repo.get("source", ""))
    except Exception as exc:
        console.print(f"[red]Cannot read config:[/] {exc}")
        pause()
        return

    if not source_path.exists():
        console.print(f"[yellow]Source directory not found:[/]\n  {source_path}")
        pause()
        return

    files = sorted(source_path.glob("*.adoc"))

    table = Table(
        title=f"Source Files — {source_path}",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold",
    )
    table.add_column("#", style="dim", width=5, justify="right")
    table.add_column("Filename", style="bold")
    table.add_column("Size", justify="right", style="dim")

    for i, f in enumerate(files, 1):
        size = f.stat().st_size
        size_str = f"{size:,} B" if size < 1024 else f"{size // 1024} KB"
        table.add_row(str(i), f.name, size_str)

    console.print(table)
    console.print(f"[dim]Total: {len(files)} file(s)[/dim]")
    pause()


# ─── Keys & Values Explorer ───────────────────────────────────────────────────

def _kbdict_path(config_path: str) -> Path | None:
    """Return the path to kbdict.json for a project, or None if not found."""
    try:
        repo = json_load(config_path)
        source_path = Path(repo.get("source", ""))
        db_path = source_path.parent / "var" / "db" / "kbdict.json"
        return db_path if db_path.exists() else None
    except Exception:
        return None


def explore_keys_values(config_path: str) -> None:
    """Interactive explorer: keys → values → documents."""
    db_path = _kbdict_path(config_path)

    if db_path is None:
        clear()
        header()
        console.print(
            "[yellow]No database found.[/]\n"
            "Build the project first to generate the metadata database."
        )
        pause()
        return

    try:
        kbdict = json_load(str(db_path))
    except Exception as exc:
        clear()
        header()
        console.print(f"[red]Cannot read database:[/] {exc}")
        pause()
        return

    metadata: dict = kbdict.get("metadata", {})
    if not metadata:
        clear()
        header()
        console.print("[yellow]No metadata found in the database.[/yellow]")
        pause()
        return

    # ── Key selection loop ──
    while True:
        clear()
        header()
        keys = sorted(metadata.keys())

        idx = pick_from_list(
            keys,
            "Metadata Keys — Select a Key",
            display_fn=lambda k: (
                f"[bold]{k}[/]  "
                f"[dim]({len(metadata.get(k, {}))} value(s))[/dim]"
            ),
        )
        if idx is None:
            break

        selected_key = keys[idx]
        values: dict = metadata[selected_key]

        # ── Value selection loop ──
        while True:
            clear()
            header()
            value_list = sorted(values.keys())

            idx2 = pick_from_list(
                value_list,
                f"Key: [bold]{selected_key}[/] — Select a Value",
                display_fn=lambda v: (
                    f"[bold]{v}[/]  "
                    f"[dim]({len(values.get(v, []))} doc(s))[/dim]"
                ),
            )
            if idx2 is None:
                break

            selected_value = value_list[idx2]
            doc_ids: list = values[selected_value]

            # ── Document list ──
            clear()
            header()
            table = Table(
                title=f"{selected_key} = [bold]{selected_value}[/]",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold",
            )
            table.add_column("#", style="dim", width=5, justify="right")
            table.add_column("Document ID", style="bold cyan")

            for i, doc_id in enumerate(sorted(doc_ids), 1):
                table.add_row(str(i), doc_id)

            console.print(table)
            console.print(f"[dim]{len(doc_ids)} document(s)[/dim]")
            pause()


# ─── Project Submenu ──────────────────────────────────────────────────────────

def project_menu(project: dict) -> None:
    """Submenu for a selected project."""
    config_path = project["config"]

    while True:
        clear()
        header()

        # Load current repo settings for display
        try:
            repo = json_load(config_path)
            repo_title = repo.get("title", project["name"])
            repo_theme = repo.get("theme", "?")
            repo_source = repo.get("source", "?")
            repo_target = repo.get("target", "?")
        except Exception:
            repo_title = project["name"]
            repo_theme = "?"
            repo_source = "?"
            repo_target = "?"

        # Check if database exists (project has been built)
        db_exists = _kbdict_path(config_path) is not None
        db_label = "[green]yes[/]" if db_exists else "[dim]not yet built[/dim]"

        info_text = (
            f"[bold]{repo_title}[/]\n"
            f"Theme: [cyan]{repo_theme}[/]   Built: {db_label}\n"
            f"Source: [dim]{repo_source}[/dim]\n"
            f"Target: [dim]{repo_target}[/dim]"
        )
        console.print(Panel(info_text, title=f"Project: {project['name']}", box=box.ROUNDED))

        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("#", style="bold cyan", width=4)
        table.add_column("Action")

        table.add_row("1", "Compile")
        table.add_row("2", "Force compile  [dim](recompile everything)[/dim]")
        table.add_row("3", "Project info")
        table.add_row("4", "List source files")
        table.add_row("5", "Explore keys & values")
        table.add_row("[dim]B[/dim]", "[dim]Back to main menu[/dim]")

        console.print(table)

        choice = Prompt.ask("Choose", choices=["1", "2", "3", "4", "5", "b", "B"])

        if choice == "1":
            clear()
            header()
            run_build(config_path, force=False)
            pause()
        elif choice == "2":
            clear()
            header()
            run_build(config_path, force=True)
            pause()
        elif choice == "3":
            show_project_info(project, config_path)
        elif choice == "4":
            list_source_files(config_path)
        elif choice == "5":
            explore_keys_values(config_path)
        elif choice.lower() == "b":
            break


# ─── Main Menu ────────────────────────────────────────────────────────────────

def run() -> None:
    """Launch the KB4IT Terminal User Interface."""
    projects = load_projects()

    while True:
        clear()
        header()

        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("#", style="bold cyan", width=4)
        table.add_column("Action")

        proj_count = f"[dim]({len(projects)} configured)[/dim]" if projects else "[dim](none)[/dim]"
        table.add_row("1", f"Select project  {proj_count}")
        table.add_row("2", "Create a new project")
        table.add_row("3", "Delete a project")
        table.add_row("4", "List themes")
        table.add_row("5", "List apps per theme")
        table.add_row("[dim]X[/dim]", "[dim]Exit[/dim]")

        console.print(Panel(table, title="Main Menu", box=box.ROUNDED))

        choices = ["1", "2", "3", "4", "5", "x", "X"]
        try:
            choice = Prompt.ask("Choose", choices=choices)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[blue]Goodbye![/blue]")
            break

        choice = choice.lower()

        if choice == "1":
            if not projects:
                console.print(
                    "[yellow]No projects configured. "
                    "Use option 2 to create one.[/yellow]"
                )
                pause()
                continue
            clear()
            header()
            idx = pick_from_list(
                projects,
                "Select Project",
                display_fn=lambda p: (
                    f"[bold]{p['name']}[/]  [dim]{p.get('config', '')}[/dim]"
                ),
            )
            if idx is not None:
                try:
                    project_menu(projects[idx])
                except KeyboardInterrupt:
                    pass
                projects = load_projects()  # Reload in case of changes

        elif choice == "2":
            try:
                p = create_project()
            except KeyboardInterrupt:
                p = None
            if p:
                projects.append(p)
                save_projects(projects)

        elif choice == "3":
            try:
                projects = delete_project(projects)
            except KeyboardInterrupt:
                pass

        elif choice == "4":
            try:
                show_themes()
            except KeyboardInterrupt:
                pass

        elif choice == "5":
            try:
                show_apps()
            except KeyboardInterrupt:
                pass

        elif choice == "x":
            console.print("\n[blue]Goodbye![/blue]\n")
            break
