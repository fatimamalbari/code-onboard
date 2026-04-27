"""Extract symbols from Python source using tree-sitter."""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Node, Tree

from code_onboard.parsing.extractors.base import BaseExtractor
from code_onboard.parsing.models import (
    CallSite,
    ClassDef,
    FileSummary,
    FunctionDef,
    ImportStmt,
)


class PythonExtractor(BaseExtractor):
    def extract(self, tree: Tree, source: bytes, path: Path) -> FileSummary:
        summary = FileSummary(path=path, relative_path="", language="python")
        self._walk(tree.root_node, summary, source, is_top_level=True)
        summary.has_main_guard = b'if __name__ == "__main__"' in source or b"if __name__ == '__main__'" in source
        return summary

    def _walk(self, node: Node, summary: FileSummary, source: bytes, is_top_level: bool) -> None:
        for child in node.children:
            if child.type == "import_statement":
                self._extract_import(child, summary, source)
            elif child.type == "import_from_statement":
                self._extract_from_import(child, summary, source)
            elif child.type == "function_definition":
                self._extract_function(child, summary, source, is_top_level)
            elif child.type == "class_definition":
                self._extract_class(child, summary, source)
            elif child.type == "call":
                self._extract_call(child, summary, source)
            elif child.type in ("expression_statement", "if_statement", "for_statement",
                                "while_statement", "with_statement", "try_statement"):
                self._walk(child, summary, source, is_top_level=False)

    def _text(self, node: Node, source: bytes) -> str:
        return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

    def _extract_import(self, node: Node, summary: FileSummary, source: bytes) -> None:
        for child in node.children:
            if child.type == "dotted_name":
                summary.imports.append(ImportStmt(module=self._text(child, source)))

    def _extract_from_import(self, node: Node, summary: FileSummary, source: bytes) -> None:
        module = ""
        names: list[str] = []
        is_relative = False
        past_import_keyword = False

        for child in node.children:
            if child.type == "import":
                past_import_keyword = True
            elif child.type == "relative_import":
                is_relative = True
                for sub in child.children:
                    if sub.type == "dotted_name":
                        module = self._text(sub, source)
            elif child.type == "import_prefix":
                is_relative = True
            elif child.type == "dotted_name":
                if not past_import_keyword:
                    module = self._text(child, source)
                else:
                    names.append(self._text(child, source).split(" as ")[0])
            elif child.type == "aliased_import":
                name_node = child.child_by_field_name("name") or child
                names.append(self._text(name_node, source).split(" as ")[0])
            elif child.type == "import_list":
                for item in child.children:
                    if item.type == "dotted_name":
                        names.append(self._text(item, source).split(" as ")[0])
                    elif item.type == "aliased_import":
                        name_node = item.child_by_field_name("name") or item
                        text = self._text(name_node, source).split(" as ")[0]
                        if text.strip():
                            names.append(text)

        summary.imports.append(ImportStmt(module=module, names=names, is_relative=is_relative))

    def _extract_function(self, node: Node, summary: FileSummary, source: bytes, is_top_level: bool) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return

        params: list[str] = []
        params_node = node.child_by_field_name("parameters")
        if params_node:
            for p in params_node.children:
                if p.type in ("identifier", "typed_parameter", "default_parameter",
                              "typed_default_parameter", "list_splat_pattern",
                              "dictionary_splat_pattern"):
                    pname = p.child_by_field_name("name") or p
                    name = self._text(pname, source)
                    if name not in ("self", "cls", "(", ")", ","):
                        params.append(name)

        is_async = any(c.type == "async" for c in node.parent.children) if node.parent else False

        summary.functions.append(FunctionDef(
            name=self._text(name_node, source),
            line=node.start_point[0] + 1,
            params=params,
            is_method=not is_top_level,
            is_async=is_async,
        ))

        # Walk body for calls
        body = node.child_by_field_name("body")
        if body:
            self._walk_for_calls(body, summary, source)

    def _extract_class(self, node: Node, summary: FileSummary, source: bytes) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return

        bases: list[str] = []
        superclasses = node.child_by_field_name("superclasses")
        if superclasses:
            for child in superclasses.children:
                if child.type in ("identifier", "attribute"):
                    bases.append(self._text(child, source))

        methods: list[str] = []
        body = node.child_by_field_name("body")
        if body:
            for child in body.children:
                if child.type == "function_definition":
                    mn = child.child_by_field_name("name")
                    if mn:
                        methods.append(self._text(mn, source))
                    self._extract_function(child, summary, source, is_top_level=False)

        summary.classes.append(ClassDef(
            name=self._text(name_node, source),
            line=node.start_point[0] + 1,
            methods=methods,
            bases=bases,
        ))

    def _extract_call(self, node: Node, summary: FileSummary, source: bytes) -> None:
        func = node.child_by_field_name("function")
        if func:
            name = self._text(func, source)
            # Simplify attribute calls: keep last part
            if "." in name:
                name = name.split(".")[-1]
            summary.calls.append(CallSite(name=name, line=node.start_point[0] + 1))

    def _walk_for_calls(self, node: Node, summary: FileSummary, source: bytes) -> None:
        for child in node.children:
            if child.type == "call":
                self._extract_call(child, summary, source)
            else:
                self._walk_for_calls(child, summary, source)
