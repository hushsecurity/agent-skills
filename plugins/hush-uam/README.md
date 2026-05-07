# hush-uam

Claude Code plugin for authoring Kubernetes manifests for the Hush UAM (Universal Access Management) operator. Currently bundles one skill — `hush-uam-manifest` — covering `AccessCredential`, `AccessPrivilege`, and `AccessPolicy` CRDs under the `am.hush.security/v1alpha1` API group.

This is the **canonical** location for the skill content. Wrappers for non-Claude-Code agents (e.g. [Cursor](../../tools/cursor/)) are generated from here by [`scripts/sync-tools.sh`](../../scripts/sync-tools.sh); don't edit those — edit here.

## Install

### Via the marketplace (Recommended)

If you've added the repo as a Claude Code marketplace, this plugin is installable in one command:

```
/plugin marketplace add hushsecurity/agent-skills    # one-time, if not already added
/plugin install hush-uam
```

### Manual install

Clone the repo and symlink (or copy) the skill into your Claude Code skills directory:

```bash
# user-level — available in every project
git clone https://github.com/hushsecurity/agent-skills.git ~/hush-agent-skills
ln -s ~/hush-agent-skills/plugins/hush-uam/skills/hush-uam-manifest \
      ~/.claude/skills/hush-uam-manifest

# or project-level — checked into your project's repo so teammates pick it up
git clone https://github.com/hushsecurity/agent-skills.git /tmp/hush-agent-skills
cp -r /tmp/hush-agent-skills/plugins/hush-uam/skills/hush-uam-manifest \
      <your-project>/.claude/skills/
cd <your-project>
git add .claude/skills/hush-uam-manifest
git commit -m "Add hush-uam-manifest Claude Code skill"
```

Symlink is preferred for user-level installs because skill updates land automatically when you `git pull` the agent-skills checkout. Copy is preferred for project-level because the skill is then versioned with the project.

## Pre-allow reference reads (recommended)

The skill loads per-type files from `references/` on demand (`postgres.md`, `gemini.md`, etc.). By default Claude Code asks for permission on every file read, including these. To auto-allow them, add a `Read(...)` permission to your `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Read(./.claude/skills/hush-uam-manifest/references/**)"
    ]
  }
}
```

For user-level installs (skill symlinked into `~/.claude/skills/`), put it in `~/.claude/settings.json` and adjust the path:

```json
{
  "permissions": {
    "allow": [
      "Read(~/.claude/skills/hush-uam-manifest/references/**)"
    ]
  }
}
```

Without this, the first time you generate a manifest of a given type, Claude Code will prompt to approve reading the matching reference file. You can also pick the session-scoped "allow reading from references/" option in that prompt to defer the settings change.

## Usage

Once installed, ask Claude Code things like:

- *"Create an access policy for postgres"*
- *"I need a Hush credential for our Gemini project"*
- *"Generate manifests for an OpenAI policy bound to my staging namespace"*

The skill activates automatically based on intent and walks you through the necessary inputs (scope, attestation, delivery, credential fields, secret strategy, privileges) using structured `AskUserQuestion` prompts. It then prints the manifest along with the auth-principal permissions Hush needs on the target system.

## Structure

```
plugins/hush-uam/
├── .claude-plugin/plugin.json        ← plugin manifest (name, version, description)
├── README.md                         ← this file
└── skills/hush-uam-manifest/
    ├── SKILL.md                      ← the skill itself
    └── references/                   ← per-type reference docs (postgres.md, gemini.md, ...)
                                       loaded on demand when generating that type
```

## Versioning

This plugin is versioned independently of others in the repo, tagged as `hush-uam-v<X.Y.Z>`, following [Semantic Versioning](https://semver.org). The current version is in [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json). See the top-level [`CHANGELOG.md`](../../CHANGELOG.md) for release notes.

The plugin tracks operator API version `am.hush.security/v1alpha1`. When the operator's CRD breaks compatibility, the plugin's MAJOR version bumps with it.

## Other AI tools

A pre-built Cursor project-rule wrapper for the same skill lives at [`../../tools/cursor/`](../../tools/cursor/). See [`tools/cursor/README.md`](../../tools/cursor/README.md) for Cursor install instructions.
