"""Generate a self-contained HTML report with rendered Mermaid diagrams."""

from __future__ import annotations

import html
import re


def markdown_to_html(md: str) -> str:
    """Convert the ONBOARDING.md content to a self-contained HTML page.

    Replaces Mermaid code blocks with <pre class="mermaid"> tags so that
    Mermaid.js renders them as diagrams. Other Markdown is converted to
    basic HTML (tables, headings, lists, code blocks, paragraphs).
    """
    lines = md.split("\n")
    html_parts: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Mermaid code block
        if line.strip() == "```mermaid":
            mermaid_lines: list[str] = []
            i += 1
            while i < len(lines) and lines[i].strip() != "```":
                mermaid_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            mermaid_code = html.escape("\n".join(mermaid_lines))
            html_parts.append(f'<pre class="mermaid">\n{mermaid_code}\n</pre>')
            continue

        # Other code block
        if line.strip().startswith("```"):
            lang = line.strip().removeprefix("```")
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and lines[i].strip() != "```":
                code_lines.append(html.escape(lines[i]))
                i += 1
            i += 1
            code_content = "\n".join(code_lines)
            html_parts.append(f'<pre><code class="{html.escape(lang)}">{code_content}</code></pre>')
            continue

        # Headings
        if line.startswith("# "):
            html_parts.append(f"<h1>{_inline(line[2:])}</h1>")
            i += 1
            continue
        if line.startswith("## "):
            html_parts.append(f"<h2>{_inline(line[3:])}</h2>")
            i += 1
            continue
        if line.startswith("### "):
            html_parts.append(f"<h3>{_inline(line[4:])}</h3>")
            i += 1
            continue

        # Table
        if line.strip().startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|--"):
            table_lines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            html_parts.append(_table_to_html(table_lines))
            continue

        # Ordered list
        if re.match(r"^\d+\.\s", line):
            list_items: list[str] = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i]):
                list_items.append(re.sub(r"^\d+\.\s", "", lines[i]))
                i += 1
            items = "".join(f"<li>{_inline(item)}</li>" for item in list_items)
            html_parts.append(f"<ol>{items}</ol>")
            continue

        # Empty line
        if not line.strip():
            i += 1
            continue

        # Paragraph
        html_parts.append(f"<p>{_inline(line)}</p>")
        i += 1

    body = "\n".join(html_parts)
    return _HTML_TEMPLATE.replace("{{BODY}}", body)


def _inline(text: str) -> str:
    """Convert inline markdown: bold, italic, code, links."""
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2">\1</a>',
        text,
    )
    return text


def _table_to_html(table_lines: list[str]) -> str:
    """Convert markdown table lines to HTML table."""
    rows: list[list[str]] = []
    for line in table_lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)

    if len(rows) < 2:
        return ""

    header = rows[0]
    # Skip separator row (row[1])
    body_rows = rows[2:]

    thead = "<tr>" + "".join(f"<th>{_inline(h)}</th>" for h in header) + "</tr>"
    tbody = ""
    for row in body_rows:
        # Pad row to match header length
        while len(row) < len(header):
            row.append("")
        tbody += "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>"

    return f"<table><thead>{thead}</thead><tbody>{tbody}</tbody></table>"


_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Onboarding Guide</title>
<style>
  :root { --bg: #0d1117; --fg: #c9d1d9; --accent: #58a6ff; --border: #30363d; --card: #161b22; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
         background: var(--bg); color: var(--fg); max-width: 1100px; margin: 0 auto; padding: 2rem; line-height: 1.6; }
  h1 { color: #f0f6fc; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin: 2rem 0 1rem; font-size: 2rem; }
  h2 { color: #f0f6fc; border-bottom: 1px solid var(--border); padding-bottom: 0.3rem; margin: 1.8rem 0 0.8rem; font-size: 1.5rem; }
  h3 { color: #f0f6fc; margin: 1.2rem 0 0.5rem; font-size: 1.2rem; }
  p { margin: 0.5rem 0; }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  code { background: var(--card); padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.9em; color: #e6edf3; }
  pre { background: var(--card); padding: 1rem; border-radius: 8px; overflow-x: auto; margin: 1rem 0; }
  pre code { padding: 0; background: none; }
  pre.mermaid { background: #fff; color: #333; border-radius: 8px; padding: 1.5rem; text-align: center; }
  table { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.9rem; }
  th { background: var(--card); text-align: left; padding: 0.6rem 0.8rem; border: 1px solid var(--border); color: #f0f6fc; }
  td { padding: 0.5rem 0.8rem; border: 1px solid var(--border); }
  tr:hover { background: rgba(88,166,255,0.05); }
  ol { padding-left: 1.5rem; margin: 0.5rem 0; }
  li { margin: 0.25rem 0; }
  strong { color: #f0f6fc; }
  em { color: var(--accent); font-style: italic; }
</style>
</head>
<body>
{{BODY}}
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>
mermaid.initialize({ startOnLoad: true, theme: 'default', securityLevel: 'loose' });
</script>
</body>
</html>
"""
