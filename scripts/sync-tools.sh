#!/usr/bin/env bash
# sync-tools.sh — regenerates everything under tools/<tool>/ from the canonical
# Claude Code skill content under plugins/<plugin>/skills/<skill>/.
#
# Run this before committing changes to a skill. CI runs it too and fails the
# build if its output differs from what's committed — forcing tool wrappers to
# stay in sync with canonical content.
#
# Usage:
#   scripts/sync-tools.sh                 # regenerate all tool wrappers
#   scripts/sync-tools.sh --check         # exit 1 if regeneration would change anything

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

CHECK_MODE=0
if [[ "${1:-}" == "--check" ]]; then
  CHECK_MODE=1
fi

# ─── helpers ─────────────────────────────────────────────────────────────────

# Strip the Claude Code SKILL.md YAML frontmatter (lines between the first two
# `---` delimiters at the top of the file) and emit the body only. Body-level
# `---` separators (Markdown horizontal rules between sections) are preserved.
skill_body() {
  awk '
    BEGIN { state = 0 }                              # 0=before fm, 1=in fm, 2=body
    state == 0 && /^---$/ { state = 1; next }        # opening fence
    state == 1 && /^---$/ { state = 2; next }        # closing fence
    state == 1 { next }                              # frontmatter line — skip
    state == 2 { print }                             # body — print verbatim, including body --- separators
  ' "$1"
}

# Read the `description` field from a SKILL.md frontmatter.
skill_description() {
  awk '
    BEGIN{in_fm=0}
    /^---$/{in_fm++; next}
    in_fm==1 && /^description:/{
      sub(/^description:[[:space:]]*/, "");
      print;
      exit
    }
  ' "$1"
}

# ─── target: tools/cursor ────────────────────────────────────────────────────

