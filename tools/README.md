# Tool wrappers

This directory holds wrappers that adapt Hush agent skills for AI agents *other* than Claude Code (Cursor, GitHub Copilot, Aider, Cline, Windsurf, etc.).

## Current status

| Tool | Wrapper | Notes |
|---|---|---|
| Cursor | [`cursor/`](cursor/) | Project-rule wrapper. Generated from canonical by `scripts/sync-tools.sh`. |

The canonical implementation is the Claude Code skill at [`../plugins/hush-uam/skills/hush-uam-manifest/`](../plugins/hush-uam/skills/hush-uam-manifest/). Skill content is plain Markdown and can be consumed by any LLM-driven editor; this directory hosts concrete, ready-to-install wrappers for non-Claude-Code agents.

## How wrappers work

Most non-Claude-Code agents have one of two extension primitives:

1. **Always-loaded instruction files** (Copilot's `copilot-instructions.md`, Aider's `CONVENTIONS.md`) — short documents loaded into every prompt.
2. **Conditionally-loaded rules** (Cursor's `.cursor/rules/*.mdc` with glob/auto-attach metadata, Windsurf's rules, Cline's project rules) — rules attached based on file patterns or manual selection.

Neither model has Claude Code's intent-based skill activation, so wrappers should be **thin pointers** rather than full content duplicates:

> When the user asks about Hush UAM, AccessCredential, AccessPrivilege, AccessPolicy, or any `am.hush.security` resource, read the agent guide at `<repo>/plugins/hush-uam/skills/hush-uam-manifest/SKILL.md` and the matching `references/<type>.md` files, and follow their instructions.

The wrapper carries the activation hints that the host tool understands; the actual content stays in the canonical skill location, so updates only need to happen once.

## Adding a new wrapper

Wrappers are **generated from canonical content** by [`../scripts/sync-tools.sh`](../scripts/sync-tools.sh). Don't hand-edit files inside `tools/<tool>/` — they get overwritten.

To add support for a new tool:

1. Open `scripts/sync-tools.sh` and add a `sync_<tool>()` function modeled on `sync_cursor()`. It should `rm -rf` the destination directory and rebuild it from canonical, applying any tool-specific transformations (frontmatter format, capability disclaimers, etc.).
2. Call the new function from the `main` section at the bottom of the script.
3. Run `bash scripts/sync-tools.sh` and inspect the output.
4. Add a `tools/<tool>/README.md` documenting install instructions and capability caveats.
5. Add a row to the table in this file.
6. Update the top-level [`README.md`](../README.md) to mention the new wrapper.
7. Commit both `scripts/sync-tools.sh` and the generated `tools/<tool>/` content. CI will keep them in sync going forward via [`../.github/workflows/check-tool-sync.yml`](../.github/workflows/check-tool-sync.yml).

## Future: shared content extraction

If two or more non-Claude-Code wrappers end up needing the same chunks of body text (workflows, schemas, examples) that currently live inside `SKILL.md`, factor those chunks out into a new top-level `shared/` directory and have all wrappers (including the Claude Code SKILL.md) reference them. Don't pre-extract — wait until there's actual duplication to deduplicate.
