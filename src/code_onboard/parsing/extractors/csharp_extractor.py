"""Extract symbols from C# source using tree-sitter."""

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


class CSharpExtractor(BaseExtractor):
    def extract(self, tree: Tree, source: bytes, path: Path) -> FileSummary:
        summary = FileSummary(path=path, relative_path="", language="c_sharp")
        self._walk(tree.root_node, summary, source)
        return summary

    def _text(self, node: Node, source: bytes) -> str:
        return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

    def _walk(self, node: Node, summary: FileSummary, source: bytes) -> None:
        for child in node.children:
            if child.type == "using_directive":
                self._extract_using(child, summary, source)
            elif child.type in ("class_declaration", "record_declaration"):
                self._extract_class(child, summary, source)
            elif child.type == "interface_declaration":
                self._extract_interface(child, summary, source)
            elif child.type in ("namespace_declaration", "file_scoped_namespace_declaration"):
                # Recurse into namespace body
                self._walk(child, summary, source)
            elif child.type == "declaration_list":
                self._walk(child, summary, source)
            elif child.type in ("method_declaration", "local_function_statement"):
                self._extract_method(child, summary, source, is_top_level=True)

    def _extract_using(self, node: Node, summary: FileSummary, source: bytes) -> None:
        for child in node.children:
            if child.type in ("identifier", "qualified_name"):
                module = self._text(child, source)
                summary.imports.append(ImportStmt(module=module))
                return

    def _extract_class(self, node: Node, summary: FileSummary, source: bytes) -> None:
        name = ""
        bases: list[str] = []
        methods: list[str] = []
        is_public = False

        for child in node.children:
            if child.type == "identifier":
                name = self._text(child, source)
            elif child.type == "modifier":
                if self._text(child, source) == "public":
                    is_public = True
            elif child.type == "base_list":
                for sub in child.children:
                    if sub.type in ("identifier", "qualified_name", "generic_name"):
                        bases.append(self._text(sub, source))
            elif child.type == "declaration_list":
                for member in child.children:
                    if member.type == "method_declaration":
                        mn = self._find_child(member, "identifier")
                        if mn:
                            methods.append(self._text(mn, source))
                        self._extract_method(member, summary, source, is_top_level=False)
                    elif member.type == "constructor_declaration":
                        mn = self._find_child(member, "identifier")
                        if mn:
                            methods.append(self._text(mn, source))
                        self._extract_method(member, summary, source, is_top_level=False)
                    elif member.type == "property_declaration":
                        pass  # Skip properties for now

        if name:
            summary.classes.append(ClassDef(
                name=name,
                line=node.start_point[0] + 1,
                methods=methods,
                bases=bases,
                is_exported=is_public,
            ))

    def _extract_interface(self, node: Node, summary: FileSummary, source: bytes) -> None:
        name = ""
        bases: list[str] = []
        methods: list[str] = []

        for child in node.children:
            if child.type == "identifier":
                name = self._text(child, source)
            elif child.type == "base_list":
                for sub in child.children:
                    if sub.type in ("identifier", "qualified_name", "generic_name"):
                        bases.append(self._text(sub, source))
            elif child.type == "declaration_list":
                for member in child.children:
                    if member.type == "method_declaration":
                        mn = self._find_child(member, "identifier")
                        if mn:
                            methods.append(self._text(mn, source))

        if name:
            summary.classes.append(ClassDef(
                name=name,
                line=node.start_point[0] + 1,
                methods=methods,
                bases=bases,
                is_exported=True,
            ))

    def _extract_method(self, node: Node, summary: FileSummary, source: bytes, is_top_level: bool) -> None:
        name_node = self._find_child(node, "identifier")
        if not name_node:
            return

        params: list[str] = []
        param_list = self._find_child(node, "parameter_list")
        if param_list:
            for p in param_list.children:
                if p.type == "parameter":
                    pname = self._find_child(p, "identifier")
                    if pname:
                        params.append(self._text(pname, source))

        is_async = any(
            c.type == "modifier" and self._text(c, source) == "async"
            for c in node.children
        )

        summary.functions.append(FunctionDef(
            name=self._text(name_node, source),
            line=node.start_point[0] + 1,
            params=params,
            is_method=not is_top_level,
            is_async=is_async,
        ))

        # Walk body for calls
        body = self._find_child(node, "block")
        if body:
            self._walk_for_calls(body, summary, source)

    def _walk_for_calls(self, node: Node, summary: FileSummary, source: bytes) -> None:
        for child in node.children:
            if child.type == "invocation_expression":
                self._extract_call(child, summary, source)
            else:
                self._walk_for_calls(child, summary, source)

    def _extract_call(self, node: Node, summary: FileSummary, source: bytes) -> None:
        func = node.children[0] if node.children else None
        if func:
            name = self._text(func, source)
            # Simplify: keep last segment
            if "." in name:
                name = name.split(".")[-1]
            summary.calls.append(CallSite(name=name, line=node.start_point[0] + 1))

    def _find_child(self, node: Node, child_type: str) -> Node | None:
        for c in node.children:
            if c.type == child_type:
                return c
        return None
