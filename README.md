# code-onboard

[![CI](https://github.com/fatimamalbari/code-onboard/actions/workflows/ci.yml/badge.svg)](https://github.com/fatimamalbari/code-onboard/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

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

## How It Compares

| Feature | code-onboard | readme-ai | Madge | Sourcegraph | Dependency Cruiser |
|---------|:---:|:---:|:---:|:---:|:---:|
| AST parsing (tree-sitter) | Yes | No | No | Yes | Yes |
| Multi-language (Py + TS + C#) | Yes | No | JS/TS only | Yes | JS/TS only |
| Entry point detection | Yes | No | No | No | No |
| Hotspot ranking | Yes | No | No | No | No |
| Reading order suggestion | Yes | No | No | No | No |
| Mermaid diagrams | Yes | No | Yes (dot) | No | Yes |
| LLM narratives | Yes | Yes | No | No | No |
| Never sends raw source to LLM | Yes | No | N/A | N/A | N/A |
| tsconfig path alias resolution | Yes | No | No | Yes | Yes |
| Next.js route detection | Yes | No | No | No | No |
| Offline mode | Yes | No | Yes | No | Yes |
| Self-hosted / no SaaS | Yes | Yes | Yes | No | Yes |
| HTML report output | Yes | No | Yes | Yes | Yes |

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

## FAQ

**Does it send my source code to the LLM?**
No. code-onboard sends only structured JSON metadata (file paths, function names, import relationships, scores) to the LLM. Raw source code is never transmitted. You can verify this in [`src/code_onboard/llm/context.py`](src/code_onboard/llm/context.py).

**How much does the LLM cost per run?**
Approximately $0.05 per run (~12K tokens) using Claude Sonnet. The `--no-llm` flag produces a complete output with zero API cost.

**Can I use it with a local LLM?**
Yes. Set `OPENAI_BASE_URL` to your local endpoint (e.g. Ollama, LM Studio) and use `--provider openai` with any compatible model.

**Why are some files missing from the output?**
The default `--max-files` is 500. For large monorepos, increase it: `--max-files 3000`. Files in `node_modules`, `.git`, `dist`, `build`, and other common vendor directories are always skipped.

## Known Limitations

- **CommonJS `require()`** — only ESM `import` syntax is parsed; `require()` calls are not resolved
- **Dynamic imports** — `import()` expressions are not tracked
- **Non-alias non-relative imports** — bare imports like `lodash` or `react` are treated as external and skipped (by design)
- **C# namespace resolution** — inferred from directory structure, not from actual `namespace` declarations in source
- **Large monorepos** — the `--max-files` cap (default 500) may exclude parts of the codebase; increase as needed

## Roadmap

- [ ] Go language support
- [ ] Java language support
- [ ] Rust language support
- [ ] Circular dependency detection
- [ ] Dead code detection (zero in-degree + zero out-degree)
- [ ] Git log-based change frequency hotspots
- [ ] `--watch` mode for re-generation on file changes
- [ ] `--diff` mode to show what changed since last generation
- [ ] GitHub Action for auto-generating ONBOARDING.md on push
- [ ] PyPI package publishing (`pip install code-onboard`)

## Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Make your changes and add tests
5. Run the test suite: `pytest tests/ -v`
6. Submit a pull request

Please keep PRs focused on a single change. If you're adding a new language, include test fixtures and extractor tests.

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Inspiration

Inspired by [GitNexus](https://github.com/abhigyanpatwari/GitNexus) — a tool for analyzing GitHub repositories.

## License

MIT
