"""Data models for parsed AST information."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ImportStmt:
    module: str
    names: list[str] = field(default_factory=list)
    is_relative: bool = False


@dataclass
class FunctionDef:
    name: str
    line: int
    params: list[str] = field(default_factory=list)
    is_method: bool = False
    is_async: bool = False
    is_exported: bool = False


@dataclass
class ClassDef:
    name: str
    line: int
    methods: list[str] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)
    is_exported: bool = False


@dataclass
class CallSite:
    name: str
    line: int


@dataclass
class FileSummary:
    path: Path
    relative_path: str
    language: str
    imports: list[ImportStmt] = field(default_factory=list)
    functions: list[FunctionDef] = field(default_factory=list)
    classes: list[ClassDef] = field(default_factory=list)
    calls: list[CallSite] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    has_main_guard: bool = False
    line_count: int = 0
