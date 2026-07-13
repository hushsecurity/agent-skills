# Changelog

All notable changes to plugins in this repository.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Each plugin is versioned independently and tagged as `<plugin-name>-v<X.Y.Z>` (e.g. `hush-uam-v0.1.0`).

## [Unreleased]

### Added

- `redis` credential: `aiven` engine (`config.engine: aiven`) alongside the existing `redis` and `elasticache` engines. An Aiven-managed Valkey service — authenticated with an Aiven REST API token via `secretRef.token`, addressed by `project` + `service_name`. Hush resolves the host/port and mints the user via the Aiven API, so none of the redis/elasticache connection or auth fields (`host`, `port`, `password`, `username`, `database`, `tls`, `tls_ca`, `cache_engine`, and the ElastiCache fields) may be set; `cache_engine` in particular is not taken (Hush resolves the valkey-family variant from the live service). `engine` is fixed at create. The `elasticache` engine now validates `cache_engine` against `redis`/`valkey`. Redis privilege `keys`/`channels` entries must each be a single whitespace-free token. Documented in `references/redis.md` (and the cursor mirror); `SKILL.md` catalog, structural-decisions, and connection-string notes updated.

- `rabbitmq` credential: `config.auto_rotate_root` flag (boolean, default `false`). When `true`, Hush periodically rotates the root/admin credential itself (the `password` in `secretRef`), not just the ephemeral per-workload users; the rotation interval is 30 days. RabbitMQ is currently the only credential type that supports root rotation. Documented in `references/rabbitmq.md` (and the cursor mirror).

## [hush-uam-v0.3.0] - 2026-06-22

### Added

- `kafka` credential type — dynamic credential that provisions an ephemeral per-workload Kafka user and ACLs. Two engines selected by the `config.engine` field (fixed at create): `native` (self-hosted brokers; admin SASL user via `secretRef.password`, with `bootstrap_servers`/`sasl_mechanism`/`tls`/`tls_ca`) and `aiven` (Aiven-managed service; API token via `secretRef.token`, with `project`/`service_name`). Each engine accepts only its own fields, enforced per-engine at the API. Matching `kafka` privilege type with `acls[]` of `{resource_type, resource_name, pattern_type, operation, permission_type, host}` (`pattern_type` is one of `LITERAL`/`PREFIXED`, `permission_type` is one of `ALLOW`/`DENY`; consumer/producer/full-access presets documented). New `references/kafka.md` reference file and catalog entry in `SKILL.md`.
- `temporal_cloud` credential type — dynamic credential that provisions ephemeral Temporal Cloud API keys via an admin API key supplied through `secretRef.api_key` (no `config` block on the credential). Matching `temporal_cloud` privilege type with `grants[]` of `{namespace, permission}` where `permission` is one of `read`, `write`, `admin` and namespaces must be unique. New `references/temporal_cloud.md` reference file and catalog entry in `SKILL.md`.

## [hush-uam-v0.2.0] - 2026-05-20

Tracks `am.hush.security/v1alpha1` as shipped in hush-uam ≥ v0.11.0 / helm chart `hush-am` ≥ 0.16.0.

### Added

- Support `remoteName` + `type` as a third form for `accessCredentialRef` and `accessPrivilegeRefs`, alongside the existing `name` and `id` forms. Resolves an externally-managed credential or privilege by its Hush UAM display name. Requires hush-uam ≥ v0.11.0 and helm chart `hush-am` ≥ 0.16.0.
- `## Compatibility` section in `SKILL.md` with a per-feature version-floor table, plus a conditional installed-versions probe in the input flow: when the user reports an older cluster, the skill drops `remoteName` from the offered ref forms and emits an "upgrade to unlock" tip.
- Post-manifest warning when `remoteName` is used, covering both the version floor and the name+type uniqueness requirement (ambiguous resolution turns the policy status to `error`).

### Fixed

- `plaintext` credentials no longer emit an empty `config: {}` block — the type has no `config` fields, so the key should be omitted entirely.
- `mysql` / `mariadb`: `ssl_mode` enum values are now the lowercase-hyphenated wire form (`disabled`, `preferred`, `required`, `verify-ca`, `verify-identity`) instead of the uppercase Python enum names — the backing enum is `HyphenatedStrEnum`.
- `snowflake`: `auth_method` value `key-pair` (hyphenated) instead of `key_pair` — same `HyphenatedStrEnum` rule. Connection-string-template note updated to match.
- `kv`: config field is `keys: List[str]` (flat string list), not `items: [{key: <name>}]`. The previous shape would have been rejected by the Pydantic model.
- `elasticsearch`: `port` and `tls` are required (no Pydantic defaults); they were previously labeled `# default` and `tls` was emitted as `false`, which is a poor production recommendation. Now labeled as required with `tls: true` shown in the example.

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

[Unreleased]: https://github.com/hushsecurity/agent-skills/compare/hush-uam-v0.3.0...HEAD
[hush-uam-v0.3.0]: https://github.com/hushsecurity/agent-skills/releases/tag/hush-uam-v0.3.0
[hush-uam-v0.2.0]: https://github.com/hushsecurity/agent-skills/releases/tag/hush-uam-v0.2.0
[hush-uam-v0.1.0]: https://github.com/hushsecurity/agent-skills/releases/tag/hush-uam-v0.1.0
