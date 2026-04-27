"""Prompt templates for LLM narrative generation."""

SYSTEM_PROMPT = """\
You are a senior software engineer writing an onboarding guide for a new team member.
Use ONLY the structured data provided — do not invent or assume information not present.
Write in a clear, friendly, concise style. Use Markdown formatting.
Each section should be 2-4 sentences maximum."""

ENTRY_POINTS_PROMPT = """\
Based on this data about the application's entry points, write a brief narrative \
explaining how the application starts and what the main entry points do.

Entry points:
{entry_points_json}

Write 2-4 sentences. Focus on what a newcomer needs to know first."""

ARCHITECTURE_PROMPT = """\
Based on this dependency data, write a brief narrative describing the high-level \
architecture of this codebase — what the main modules are and how they relate.

Modules and dependencies:
{architecture_json}

Write 2-4 sentences. Focus on the big picture."""

HOTSPOTS_PROMPT = """\
Based on this data about the most important files in the codebase, write a brief \
narrative explaining why these files matter and what a newcomer should focus on.

Top hotspots:
{hotspots_json}

Write 2-4 sentences. Focus on practical advice."""

READING_ORDER_PROMPT = """\
Based on this suggested reading order, write a brief narrative guiding a newcomer \
through the codebase in the recommended sequence.

Reading order:
{reading_order_json}

Module summaries:
{module_map_json}

Write 2-4 sentences. Explain the logic behind this reading path."""

MODULE_RESPONSIBILITIES_PROMPT = """\
Based on this data about the modules (directories) in the codebase, write a table \
describing what each module is responsible for.

Modules with their key exports, file counts, and dependencies:
{module_responsibilities_json}

Write a Markdown table with these columns: Module | Responsibility | Key Exports | Used By (count).
- "Responsibility" should be a short 5-10 word description of what this module does, inferred from the directory name, file names, function names, and dependencies.
- "Key Exports" should list the 2-3 most important exported symbols.
- "Used By" is how many other modules depend on this one.
- Group related modules together (e.g. all apps/dashboard/* modules together).
- Skip test directories and spec files.
- Keep it concise — max 20 rows. Merge small subdirectories into their parent."""