sync_cursor() {
  local skill_src="plugins/hush-uam/skills/hush-uam-manifest"
  local cursor_dst="tools/cursor/hush-uam"

  rm -rf "$cursor_dst"
  mkdir -p "$cursor_dst/references"

  # Copy references verbatim — they're tool-agnostic Markdown.
  cp -r "$skill_src/references/." "$cursor_dst/references/"

  # Convert SKILL.md → hush-uam-manifest.mdc with Cursor frontmatter.
  local description
  description="$(skill_description "$skill_src/SKILL.md")"

  {
    printf -- "---\n"
    printf "description: %s\n" "$description"
    printf "alwaysApply: false\n"
    printf -- "---\n\n"
    printf "## Note for Cursor — REQUIRED question format\n\n"
    printf "Cursor's agent does not have Claude Code's \`AskUserQuestion\` tool. Wherever the\n"
    printf "instructions below tell you to \"use \`AskUserQuestion\`\" or \"batch up to 4 structured\n"
    printf "questions\", you MUST ask via prose using the **exact** format below. The user has\n"
    printf "been told to expect it; deviating makes their reply ambiguous and the\n"
    printf "manifest-generation step will fail.\n\n"
    printf "### Required format\n\n"
    printf "1. Group questions by resource (policy / credential / privilege). Ask all\n"
    printf "   questions for one resource in a single message before moving to the next.\n"
    printf "2. Number the questions \`1.\`, \`2.\`, \`3.\`, ...\n"
    printf "3. For each question with discrete options, **place the label \`(a)\`, \`(b)\`, \`(c)\`,\n"
    printf "   ... at the very start of each option line, with no leading bullet or hyphen.**\n"
    printf "   The label is the visual anchor, not decoration on a bullet list.\n"
    printf "4. **Enumerate EVERY valid option.** Do not stop at 2-3 examples. If there are 5\n"
    printf "   attestation criterion types, list all 5. If there are 4 delivery modes, list\n"
    printf "   all 4.\n"
    printf "5. Each option gets a one-line description after the label, explaining what it\n"
    printf "   means or when to pick it.\n"
    printf "6. Mark recommended options with \`(Recommended)\` at the end of the description.\n"
    printf "7. For free-form values (CR names, hostnames, project IDs, env var names): state\n"
    printf "   the field, the expected format, and any default. Don't bury them inside an\n"
    printf "   option list.\n"
    printf "8. End the message with a literal reply template:\n"
    printf "   \`Reply with: 1: <choice>, 2: <choice>, ...\` — and use \`b,d\` notation for\n"
    printf "   multi-select questions.\n\n"
    printf "### Anti-patterns — do NOT do these\n\n"
    printf -- "- **Bullet hyphens without letter labels.** \`- Full trio — ...\` is wrong; the\n"
    printf "  user can't answer \"the third bullet\" unambiguously.\n"
    printf -- "- **Compressed option lists.** \"by namespace + SA\" is wrong if the underlying\n"
    printf "  question has 5 valid criterion types — list all of them.\n"
    printf -- "- **Inventing your own reply format.** Use \`1: a, 2: pg-app-policy, 3: a,c\`,\n"
    printf "  not free-form prose answers.\n"
    printf -- "- **Asking values across resource boundaries.** Don't ask credential field\n"
    printf "   values in the same round as policy attestation values.\n\n"
    printf "### Worked example — copy this format verbatim\n\n"
    printf "When the user prompts \"I want a policy for postgres\", your first message should\n"
    printf "look exactly like this (option *contents* will vary by type, but the *format* is\n"
    printf "fixed):\n\n"
    printf "\`\`\`\n"
    printf "Round 1 — policy plumbing.\n\n"
    printf "1. Scope (pick one):\n"
    printf "(a) Full trio — AccessCredential + AccessPrivilege + AccessPolicy (Recommended for greenfield)\n"
    printf "(b) AccessCredential + AccessPolicy — cred is new, no privilege needed\n"
    printf "(c) AccessPolicy only — references existing cred/privilege by id or name\n"
    printf "(d) Single resource — cred only, privilege only, or policy only\n\n"
    printf "2. Policy CR name (free-form; default: pg-app-policy).\n\n"
    printf "3. Attestation pattern (multi-select; pick one or more):\n"
    printf "(a) k8s:ns + k8s:sa — match by namespace + service account (Recommended for K8s workloads)\n"
    printf "(b) k8s:ns only — match all workloads in a namespace\n"
    printf "(c) k8s:pod-label — match by pod label key+value\n"
    printf "(d) k8s:pod-name — match a specific pod\n"
    printf "(e) k8s:container-name — match a specific container\n\n"
    printf "4. Delivery type (pick one):\n"
    printf "(a) env template — single env var like DATABASE_URL from the connection-string template (Recommended for DB types)\n"
    printf "(b) env split — one env var per credential field (e.g. PG_USER, PG_PASSWORD)\n"
    printf "(c) volume — write fields to files at a mount point\n"
    printf "(d) sdk — fetched at runtime via the Hush SDK\n\n"
    printf "5. enabled management (pick one):\n"
    printf "(a) Toggle outside K8s — omit spec.enabled so Hush API/UI/Terraform can flip it without operator drift (Recommended)\n"
    printf "(b) Reconcile in K8s — set spec.enabled: true and let the operator restore drift on this field too\n\n"
    printf "Reply with: 1: <a|b|c|d>, 2: <name>, 3: <letters, e.g. a or a,c>, 4: <a|b|c|d>, 5: <a|b>.\n"
    printf "\`\`\`\n\n"
    printf "After Round 1's answers come back, ask Round 2 (the values for whatever the user\n"
    printf "picked — workload namespace + SA names, env var names, etc.) in the same\n"
    printf "letter-labeled style if there are discrete choices, or as numbered free-form\n"
    printf "prompts otherwise. Then continue to the credential round, then the privilege\n"
    printf "round.\n\n"
    printf "Reference files live next to this file under \`references/\`. Read the matching\n"
    printf "\`references/<type>.md\` before generating manifests for that type.\n\n"
    printf -- "---\n\n"
    skill_body "$skill_src/SKILL.md"
  } > "$cursor_dst/hush-uam-manifest.mdc"
}

# ─── future tools ────────────────────────────────────────────────────────────
# Add per-tool sync_<tool>() functions here as new wrappers are introduced
# (sync_copilot, sync_aider, sync_windsurf). Each should rm -rf its dst dir
# and rebuild from canonical.

# ─── main ────────────────────────────────────────────────────────────────────

if [[ "$CHECK_MODE" -eq 1 ]]; then
  TMPDIR="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR"' EXIT
  cp -r tools "$TMPDIR/tools-before"
  sync_cursor
  if ! diff -ruN "$TMPDIR/tools-before" tools >/dev/null; then
    echo "tools/ is out of sync with canonical content."
    echo "Run scripts/sync-tools.sh and commit the result."
    diff -ruN "$TMPDIR/tools-before" tools | head -50
    exit 1
  fi
  echo "tools/ is in sync with canonical."
  exit 0
fi

sync_cursor
echo "Synced tools/cursor/ from canonical."
