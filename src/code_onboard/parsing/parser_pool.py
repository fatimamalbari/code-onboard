"""Tree-sitter parser initialization and file parsing orchestrator."""

from __future__ import annotations

from pathlib import Path

import tree_sitter_c_sharp as tscs
import tree_sitter_javascript as tsjs
import tree_sitter_python as tspy
import tree_sitter_typescript as tsts
from tree_sitter import Language, Parser

from code_onboard.discovery.language_detect import detect_language
from code_onboard.parsing.extractors.csharp_extractor import CSharpExtractor
from code_onboard.parsing.extractors.python_extractor import PythonExtractor
from code_onboard.parsing.extractors.ts_extractor import TSExtractor
from code_onboard.parsing.models import FileSummary

_LANGUAGES: dict[str, Language] = {}
_PARSERS: dict[str, Parser] = {}


def _get_language(name: str) -> Language:
    if name not in _LANGUAGES:
        if name == "python":
            _LANGUAGES[name] = Language(tspy.language())
        elif name == "javascript":
            _LANGUAGES[name] = Language(tsjs.language())
        elif name == "typescript":
            _LANGUAGES[name] = Language(tsts.language_typescript())
        elif name == "tsx":
            _LANGUAGES[name] = Language(tsts.language_tsx())
        elif name == "c_sharp":
            _LANGUAGES[name] = Language(tscs.language())
    return _LANGUAGES[name]


def _get_parser(lang_name: str) -> Parser:
    if lang_name not in _PARSERS:
        parser = Parser()
        parser.language = _get_language(lang_name)
        _PARSERS[lang_name] = parser
    return _PARSERS[lang_name]


def _get_extractor(lang_name: str) -> PythonExtractor | TSExtractor | CSharpExtractor:
    if lang_name == "python":
        return PythonExtractor()
    if lang_name == "c_sharp":
        return CSharpExtractor()
    return TSExtractor()


def parse_file(path: Path, repo_root: Path) -> FileSummary | None:
    lang_name = detect_language(path)
    if lang_name is None:
        return None

    try:
        source = path.read_bytes()
    except (OSError, PermissionError):
        return None

    parser = _get_parser(lang_name)
    tree = parser.parse(source)
    extractor = _get_extractor(lang_name)

    summary = extractor.extract(tree, source, path)
    summary.relative_path = str(path.relative_to(repo_root).as_posix())
    summary.language = lang_name
    summary.line_count = source.count(b"\n") + 1

    return summary


def parse_all_files(files: list[Path], repo_root: Path) -> list[FileSummary]:
    results = []
    for f in files:
        summary = parse_file(f, repo_root)
        if summary:
            results.append(summary)
    return results
