# code-onboard

Analyze any git repo and generate a newcomer-friendly **ONBOARDING.md** guide. Combines tree-sitter AST parsing with optional LLM narrative generation.

## Features

- **AST-powered analysis** — uses tree-sitter to extract functions, classes, imports, and call sites
- **Dependency graph** — builds an in-memory import graph to identify architecture, entry points, and hotspots
- **tsconfig path alias resolution** — resolves `@/*`, `baseUrl`, and workspace aliases in monorepos
- **Framework-aware entry points** — detects Next.js App Router pages/layouts/routes with URL inference
- **Test file filtering** — excludes `.spec.ts`, `.test.ts`, `.stories.tsx` from entry point analysis
- **Mermaid diagrams** — auto-generates architecture and call-graph diagrams
- **HTML reports** — `--html` generates a self-contained report with rendered Mermaid diagrams (no extensions needed)
- **LLM narratives** (optional) — sends structured summaries (never raw source) to OpenAI or Anthropic for human-readable explanations
- **Module responsibilities** — LLM-generated table showing what each module does, key exports, and coupling
- **Offline mode** — works without any API key via `--no-llm`

## Supported Languages

| Language | Extensions | Features |
|----------|-----------|----------|
| Python | `.py` | functions, classes, imports, main guards |
| TypeScript | `.ts`, `.tsx` | functions, arrow functions, classes, imports, exports |
| JavaScript | `.js`, `.jsx` | functions, arrow functions, classes, imports, exports |
| C# | `.cs` | classes, interfaces, records, methods, using directives, namespace resolution |

## Install

```bash
pip install -e ".[dev]"
```

## Usage

```bash
# Basic (no LLM, analysis-only)
code-onboard /path/to/repo --no-llm

# With Anthropic
ANTHROPIC_API_KEY=sk-ant-... code-onboard /path/to/repo

# With OpenAI
OPENAI_API_KEY=sk-... code-onboard /path/to/repo

# HTML report with rendered diagrams
code-onboard /path/to/repo --html

# Customize output
code-onboard . -o docs/ONBOARDING.md -n 15 --max-files 1000 -v
```

## CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `REPO_PATH` | `.` | Path to the repository to analyze |
| `-o, --output` | `ONBOARDING.md` | Output file path |
| `-n, --top-n` | `10` | Number of hotspots to display |
| `--max-files` | `500` | Maximum files to analyze |
| `--provider` | `auto` | `"openai"`, `"anthropic"`, `"none"`, or `"auto"` |
| `--model` | auto | Override the model name |
| `--no-llm` | off | Skip LLM, produce analysis-only output |
| `--html` | off | Also generate a self-contained HTML report |
| `-v, --verbose` | off | Show progress spinners |

## Output Sections

1. **How This App Starts** — entry points table with Next.js route detection + narrative
2. **Architecture Overview** — Mermaid dependency diagram + narrative
3. **Top N Hotspots** — most-imported files ranked by score + call graph
4. **Suggested Reading Order** — BFS-derived path through the codebase
5. **Module Responsibilities** (LLM only) — what each module does, key exports, coupling

## How It Works

```
repo/ --> [file walker] --> [tree-sitter AST parser] --> [dependency graph builder]
                                                              |
                    [tsconfig path alias resolver] <----------+
                                                              |
                    [entry point detector] <-------------------+
                    [hotspot ranker] <-------------------------+
                    [reading order (BFS)] <--------------------+
                                                              |
                    [Mermaid diagram generator] <--------------+
                    [LLM narrative generator] <----------------+
                                                              |
                    [Markdown assembler] --> ONBOARDING.md ----+
                    [HTML generator] --> ONBOARDING.html
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
# code-onboard
