# MCP wrapper

This directory holds the copy of the `hush-uam-manifest` skill that the Hush MCP server
(lens) serves as a document, for clients whose agent reads the server's documents itself,
such as the Ask Hush assistant in the Hush portal. The content under
`hush-uam-manifest/` is **generated** from the canonical Claude Code skill at
[`../../plugins/hush-uam/skills/hush-uam-manifest/`](../../plugins/hush-uam/skills/hush-uam-manifest/)
by [`scripts/sync-tools.sh`](../../scripts/sync-tools.sh). Don't edit it directly.

## What the wrapper changes

The body and references are the canonical skill, unchanged. The generated `SKILL.md`
replaces the frontmatter `description` and puts a preamble in front of the body, because
an MCP client may lack what the skill assumes:

- **No question tool.** Use one if present; otherwise ask in the same lettered prose
  format the Cursor wrapper uses.
- **No repo.** Ask for what the skill would infer from the repo: the target, and on
  Terraform whether a `provider "hush"` block and a `hush_deployment` exist.
- **No filesystem.** Deliver files as fenced code blocks.
- **Lens read tools.** Look up policy suggestions and existing credentials, privileges and
  policies in the user's org instead of asking for them. Lens has no tool that creates UAM
  resources, so the skill still only produces code.

The `description` differs because the canonical one is tuned for Claude Code's skill
matching ("whenever the user asks about Hush"), which over-triggers on a server where
every question is about Hush.

## How lens serves it

Lens's `make build` downloads this directory from `main` (`AGENT_SKILLS_REF` overrides
the ref) and bakes it into the image, so a merge here ships with the next lens build.
Lens serves each file as a `docs://skills/...` resource next to its S3 docs, which Ask
Hush lists and reads with its `list_docs` and `read_doc` tools:

- `SKILL.md` is listed under its frontmatter `name` and `description`.
- Markdown links to `references/<file>.md` are rewritten to the reference's `docs://`
  URI. Mentions in backticks aren't, which is why the preamble says to find references in
  the listing.
- Each reference's description names its guide, so a product question doesn't land on a
  reference read on its own.
