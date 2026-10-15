"""
Copy text to the system clipboard.
"""

from __future__ import annotations

from textual.app import App

# Clipboard tools per platform family, in order of preference; each gets the text on stdin.
_CLIPBOARD_TOOLS = {
    "linux": [(["wl-copy"], "utf-8"), (["xclip", "-selection", "clipboard"], "utf-8"),
              (["xsel", "--clipboard", "--input"], "utf-8")],
    "darwin": [(["pbcopy"], "utf-8")],
    # clip.exe reads UTF-16LE with a byte order mark; other encodings garble accents.
    "windows": [(["clip.exe"], "utf-16")],
}


def clipboard_commands(family: str | None = None) -> list[tuple[list[str], str]]:
    """Clipboard commands available on PATH for this platform family."""
    import shutil

    from kb4it.core.env import platform_family
    family = family or platform_family()
    return [(cmd, enc) for cmd, enc in _CLIPBOARD_TOOLS.get(family, _CLIPBOARD_TOOLS["linux"])
            if shutil.which(cmd[0])]


def _copy_to_clipboard(app: App, text: str) -> tuple[bool, str]:
    """Copy text to the system clipboard with the platform's tool, falling back to OSC 52."""
    import subprocess
    for cmd, encoding in clipboard_commands():
        try:
            subprocess.run(cmd, input=text.encode(encoding), check=True, timeout=2)
            return True, cmd[0]
        except Exception:
            continue
    try:
        app.copy_to_clipboard(text)
        return True, "OSC52"
    except Exception as exc:
        return False, str(exc)
