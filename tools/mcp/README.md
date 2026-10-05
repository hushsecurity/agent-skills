# MCP wrapper

This directory holds the copy of the `hush-uam-manifest` skill that the Hush MCP server
(lens) is meant to serve as a document, for clients whose agent reads the server's documents itself,
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

Lens turns the markdown under its S3 docs prefix into `docs://` resources, one per file:
`SKILL.md` and each `references/<file>.md` become their own documents, which Ask Hush lists
and reads with its `list_docs` and `read_doc` tools.

Two gaps on the lens side, to close before relying on this:

- Lens names each document from its S3 key and ignores frontmatter, so today the skill is
  listed as "Skill" and the `description` above is only seen after the document is opened.
  Lens should read the frontmatter, and keep `references/` out of the top-level listing so
  product questions don't land on a reference without the guide that explains it.
- Nothing publishes this directory yet. Don't upload it by hand under
  `s3://hush-knowledgebase/deployments/docs/md/`: the knowledgebase deploy empties that
  prefix before every upload, so a hand-placed copy disappears on the next docs release.
