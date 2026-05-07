# Cursor wrapper

This directory contains a [Cursor](https://cursor.com) project-rules wrapper for the `hush-uam-manifest` skill. The rule and reference content under `hush-uam/` is **generated** from the canonical Claude Code skill at [`../../plugins/hush-uam/skills/hush-uam-manifest/`](../../plugins/hush-uam/skills/hush-uam-manifest/) by [`scripts/sync-tools.sh`](../../scripts/sync-tools.sh). Don't edit the generated files directly — your changes will be overwritten on the next sync.

## Install (for end users)

Cursor expects rules at `<your-project>/.cursor/rules/<rule-name>/`. Copy the `hush-uam/` directory there:

```bash
# From a checkout of agent-skills:
mkdir -p <your-project>/.cursor/rules
cp -r tools/cursor/hush-uam <your-project>/.cursor/rules/

# Commit the rule into your project repo so teammates pick it up automatically:
cd <your-project>
git add .cursor/rules/hush-uam
git commit -m "Add hush-uam-manifest Cursor rule"
```

That's it. Open Cursor in the project, and when you ask the agent about Hush UAM, AccessCredential, AccessPrivilege, AccessPolicy, or any `am.hush.security` resource, it'll match on the rule's `description` and load the rule into context.

## Capability differences vs. Claude Code

The skill content (CRD schemas, type catalogs, examples, validation rules) is identical between the Cursor wrapper and the Claude Code skill. The interaction model differs in a few places:

- **No structured-question UI.** Claude Code uses an `AskUserQuestion` tool that renders multiple-choice prompts. Cursor's agent has no such tool, so questions go out as prose. The generated `.mdc` rule injects a "Note for Cursor" preamble telling the agent to use a numbered prose list instead. Slightly less polished UX, same outcome.
- **Activation timing.** Claude Code loads skills on intent match. Cursor's agent-requested rules use a similar matching model based on the `description` field, but the matching may be more or less aggressive than Claude Code's — Cursor users may need to mention "Hush" or the resource type explicitly to trigger it.
- **Reference files.** The `references/<type>.md` lazy-load pattern still works; Cursor's agent reads files on demand. Cursor may be more eager to load references upfront than Claude Code is — a minor efficiency difference, no behavioral change.

## How the wrapper is generated

`scripts/sync-tools.sh` reads the canonical `SKILL.md`, swaps the Claude-Code-flavored YAML frontmatter for Cursor's `.mdc` format (`description`, `alwaysApply`), prepends a Cursor-specific note about prose Q&A, and writes the result as `hush-uam-manifest.mdc`. The `references/` subdirectory is copied verbatim — those files are tool-agnostic Markdown.

To regenerate after editing canonical content:

```bash
bash scripts/sync-tools.sh
```

CI runs `scripts/sync-tools.sh --check` on every PR and fails the build if the committed `tools/cursor/` doesn't match what the script produces — this catches forgotten syncs before merge.

## Contributing

If you spot a bug in this wrapper:

- For content issues (wrong field name, missing type, etc.) — fix the canonical file at `plugins/hush-uam/skills/hush-uam-manifest/`, then run `bash scripts/sync-tools.sh` and commit both the canonical change and the regenerated wrapper.
- For wrapper-specific issues (the Cursor preamble, the frontmatter conversion, etc.) — edit `scripts/sync-tools.sh` (specifically the `sync_cursor()` function), regenerate, and commit.
