# Hush Agent Skills

Plugins, skills, and rules for AI coding agents (Claude Code, and future support for other tools) that help you work with [Hush Security](https://hush.security) products.

## Plugins

| Plugin | Description |
|---|---|
| [`hush-uam`](plugins/hush-uam) | Author Hush UAM resources — `AccessCredential`, `AccessPrivilege`, `AccessPolicy` — as Kubernetes CRDs under `am.hush.security/v1alpha1`, or as Terraform for the `hushsecurity/hush` provider. |

## Installation

### Claude Code (recommended)

Add this repo as a marketplace and install the plugin:

```
/plugin marketplace add hushsecurity/agent-skills
/plugin install hush-uam
```

Or install a specific skill manually by cloning into your skills directory:

```bash
# user-level (available in all projects)
git clone https://github.com/hushsecurity/agent-skills.git ~/hush-agent-skills
ln -s ~/hush-agent-skills/plugins/hush-uam/skills/hush-uam-manifest ~/.claude/skills/hush-uam-manifest

# or project-level (checked into the repo)
git clone https://github.com/hushsecurity/agent-skills.git /tmp/hush-agent-skills
cp -r /tmp/hush-agent-skills/plugins/hush-uam/skills/hush-uam-manifest \
      <your-project>/.claude/skills/
```

### Cursor

A pre-built Cursor project-rule wrapper lives at [`tools/cursor/`](tools/cursor/). Copy it into your project's `.cursor/rules/` directory:

```bash
git clone https://github.com/hushsecurity/agent-skills.git /tmp/agent-skills
mkdir -p <your-project>/.cursor/rules
cp -r /tmp/agent-skills/tools/cursor/hush-uam <your-project>/.cursor/rules/
```

See [`tools/cursor/README.md`](tools/cursor/README.md) for capability caveats (Cursor doesn't have Claude Code's structured-question tool — questions go out as prose).

### Other AI tools

Wrappers for additional non-Claude-Code agents live under [`tools/`](tools/) — see [`tools/README.md`](tools/README.md) for the current list and contribution notes. If your tool isn't listed yet, the skill content under `plugins/hush-uam/skills/hush-uam-manifest/` is plain Markdown that any LLM-driven editor can read; consult your tool's docs on how to point it at a custom rule/instruction file.

## Usage

Once installed in Claude Code, ask things like:

- *"Create an access policy for postgres"*
- *"I need a Hush credential for our Gemini project"*
- *"Generate manifests for an OpenAI policy bound to my staging namespace"*
- *"Add a Hush postgres credential to our Terraform"*

The skill activates automatically based on intent. It first establishes whether you want
Kubernetes manifests or Terraform — inferring it from the repo where it can, asking where it
can't — then walks you through the necessary inputs (scope, deployment, attestation,
delivery, credential fields, secret handling, privileges) using structured questions.

## Repository layout

```
.
├── plugins/                              ← Claude Code plugins (canonical content)
│   └── hush-uam/
│       ├── .claude-plugin/plugin.json    ← plugin manifest
│       └── skills/
│           └── hush-uam-manifest/
│               ├── SKILL.md             ← shared model, interview, type catalog
│               └── references/
│                   ├── kubernetes.md    ← CRD syntax
│                   ├── terraform.md     ← HCL syntax
│                   └── <type>.md        ← one per credential type
├── .claude-plugin/marketplace.json       ← marketplace manifest (this repo as a Claude Code marketplace)
└── tools/                                ← wrappers for non-Claude-Code AI tools (Cursor, etc.)
```

## Checking the skill against upstream

The `hush-uam` skill makes a lot of concrete claims about `terraform-provider-hush` and
the Hush API — which resources exist, which secrets may be omitted, which version floors
apply. [`scripts/check-claims.py`](scripts/check-claims.py) verifies them against the real
sources rather than by reading the prose:

```bash
scripts/check-claims.py                                   # expects sibling checkouts
scripts/check-claims.py --provider ~/src/terraform-provider-hush
```

It is a maintainer tool, not a CI step, because it reads repositories CI does not have.
Run it after editing a reference file, and when the provider or the API changes.

## License

Apache 2.0 — see [LICENSE](LICENSE).
