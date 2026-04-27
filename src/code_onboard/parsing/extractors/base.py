"""Abstract base extractor."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from tree_sitter import Tree

from code_onboard.parsing.models import FileSummary


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, tree: Tree, source: bytes, path: Path) -> FileSummary:
        ...
