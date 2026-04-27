"""Map file extensions to tree-sitter language grammars."""

from __future__ import annotations

from pathlib import Path

EXTENSION_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".cs": "c_sharp",
}


def detect_language(path: Path) -> str | None:
    """Return the tree-sitter language name for a file, or None if unsupported."""
    return EXTENSION_MAP.get(path.suffix)
