# Changelog

All notable changes to plugins in this repository.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Each plugin is versioned independently and tagged as `<plugin-name>-v<X.Y.Z>` (e.g. `hush-uam-v0.1.0`).

## [Unreleased]

_Nothing yet._

## [hush-uam-v0.1.0] - 2026-05-10

Initial public release of the `hush-uam` plugin. Tracks operator API version `am.hush.security/v1alpha1`.

### Added

- `hush-uam-manifest` skill for authoring `AccessCredential`, `AccessPrivilege`, and `AccessPolicy` CRDs.
- Per-type reference files under `references/` covering all 26 supported credential types.
- Auth-principal permission lists for every type that has them.
- Connection-string templates for DB-style types.
- Drift-correction handling for the `enabled` field on `AccessPolicy`.
- Resource-grouped, policy-first structured input flow via `AskUserQuestion`.
- Cursor wrapper at `tools/cursor/hush-uam/` generated from canonical content by `scripts/sync-tools.sh`.

[Unreleased]: https://github.com/hushsecurity/agent-skills/compare/hush-uam-v0.1.0...HEAD
[hush-uam-v0.1.0]: https://github.com/hushsecurity/agent-skills/releases/tag/hush-uam-v0.1.0
