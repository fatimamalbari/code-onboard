"""Extract symbols from TypeScript/JavaScript source using tree-sitter."""

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


class TSExtractor(BaseExtractor):
    def extract(self, tree: Tree, source: bytes, path: Path) -> FileSummary:
        summary = FileSummary(path=path, relative_path="", language="typescript")
        self._walk(tree.root_node, summary, source)
        return summary

    def _text(self, node: Node, source: bytes) -> str:
        return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

    def _walk(self, node: Node, summary: FileSummary, source: bytes) -> None:
        for child in node.children:
            if child.type == "import_statement":
                self._extract_import(child, summary, source)
            elif child.type in ("function_declaration", "method_definition",
                                "arrow_function", "generator_function_declaration"):
                self._extract_function(child, summary, source)
            elif child.type == "class_declaration":
                self._extract_class(child, summary, source)
            elif child.type == "export_statement":
                self._extract_export(child, summary, source)
            elif child.type == "call_expression":
                self._extract_call(child, summary, source)
            elif child.type == "lexical_declaration":
                self._extract_lexical(child, summary, source)
            elif child.type in ("expression_statement", "if_statement", "for_statement",
                                "for_in_statement", "while_statement", "try_statement",
                                "switch_statement"):
                self._walk(child, summary, source)

    def _extract_import(self, node: Node, summary: FileSummary, source: bytes) -> None:
        module = ""
        names: list[str] = []

        for child in node.children:
            if child.type == "string":
                module = self._text(child, source).strip("'\"")
            elif child.type == "import_clause":
                for sub in child.children:
                    if sub.type == "identifier":
                        names.append(self._text(sub, source))
                    elif sub.type == "named_imports":
                        for item in sub.children:
                            if item.type == "import_specifier":
                                name_node = item.child_by_field_name("name") or item
                                names.append(self._text(name_node, source))
                    elif sub.type == "namespace_import":
                        for s in sub.children:
                            if s.type == "identifier":
                                names.append(f"* as {self._text(s, source)}")

        is_relative = module.startswith(".")
        summary.imports.append(ImportStmt(module=module, names=names, is_relative=is_relative))

    def _extract_function(self, node: Node, summary: FileSummary, source: bytes, exported: bool = False) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return

        params: list[str] = []
        params_node = node.child_by_field_name("parameters")
        if params_node:
            for p in params_node.children:
                if p.type in ("identifier", "required_parameter", "optional_parameter",
                              "rest_parameter", "assignment_pattern"):
                    pn = p.child_by_field_name("pattern") or p.child_by_field_name("name") or p
                    name = self._text(pn, source)
                    if name not in ("(", ")", ","):
                        params.append(name)

        is_async = any(c.type == "async" for c in (node.parent.children if node.parent else []))

        summary.functions.append(FunctionDef(
            name=self._text(name_node, source),
            line=node.start_point[0] + 1,
            params=params,
            is_async=is_async,
            is_exported=exported,
        ))

        if exported:
            summary.exports.append(self._text(name_node, source))

        # Walk body for calls
        body = node.child_by_field_name("body")
        if body:
            self._walk_for_calls(body, summary, source)

    def _extract_class(self, node: Node, summary: FileSummary, source: bytes, exported: bool = False) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return

        bases: list[str] = []
        for child in node.children:
            if child.type == "class_heritage":
                for sub in child.children:
                    if sub.type == "extends_clause":
                        for s in sub.children:
                            if s.type in ("identifier", "member_expression"):
                                bases.append(self._text(s, source))

        methods: list[str] = []
        body = node.child_by_field_name("body")
        if body:
            for child in body.children:
                if child.type == "method_definition":
                    mn = child.child_by_field_name("name")
                    if mn:
                        methods.append(self._text(mn, source))
                    self._extract_function(child, summary, source)

        summary.classes.append(ClassDef(
            name=self._text(name_node, source),
            line=node.start_point[0] + 1,
            methods=methods,
            bases=bases,
            is_exported=exported,
        ))

        if exported:
            summary.exports.append(self._text(name_node, source))

    def _extract_export(self, node: Node, summary: FileSummary, source: bytes) -> None:
        for child in node.children:
            if child.type == "function_declaration":
                self._extract_function(child, summary, source, exported=True)
            elif child.type == "class_declaration":
                self._extract_class(child, summary, source, exported=True)
            elif child.type == "lexical_declaration":
                self._extract_lexical(child, summary, source, exported=True)
            elif child.type == "export_clause":
                for spec in child.children:
                    if spec.type == "export_specifier":
                        name_node = spec.child_by_field_name("name") or spec
                        summary.exports.append(self._text(name_node, source))
            elif child.type == "identifier":
                summary.exports.append(self._text(child, source))

    def _extract_lexical(self, node: Node, summary: FileSummary, source: bytes, exported: bool = False) -> None:
        """Handle const/let/var declarations — extract arrow functions."""
        for child in node.children:
            if child.type == "variable_declarator":
                name_node = child.child_by_field_name("name")
                value_node = child.child_by_field_name("value")
                if name_node and value_node and value_node.type == "arrow_function":
                    params: list[str] = []
                    params_node = value_node.child_by_field_name("parameters")
                    if params_node:
                        for p in params_node.children:
                            if p.type in ("identifier", "required_parameter", "optional_parameter"):
                                pn = p.child_by_field_name("name") or p
                                name = self._text(pn, source)
                                if name not in ("(", ")", ","):
                                    params.append(name)

                    fn_name = self._text(name_node, source)
                    summary.functions.append(FunctionDef(
                        name=fn_name,
                        line=child.start_point[0] + 1,
                        params=params,
                        is_exported=exported,
                    ))
                    if exported:
                        summary.exports.append(fn_name)

                    body = value_node.child_by_field_name("body")
                    if body:
                        self._walk_for_calls(body, summary, source)

    def _extract_call(self, node: Node, summary: FileSummary, source: bytes) -> None:
        func = node.child_by_field_name("function")
        if func:
            name = self._text(func, source)
            if "." in name:
                name = name.split(".")[-1]
            summary.calls.append(CallSite(name=name, line=node.start_point[0] + 1))

    def _walk_for_calls(self, node: Node, summary: FileSummary, source: bytes) -> None:
        for child in node.children:
            if child.type == "call_expression":
                self._extract_call(child, summary, source)
            else:
                self._walk_for_calls(child, summary, source)
