---
name: hush-uam-manifest
description: Author Kubernetes manifests for Hush UAM (Universal Access Management) — AccessCredential, AccessPrivilege, AccessPolicy CRDs from Hush Security. Use this skill whenever the user asks about Hush, hush-am, hush-uam, Hush policies/credentials/privileges, the `am.hush.security` API group, or wants to create/generate/scaffold k8s YAML for any access credential, access privilege, or access policy in a Hush deployment.
---

# Hush UAM Kubernetes Manifest Author

Generate well-formed CRD manifests for the Hush UAM (Universal Access Management) operator from Hush Security. The CRDs live under the API group `am.hush.security/v1alpha1` and cover three resources: `AccessCredential`, `AccessPrivilege`, and `AccessPolicy`. The operator forwards `spec.config` straight to the Hush API, so the keys inside `config` must match what the Hush API expects for the chosen `type`.

## ⚠️ CRITICAL: namespace is fixed

**Every manifest you generate MUST use `metadata.namespace: hush-security`.** The Hush operator only watches the `hush-security` namespace; resources placed anywhere else will silently fail to sync with the Hush platform. This applies to:

- `AccessCredential`, `AccessPrivilege`, `AccessPolicy` CRs
- Any companion `Secret` you generate alongside

**Do not** ask the user which namespace to use, do not accept overrides, and do not infer a namespace from the prompt. If the user explicitly asks for a different namespace, push back and explain that the operator only watches `hush-security`.

**Note:** this constraint is about *where the CRs live*. It is NOT the same as the workload's namespace, which appears in `attestationCriteria` entries of type `k8s:ns` and refers to where the *workload consuming the credential* runs. Those two namespaces are independent — the workload almost always lives in a different namespace than `hush-security`.

## Reference files

Every supported credential type has its own reference file at `references/<type>.md` documenting the credential schema, the matching privilege schema (or "no privilege type" note), the auth-principal permissions, and any type-specific notes (auth method choices, connection-string templates, etc.). **You MUST read the matching `references/<type>.md` before emitting a manifest** for that type — values are not interchangeable and inventing names will produce broken manifests.

See the **Type catalog** section below for the full list with one-liner descriptions and links.

For privilege types with very large enumerated value lists, additional reference docs live alongside the per-type files:

- `references/datadog-scopes.md` — full Datadog scope list (~600 scopes)
- `references/sendgrid-scopes.md` — full SendGrid scope list
- `references/twilio-permissions.md` — full Twilio permission paths
- `references/redis-commands.md` — full Redis command list
- `references/snowflake-privileges.md` — full Snowflake privilege map per resource type

The per-type file points you to these when needed.

## Compatibility

The skill targets the **current** hush-uam and `hush-am` helm chart releases. Everything in the schema and reference files works against any reasonably recent installation, with one exception: a small number of fields were added in specific versions, listed below. If a manifest you generate uses one of these fields against a cluster running an older version, the CRD will reject the field at apply time.

| Feature                                  | Min hush-uam | Min `hush-am` chart |
| ---------------------------------------- | ------------ | ------------------- |
| `remoteName` + `type` cred/privilege ref | v0.11.0      | 0.16.0              |

Older clusters can still use everything else in the skill — `name`/`id` refs, every credential type, every delivery mode. The version question is per-feature, not per-skill.

## Inputs to confirm before generating

Walk through these with the user in this order. Skip the items that don't apply to the artifacts being generated.

**Policy-first when the prompt is policy-shaped.** When the user says "create a policy for X", they care about *the policy* — who gets access and how creds are delivered. Ask the policy plumbing first (attestation, delivery), then the credential details, then the privilege. Don't bury the policy questions behind a wall of credential field prompts; that's the opposite of what the user asked for.

**Finish a resource before starting the next.** This is a strict rule. When you're gathering inputs for a resource (policy, credential, or privilege), collect *both* the structural decisions *and* the specific values for that resource before moving on. Don't ask the structural question for one resource (e.g. "which attestation pattern?") in the same round as a structural question for a different resource (e.g. "which auth method for the credential?"). Worse, don't defer the values until later: if the user picks `k8s:ns + k8s:sa` for attestation, ask in the same round (or the very next, before touching credential details) for the workload namespace and SA name. Same for delivery — once they pick "split env vars", immediately ask which env var name maps to which credential field.

### How to ask — use `AskUserQuestion` for everything

Use the `AskUserQuestion` tool for **every** input, not just multiple-choice decisions. The tool always offers an `Other` option that lets the user type a custom value, so it works equally well for free-form fields like metadata names, project IDs, hostnames, env var names. The user gets one consistent UI for the whole interview instead of being toggled between structured choices and "reply with numbers" prose.

**Never ask about namespace** — it's always `hush-security` (see the critical constraint above).

Rules:

- **Always batch** up to 4 questions per `AskUserQuestion` call. Cap is 4 — when there are more inputs to gather, fire a second call after answers come back.
- **Each question gets 2-4 named options.** Mark the most likely choice with `(Recommended)` and put it first. The tool auto-adds `Other` for free-form input — don't list it as one of your options.
- **For free-form fields with a sensible default** (e.g. cred name derived from type like `gemini-prod`), present the default as the recommended option and a generic alternative (e.g. `Use a different name`) as the second. The user clicks through or picks `Other` to type a custom value.
- **For required fields with no sensible default** (e.g. GCP `project_id`, hostnames, AWS account ARNs), don't fake a default. Use options like `I'll provide it now` plus a contextual alternative (`Use environment-specific value`) — the user picks `Other` and types it. Don't lump these into a `defaults` shortcut.
- **Group by resource.** All policy questions (structural + values) come first if a policy is being generated. Then all credential questions. Then all privilege questions. Don't interleave resources. Within a resource, structural choices (e.g. attestation pattern, delivery method, cred auth method) come right before the values they unlock (e.g. namespace + SA names for `k8s:ns + k8s:sa`, or env var name → cred field mappings for `env splitted`).
- **Skip what you already know** from the prompt — but be conservative about what counts as "known". `type` is genuinely pinned by phrases like "policy for postgres" — don't re-ask. **Scope is *not* pinned** by mentioning a policy: "I want a policy for X" could mean just the policy (referring to existing cred/privilege via `id` or `name`), cred+policy, or the full trio. Always ask scope when a policy is involved, even if the trio is the most likely answer; present the trio as Recommended but list the other options explicitly so the user can opt out.

### `defaults` shortcut

Offer a `defaults` shortcut **only** for fields that genuinely have defaults — CR names, attestation pattern, env var name, delivery type, etc. Required-no-default values (project_id, host, port for non-standard ports, the workload's namespace and SA for attestation, etc.) must be asked individually; never silently fill them in. Namespace is fixed (`hush-security`) and is not part of the shortcut.

Example: "Or say `defaults` and I'll use: cred `gemini-prod`, policy `gemini-app-policy`, attestation by `k8s:ns` + `k8s:sa` (you tell me the workload's namespace + SA), env delivery as `GEMINI_API_KEY` — you still need to provide the GCP project ID."

### Canonical input order (resource-grouped, policy-first)

The order below is grouped by resource. Within each resource, structural choices come first and the values they unlock follow immediately — never defer values to a later resource's round.

#### 0. Meta

- **Scope** — always ask when a policy is involved. Present these options (with the trio as Recommended for greenfield use cases):
  - Full trio: `AccessCredential` + `AccessPrivilege` + `AccessPolicy` (Recommended)
  - `AccessCredential` + `AccessPolicy` (cred is new, privilege already exists or isn't needed for this type)
  - `AccessPolicy` only (cred and privilege already exist; the policy will reference them by `id` or `name`)
  - Single resource (`AccessCredential` only / `AccessPrivilege` only / `AccessPolicy` only)

  Don't auto-assume the trio. The user might already have the cred and privilege managed via Hush API/UI/Terraform and only want a policy CR to wire attestation + delivery for a specific workload. If they pick "policy only" or "cred + policy", remember to ask how the unowned references should be expressed: `name` (CR in `hush-security`), `id` (managed externally), or `remoteName` + `type` (managed externally, referred to by its Hush UAM display name) — see "Referencing credentials and privileges".
- **Installed versions** — *conditional, optional.* Ask only when the scope answer implies externally-managed refs (`AccessPolicy` only, `AccessCredential + AccessPolicy`, or a single-resource policy that references existing externals). Skip for the fresh-trio path — every ref will be `name`, so the version doesn't change anything. Present a single `AskUserQuestion` with options like `Latest (Recommended)`, `Older — I'll tell you the versions`, prompting for **hush-uam** version and **`hush-am` chart** version when the user picks "older". Behaviour:
  - **Latest / unanswered / hush-uam ≥ v0.11.0 and chart ≥ 0.16.0** → offer all three ref forms (`name`/`id`/`remoteName`+`type`). Still emit the version requirement in the post-manifest note as a sanity check.
  - **hush-uam < v0.11.0 OR chart < 0.16.0** → drop `remoteName` from the ref-form options; only offer `name`/`id`. Append a one-line tip after the manifest: "upgrade to hush-uam ≥ v0.11.0 and chart ≥ 0.16.0 to also reference externals by display name (`remoteName` + `type`)."
- **Type** — `postgres`, `gemini`, `aws_access_key`, etc. Skip if implied by the prompt.

#### 1. Policy (skip if no policy is being generated)

Walk the user through every policy decision before touching the credential.

- **Policy CR name** — default to `<type>-<purpose>-policy` (e.g. `pg-app-policy`).
- **Attestation criteria** — pattern *and* values together.
  - First the pattern: which K8s identity dimensions to match? Common starter for K8s: `k8s:ns` + `k8s:sa`. Available types: `k8s:ns`, `k8s:sa`, `k8s:pod-label` (requires `key`), `k8s:pod-name`, `k8s:container-name`. At least one required.
  - **Immediately after the pattern is chosen**, ask for the value of each criterion the user picked — workload namespace, SA name, label key+value, etc. Don't move on until each chosen criterion has its value.
- **Delivery config** — type *and* item details together.
  - First the type: `env` (split vars) / `env` (connection-string template) / `volume` / `sdk` / matching WIF type. For DB-style creds, the connection-string template is usually the right default.
  - **Immediately after the type is chosen**, ask for the item-level details that depend on the choice:
    - `env` (split): one env var name per credential field to expose (e.g. `POSTGRES_USERNAME`, `POSTGRES_PASSWORD`).
    - `env` (template): the single env var name (e.g. `DATABASE_URL`).
    - `volume`: mount point + a relative file path per item.
    - `sdk`: the secret name + one in-SDK key name per item.
    - WIF: `role_arn` / pool details / `subject_kind` / `subject` as appropriate for the federation type.
- **`enabled` management** — toggle outside K8s (Recommended, omit `spec.enabled`) or reconcile in K8s (set it). See "How `enabled` interacts with drift correction".

#### 2. Credential (skip if no credential is being generated, or the policy refers to an existing credential by `id`/`name`)

All credential decisions in one block — structural choices, field values, and secret strategy.

- **Credential CR name** — default to `<type>-<env>` style (e.g. `gemini-prod`, `pg-prod`).
- **Type-specific structural decisions** (only applicable to some types — see `references/<type>.md`): GCP auth method (federation vs uploaded key) for `gemini`/`gcp_sa`/`apigee`, `service_account_bound` for `gemini`, `auth_method: password|key_pair` for `snowflake`, `engine: redis|elasticache|aiven` for `redis` (immutable after create; `elasticache` needs `cache_engine: redis|valkey`, `aiven` needs `project`+`service_name` and takes no `cache_engine`), `engine: native|aiven` for `kafka` (immutable after create), `client_id+client_secret` vs `public_key+private_key` for `mongodb_atlas`, etc. Ask the structural choice and immediately follow with any extra values it requires.
- **Field values** — all required non-sensitive fields the type expects. For `postgres`: `host`, `port`, `db_name`, `ssl_mode`, `username`. Pull the per-type field list and defaults from `references/<type>.md`. Volunteer defaults inline ("port — default 5432") to keep the conversation tight.
- **Secret source** (skip if the type has no `secretRef`).
  - Existing Secret or generate alongside? Default to `secretRef` over inlining.
  - **Existing Secret** → ask for the *exact key names* in that Secret. Always emit `keyMappings`.
  - **Generate alongside** → use canonical key names and skip `keyMappings`.

#### 3. Privilege (skip for no-privilege types: `plaintext`, `kv`, `gemini`, `bedrock`, `aws_wif`, `gcp_wif`, `azure_wif`)

- **Privilege CR name** — default to `<type>-<purpose>` (e.g. `pg-readonly`).
- **Privilege configuration** — type-specific shape from `references/<type>.md`. Offer well-known presets when the type has them (e.g. read-only vs read-write for SQL). For privileges with very large enumerated lists (datadog, sendgrid, twilio, redis commands, snowflake), confirm scope/permission/command names with the user and load the matching oversized reference file (`references/<file>.md`) before generating.

### Batching strategy

Use one or more `AskUserQuestion` calls per resource. **Never split a resource across rounds with another resource's questions in between.** A typical trio for a policy-shaped prompt looks like:

- **Round 1 — meta + policy structural choices**: scope (if not implied), policy CR name, attestation pattern, delivery type. (`enabled` management can fit here too if there's room.)
- **Round 2 — policy values**: workload namespace + SA names (or whatever the chosen attestation pattern needs), per-item delivery details (env var names, file paths, etc.) for the chosen delivery type. This round depends on Round 1's answers.
- **Round 3 — credential**: credential CR name, type-specific structural choice (when applicable), required field values, secret source. (May need a follow-up round if "existing Secret" is picked, to ask for the exact key names.)
- **Round 4 — privilege**: privilege CR name, preset choice, custom specifics if needed.

Skip rounds that don't apply (e.g. no privilege round for gemini). Combine rounds when possible (the cap is 4 questions per call) but **never combine across resources**. If Round 2 doesn't fit alongside Round 1's leftovers, fire Round 2 as its own call.

## CRD shape

### AccessCredential

```yaml
apiVersion: am.hush.security/v1alpha1
kind: AccessCredential
metadata:
  name: <metadata-name>             # decoupled from spec.name
  namespace: hush-security          # FIXED — never change
spec:
  name: <display-name>              # what the API sees
  type: <type>                      # see "Type catalog" section
  description: <optional>
  config:                           # non-sensitive fields go here; OMIT entirely for `plaintext` (no config fields)
    <field>: <value>
  secretRef:                        # only if the type has sensitive fields
    name: <k8s-secret-name>
    keyMappings:                    # see "How keyMappings behaves" below
      <expected-field>: <secret-key>
```

### How `keyMappings` behaves

`keyMappings` is **not just a rename map — it's also a filter.** The two modes:

- **Without `keyMappings`:** the operator forwards **every key** in the Secret to the Hush API as-is. If the Secret has any keys the API doesn't recognize for that credential type (e.g. `username`, `created_at`, `rotation_id`, audit metadata, an unrelated key the team stored there), the create/update call **will fail**. This works only when the Secret was specifically created with exactly the canonical key names and nothing else.

- **With `keyMappings`:** only the keys mentioned in the mapping are forwarded. Everything else in the Secret is ignored. Each entry is `<expected-field>: <secret-key>` — the left side is what the Hush API expects, the right side is the actual key in the K8s Secret. Even an *identity* mapping (e.g. `password: password`) is valid and useful — it explicitly opts in to that one key and filters out the rest.

### Recommended pattern

- **Generating the Secret alongside the manifest** → use canonical key names (`password`, `api_key`, etc.), skip `keyMappings`. You control the Secret, so there are no extra keys.
- **Referring to an existing Secret** → ask the user for the actual key names and **always emit `keyMappings`**, even if every entry is identity. This avoids silent failures when the Secret has extra keys, and makes the manifest self-documenting.

```yaml
# Existing Secret with extra keys — keyMappings filters to just what's needed
secretRef:
  name: pg-creds
  keyMappings:
    password: password           # identity map — still required to filter out extras
```

```yaml
# Existing Secret with non-canonical keys — keyMappings remaps and filters
secretRef:
  name: pg-creds
  keyMappings:
    password: db_pass
```

### AccessPrivilege

```yaml
apiVersion: am.hush.security/v1alpha1
kind: AccessPrivilege
metadata:
  name: <metadata-name>
  namespace: hush-security          # FIXED — never change
spec:
  name: <display-name>
  type: <type>
  description: <optional>
  config:
    <type-specific fields, see catalog>
```

There is no `secretRef` on privileges.

### AccessPolicy

```yaml
apiVersion: am.hush.security/v1alpha1
kind: AccessPolicy
metadata:
  name: <metadata-name>
  namespace: hush-security          # FIXED — never change. The CR lives here regardless of where the workload runs.
spec:
  name: <display-name>
  description: <optional>
  # enabled: true                 # OPTIONAL — see "How `enabled` interacts with drift correction" below
  accessCredentialRef:            # exactly one of `name`, `id`, or `remoteName`+`type` — see "Referencing creds/privileges" below
    name: <cred-cr-name>
  accessPrivilegeRefs:            # OMIT for types that don't take privileges (see below)
    - name: <priv-cr-name>        # exactly one of `name`, `id`, or `remoteName`+`type` per entry
  attestationCriteria:            # min 1
    - type: k8s:ns                # one of: k8s:ns, k8s:sa, k8s:pod-label, k8s:pod-name, k8s:container-name
      value: <workload-namespace> # the *workload's* namespace — NOT hush-security
    - type: k8s:pod-label
      key: <label-key>            # required only for k8s:pod-label
      value: <label-value>
  deliveryConfig:
    type: env                     # one of: env, volume, sdk, aws_wif, gcp_wif, azure_wif
    config:
      <delivery-type-specific>
```

## How `enabled` interacts with drift correction

The Hush operator reconciles the policy on the platform back to whatever the manifest declares — if someone changes a managed field via the Hush API, UI, or Terraform, the operator restores it. **`enabled` is the one field this can be opted out of**, because flipping a policy on/off is often an operational action (e.g. on-call temporarily disabling a misbehaving policy) that shouldn't fight the controller.

The rule is based on whether `spec.enabled` is present in the manifest:

- **`enabled` omitted** (default, recommended) — the operator does not reconcile this field. Anyone can flip the policy on/off via the Hush API/UI/Terraform without the operator restoring it. Use this when the manifest is the source of truth for *what* the policy is, but enable/disable is controlled elsewhere.
- **`enabled: true` or `enabled: false`** — the operator reconciles this field too. If it drifts (someone disables a policy declared `enabled: true`), the operator flips it back. Use this when you want declarative control over enable/disable as well, e.g. when the policy is defined alongside an app deployment that should always start enabled.

All other policy fields (`accessCredentialRef`, `accessPrivilegeRefs`, `attestationCriteria`, `deliveryConfig`, etc.) are always reconciled — drift on those fields is always restored to the manifest value.

**Default to omitting `enabled`.** Only include it when the user explicitly says they want declarative on/off control.

## Referencing credentials and privileges

`accessCredentialRef` and each entry of `accessPrivilegeRefs` accept **exactly one** of three forms — not zero, not more than one:

1. **`name`** — when the credential or privilege is also being managed in Kubernetes as a CR in the same namespace. The operator resolves it to its underlying ID.
2. **`id`** — when the credential or privilege was created outside Kubernetes (e.g. via the Hush API or UI) and exists only on the platform side, not as a CR. Use this when the user has the platform ID handy.
3. **`remoteName` + `type`** — when the credential or privilege was created outside Kubernetes and the user only knows it by its display name on the platform. The api-controller resolves the `remoteName`/`type` pair to an ID via Hush UAM within the deployment's scope. `type` is required here to disambiguate (e.g. `postgres`, `gemini`, `plaintext`, etc.). **Requires:** hush-uam ≥ v0.11.0, helm chart `hush-am` ≥ 0.16.0 — older clusters' CRDs reject this field. See the [Compatibility](#compatibility) section.

You can mix the three forms freely within a single policy — e.g. reference the credential by `name` (CR in this namespace) and the privilege by `remoteName` + `type` (managed externally, only known by name).

```yaml
# Both managed in K8s — refer by CR name
accessCredentialRef:
  name: pg-prod
accessPrivilegeRefs:
  - name: pg-readonly
```

```yaml
# Both managed externally with known IDs — refer by platform ID
accessCredentialRef:
  id: acr_abc123
accessPrivilegeRefs:
  - id: apr_xyz789
```

```yaml
# Both managed externally, referred to by remote display name + type
accessCredentialRef:
  remoteName: pg-prod
  type: postgres
accessPrivilegeRefs:
  - remoteName: pg-readonly
    type: postgres
```

```yaml
# Mixed — credential by CR name, privilege by remoteName + type
accessCredentialRef:
  name: pg-prod
accessPrivilegeRefs:
  - remoteName: pg-readonly
    type: postgres
```

When the user is unclear, default to `name` if you're also generating the matching credential/privilege CR; otherwise ask whether they have the platform `id` or only the display name (`remoteName`).

### `remoteName` ambiguity → error status

`remoteName` + `type` is resolved by Hush UAM at reconcile time. If **more than one** credential (or privilege) with that exact display name *and* that exact type exists in the deployment's scope, the resolution is ambiguous and the policy's status will turn to **error** — the operator won't pick one arbitrarily. When you generate a manifest that uses `remoteName`, surface this risk to the user in a short post-manifest note so they can confirm the name is unique before applying.

## Types that don't take privileges

For these credential types, the `AccessPolicy` MUST omit `accessPrivilegeRefs`:

- `plaintext`, `kv` — static credentials.
- `gemini`, `bedrock` — privileges are not modeled for these providers.
- `aws_wif`, `gcp_wif`, `azure_wif` — workload identity federation; access is enforced by the cloud provider.

For all other dynamic types, the policy requires exactly one privilege of the matching type.

## deliveryConfig variants

```yaml
# env — inject as environment variables
deliveryConfig:
  type: env
  config:
    items:                         # min 1
      - name: POSTGRES_USERNAME    # env var name; must match ^[a-zA-Z_][a-zA-Z0-9_]*$
        key: username              # credential field name
        type: key                  # or "template" — see "Templated values" below for connection-string-style delivery
```

```yaml
# volume — write into files at a mount point
deliveryConfig:
  type: volume
  config:
    mount_point: /var/run/secrets/db   # absolute path
    items:
      - path: username                  # relative path under mount_point
        key: username
        type: key
```

```yaml
# sdk — fetched via the Hush SDK at runtime
deliveryConfig:
  type: sdk
  config:
    secret_name: my-app-secret          # must match ^[a-zA-Z0-9/_+=.@-]+$
    items:
      - name: db_user
        key: username
        type: key
```

```yaml
# aws_wif — exchange for AWS credentials via STS
deliveryConfig:
  type: aws_wif
  config:
    role_arn: arn:aws:iam::123:role/my-role
    subject_kind: hush_subject          # or service_account
    subject: my-subject                 # required when subject_kind=hush_subject
```

```yaml
# gcp_wif — exchange for GCP credentials
deliveryConfig:
  type: gcp_wif
  config:
    subject_kind: hush_subject
    subject: my-subject
    service_account: optional@proj.iam.gserviceaccount.com
    service_account_token_lifetime: 3600
```

```yaml
# azure_wif — exchange for Azure tokens
deliveryConfig:
  type: azure_wif
  config:
    tenant_id: <uuid>
    client_id: <client-id>
    subject_kind: hush_subject
    subject: my-subject
```

WIF constraints:
- `k8s:container-name` attestation is **not** allowed with WIF delivery types.
- `subject_kind: service_account` requires both `k8s:ns` and `k8s:sa` attestation criteria.
- The credential `type` and the delivery `type` must match for WIF (e.g. an `aws_wif` credential needs an `aws_wif` delivery).

## Templated values (connection strings, composite values)

Each delivery item under `env`, `volume`, or `sdk` chooses between two `type` values:

- `type: key` — `key` is a credential field name; the delivered value is the raw field value.
- `type: template` — `key` is a template string with `${field}` placeholders; the delivered value is the rendered string.

Templates use Python's `string.Template` syntax (`${name}` or `$name`). Every variable must be a valid field on the credential — both *configured* fields (e.g. `host`, `port`, `db_name`) and *auto-generated* fields (e.g. `username`, `password` for dynamic credentials).

```yaml
# env delivery: a single DATABASE_URL env var built from credential fields
deliveryConfig:
  type: env
  config:
    items:
      - name: DATABASE_URL
        key: "postgresql://${username}:${password}@${host}:${port}/${db_name}"
        type: template
```

```yaml
# volume delivery: write a connection string to a file
deliveryConfig:
  type: volume
  config:
    mount_point: /var/run/secrets/db
    items:
      - path: connection-string
        key: "postgresql://${username}:${password}@${host}:${port}/${db_name}"
        type: template
```

You can mix `key` and `template` items in the same `items[]` list — e.g. expose username and password as separate env vars *and* a combined `DATABASE_URL`.

### Ready-made connection-string templates

These are validated patterns matching each credential type's actual field names. Drop them into `key:` with `type: template`.

| Credential type | Connection string template |
|---|---|
| `postgres` | `postgresql://${username}:${password}@${host}:${port}/${db_name}` |
| `mysql` | `mysql://${username}:${password}@${host}:${port}/${db_name}` |
| `mariadb` | `mariadb://${username}:${password}@${host}:${port}/${db_name}` |
| `mongodb` | `mongodb://${username}:${password}@${host}:${port}/${db_name}?authSource=${auth_source}` |
| `mongodb_atlas` | `mongodb+srv://${username}:${password}@${host}` |
| `redis` | `redis://${username}:${password}@${host}:${port}/${database}` |
| `rabbitmq` | `amqp://${username}:${password}@${host}:${port}/${vhost}` |
| `elasticsearch` | `http://${username}:${password}@${host}:${port}` |
| `snowflake` | `snowflake://${username}@${account}/${database}/${schema}?warehouse=${warehouse}&role=${role}` |

Notes:
- Field names in templates must match the credential schema exactly (e.g. `${db_name}` for postgres, **not** `${db}`).
- For `mongodb_atlas`, `username`/`password` are auto-generated (Atlas does not take user-supplied DB credentials), so they're available in templates even though they're not in the credential's `config`.
- For `snowflake` with `auth_method: key_pair`, the `${password}` placeholder won't resolve — use a separate item or omit credential auth from the connection string.
- For `redis` with `engine: elasticache`, the `${password}` placeholder is unavailable (ElastiCache uses AWS auth) — adjust the template accordingly.
- For `redis` with `engine: aiven`, `${username}`/`${password}`/`${host}`/`${port}` are auto-generated / resolved by Hush and available in templates, but there is no `${database}` (no selectable DB) — drop it from the connection string.

---

---

# Type catalog — read the matching reference file before generating

Each supported credential type has its own reference file in `references/<type>.md`. The file documents that type's credential `config`/`secretRef` shape, the matching privilege schema (or "no privilege type" note), the auth-principal permissions Hush needs, and any type-specific notes (auth method choices, connection-string templates, etc.).

**Workflow:** once the user has confirmed the type, **you MUST read the matching `references/<type>.md` before emitting any manifest or asking type-specific questions.** Don't try to recall fields from memory — types evolve and field names matter. The file is small and self-contained.

## All types

| Type | Privilege? | Reference file | Notes |
|---|---|---|---|
| `plaintext` | no | [`references/plaintext.md`](references/plaintext.md) | Static; single secret value |
| `kv` | no | [`references/kv.md`](references/kv.md) | Static; multiple named secret values |
| `postgres` | yes | [`references/postgres.md`](references/postgres.md) | DB |
| `mysql` | yes | [`references/mysql.md`](references/mysql.md) | DB |
| `mariadb` | yes | [`references/mariadb.md`](references/mariadb.md) | DB |
| `mongodb` | yes | [`references/mongodb.md`](references/mongodb.md) | DB |
| `mongodb_atlas` | yes | [`references/mongodb_atlas.md`](references/mongodb_atlas.md) | DB; OAuth or API Key auth |
| `redis` | yes | [`references/redis.md`](references/redis.md) | KV; `redis`, `elasticache`, or `aiven` engine (`config.engine`, fixed at create) |
| `elasticsearch` | yes | [`references/elasticsearch.md`](references/elasticsearch.md) | Search |
| `rabbitmq` | yes | [`references/rabbitmq.md`](references/rabbitmq.md) | Messaging |
| `snowflake` | yes | [`references/snowflake.md`](references/snowflake.md) | Data warehouse; password or key_pair auth |
| `openai` | yes | [`references/openai.md`](references/openai.md) | AI |
| `gemini` | **no** | [`references/gemini.md`](references/gemini.md) | AI; GCP-backed; SA-bound option |
| `bedrock` | **no** | [`references/bedrock.md`](references/bedrock.md) | AWS-backed AI |
| `grok` | yes | [`references/grok.md`](references/grok.md) | AI |
| `gcp_sa` | yes | [`references/gcp_sa.md`](references/gcp_sa.md) | GCP Service Account; federated or uploaded auth |
| `azure_app` | yes | [`references/azure_app.md`](references/azure_app.md) | Azure Application |
| `aws_access_key` | yes | [`references/aws_access_key.md`](references/aws_access_key.md) | AWS IAM users |
| `apigee` | yes | [`references/apigee.md`](references/apigee.md) | GCP Apigee; federated or uploaded auth |
| `datadog` | yes | [`references/datadog.md`](references/datadog.md) | + see `references/datadog-scopes.md` |
| `gitlab` | yes | [`references/gitlab.md`](references/gitlab.md) | |
| `salesforce` | yes | [`references/salesforce.md`](references/salesforce.md) | |
| `sendgrid` | yes | [`references/sendgrid.md`](references/sendgrid.md) | + see `references/sendgrid-scopes.md` |
| `twilio` | yes | [`references/twilio.md`](references/twilio.md) | + see `references/twilio-permissions.md` |
| `temporal_cloud` | yes | [`references/temporal_cloud.md`](references/temporal_cloud.md) | Workflow engine; no `config` block, admin API key in `secretRef` |
| `kafka` | yes | [`references/kafka.md`](references/kafka.md) | Messaging; `native` or `aiven` engine (`config.engine`, fixed at create) |
| `aws_wif` | **no** | [`references/aws_wif.md`](references/aws_wif.md) | Federation |
| `gcp_wif` | **no** | [`references/gcp_wif.md`](references/gcp_wif.md) | Federation |
| `azure_wif` | **no** | [`references/azure_wif.md`](references/azure_wif.md) | Federation |

Types marked **no** in the Privilege column don't take an `AccessPrivilege` — the `AccessPolicy` for these MUST omit `accessPrivilegeRefs`.

## Oversized enumeration files

Some privilege types have very long enumerations (hundreds of scopes/commands/permissions). The per-type reference file links to these as needed:

- `references/datadog-scopes.md` — full Datadog scope list
- `references/sendgrid-scopes.md` — full SendGrid scope list
- `references/twilio-permissions.md` — full Twilio permission paths
- `references/redis-commands.md` — full Redis command list (categories are inline in `redis.md`)
- `references/snowflake-privileges.md` — full Snowflake privilege map per resource type

Load these only when generating that specific privilege type — the per-type file will tell you when.

## Adding a new type

When a new credential type is added to Hush, add a new `references/<type>.md` following the same structure as existing files (Credential / Privilege / Required permissions on the auth principal / type-specific notes). Then add a row to the table above. No other files need to change.

# Workflow

1. **Identify what's being created.** Credential alone? Privilege alone? Or all three? If the user only mentions the credential, ask whether they also want the matching privilege and policy — typical full setup is all three.
2. **Pick the type** and confirm with the user.
3. **Split fields** between `config` (non-sensitive) and `secretRef` (sensitive), per `references/<type>.md`.
4. **Decide the Secret strategy:**
   - If you're generating the Secret alongside the manifest, use canonical key names and skip `keyMappings`.
   - If the user references an existing Secret, ask for its actual key names and **emit `keyMappings` for every sensitive field** (identity map is fine). This avoids the "extra keys cause API failure" footgun.
5. **For policies**, select the right `deliveryConfig` and remember to omit `accessPrivilegeRefs` for the no-privilege types. Decide how each unowned reference is expressed: `name` (CR in `hush-security`), `id` (managed externally, ID known), or `remoteName` + `type` (managed externally, only display name known).
6. **Assemble the manifest** with explicit `apiVersion`/`kind`/`metadata.namespace: hush-security`. Default to multi-document YAML (`---` separator) when generating cred + privilege + policy together. Companion `Secret` documents must also live in `hush-security` so the operator can read them.
7. **For sensitive fields**, generate a `kind: Secret` document alongside the credential, or note that the user must run `kubectl create secret generic <name> --from-literal=<key>=<value>` first.
8. **Surface the required auth-principal permissions** for the credential's target system. After the manifest, print a clearly-labeled **"Required permissions on the auth principal"** block listing what the GCP SA / IAM role / DB user / API token needs in order for Hush to provision and rotate ephemeral credentials. Pull the list from `references/<type>.md` — every per-type file has a "Required permissions on the auth principal" section. If the per-type file lacks one or marks it "not applicable", say so explicitly to the user — don't invent permissions.
9. **If the manifest uses `remoteName`**, append a short post-manifest note covering both compatibility and uniqueness:
   - **Version floor** — the cluster must be running hush-uam ≥ v0.11.0 and helm chart `hush-am` ≥ 0.16.0; older CRDs reject the `remoteName` field at apply time.
   - **Uniqueness** — the `remoteName` + `type` pair must be unique within the deployment's scope, otherwise the policy status turns to error.

   Ask the user to confirm both before applying. (If the version probe in step 0 already established the cluster is on a recent release, you can shorten the version note to a brief reminder.)

# Validation gotchas

- `accessCredentialRef` and each entry of `accessPrivilegeRefs` accept exactly one of `name`, `id`, or `remoteName`+`type` (never two of these, never none). When using `remoteName` it must be paired with `type`.
- `remoteName` + `type` is resolved at reconcile time; if multiple remote entities share that name and type within the deployment, the policy status turns to **error**. Flag this to the user when you emit a `remoteName` reference.
- `remoteName` is only accepted by **hush-uam ≥ v0.11.0** / **chart `hush-am` ≥ 0.16.0**; older CRDs reject the field at apply time. See the [Compatibility](#compatibility) section.
- `attestationCriteria.key` is required iff `type: k8s:pod-label`; it must be omitted for the other criterion types.
- Delivery item names: env uses `^[a-zA-Z_][a-zA-Z0-9_]*$`; sdk uses `^[a-zA-Z0-9/_+=.@-]+$`; volume `path` is relative, cannot contain `..`, and cannot contain `hush.security`.
- Reserved env name prefixes `_HUSH` and `__HUSH` are rejected.
- Static credentials (`plaintext`, `kv`) cannot be referenced by a policy that has `accessPrivilegeRefs`.
- Privilege `type` must match credential `type`.
- The privilege list is constrained to a single privilege per policy.
- WIF delivery types only work with the matching WIF credential type (`aws_wif` ↔ `aws_wif`, etc.).
- **Secret with extra keys + no `keyMappings` → API failure.** Without `keyMappings`, every key in the K8s Secret is forwarded to the Hush API; any unrecognized key causes the create/update to fail. Emit `keyMappings` (identity is fine) whenever you reference a Secret you didn't generate.
- **Wrong namespace → silent sync failure.** All Hush UAM CRs (and any companion `Secret`) MUST live in `hush-security`. The operator only watches that namespace. Resources placed elsewhere are simply ignored — no error, just nothing happens. This is a hard rule; never override.

---

# Example: Postgres trio

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: pg-creds
  namespace: hush-security
type: Opaque
stringData:
  password: <pg-password>
---
apiVersion: am.hush.security/v1alpha1
kind: AccessCredential
metadata:
  name: pg-prod
  namespace: hush-security
spec:
  name: pg-prod
  type: postgres
  config:
    db_name: app
    host: pg.internal
    port: 5432
    ssl_mode: require
    username: app_user
  secretRef:
    name: pg-creds
---
apiVersion: am.hush.security/v1alpha1
kind: AccessPrivilege
metadata:
  name: pg-readonly
  namespace: hush-security
spec:
  name: pg-readonly
  type: postgres
  config:
    grants:
      - privileges: [SELECT]
        object_type: TABLE
        object_names: [public]
        all_in_schema: true
---
apiVersion: am.hush.security/v1alpha1
kind: AccessPolicy
metadata:
  name: pg-app-policy
  namespace: hush-security
spec:
  name: pg-app-policy
  # enabled is omitted — toggle via API/UI/Terraform without operator restoring drift
  accessCredentialRef:
    name: pg-prod
  accessPrivilegeRefs:
    - name: pg-readonly
  attestationCriteria:
    - type: k8s:ns
      value: app-namespace
    - type: k8s:sa
      value: app-sa
  deliveryConfig:
    type: env
    config:
      items:
        - name: PG_USER
          key: username
          type: key
        - name: PG_PASSWORD
          key: password
          type: key
```

## Variant: referencing an existing Secret

When `pg-creds` already exists and may contain other keys (e.g. `username`, `created_at`, rotation metadata), drop the inline `Secret` document above and use `keyMappings` on the credential to filter and map explicitly:

```yaml
apiVersion: am.hush.security/v1alpha1
kind: AccessCredential
metadata:
  name: pg-prod
  namespace: hush-security
spec:
  name: pg-prod
  type: postgres
  config:
    db_name: app
    host: pg.internal
    port: 5432
    ssl_mode: require
    username: app_user
  secretRef:
    name: pg-creds
    keyMappings:
      password: db_password    # or `password: password` if the existing key matches —
                               # still required to filter out unrelated keys in the Secret
```

# Example: Gemini (no privilege)

GCP auth via identity federation, generated API keys unbound — the simplest combination. No `secretRef`.

```yaml
apiVersion: am.hush.security/v1alpha1
kind: AccessCredential
metadata:
  name: gemini-prod
  namespace: hush-security
spec:
  name: gemini-prod
  type: gemini
  config:
    project_id: my-gcp-project
    service_account_bound: false
---
apiVersion: am.hush.security/v1alpha1
kind: AccessPolicy
metadata:
  name: gemini-app-policy
  namespace: hush-security
spec:
  name: gemini-app-policy
  # enabled is omitted — toggle via API/UI/Terraform without operator restoring drift
  accessCredentialRef:
    name: gemini-prod
  # NO accessPrivilegeRefs — gemini does not take privileges
  attestationCriteria:
    - type: k8s:ns
      value: app-namespace
  deliveryConfig:
    type: env
    config:
      items:
        - name: GEMINI_API_KEY
          key: api_key
          type: key
```

## Variant: Gemini with uploaded SA key + bound API keys

GCP auth via uploaded service account key, generated API keys bound to a Hush-managed service account. Both decisions opted in.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gemini-gcp-sa
  namespace: hush-security
type: Opaque
stringData:
  service_account_key: |
    {
      "type": "service_account",
      ...
    }
---
apiVersion: am.hush.security/v1alpha1
kind: AccessCredential
metadata:
  name: gemini-prod
  namespace: hush-security
spec:
  name: gemini-prod
  type: gemini
  config:
    project_id: my-gcp-project
    service_account_bound: true        # bind generated API keys to a created GCP SA
  secretRef:
    name: gemini-gcp-sa                # Hush uses this SA key to provision API keys
```

# Example: Policy referencing externally-managed credential

When the credential and privilege already exist on the Hush platform (created via API or UI), the policy refers to them by `id` — no companion CRs needed.

```yaml
apiVersion: am.hush.security/v1alpha1
kind: AccessPolicy
metadata:
  name: external-pg-policy
  namespace: hush-security
spec:
  name: external-pg-policy
  enabled: true                    # included here to demonstrate K8s-managed enable/disable; the operator will restore drift on this field
  accessCredentialRef:
    id: acr_01h8z9p7q2r5x3v6t4y2k1m9w8
  accessPrivilegeRefs:
    - id: apr_01h8z9p7q2r5x3v6t4y2k1m9w9
  attestationCriteria:
    - type: k8s:ns
      value: app-namespace
    - type: k8s:sa
      value: app-sa
  deliveryConfig:
    type: env
    config:
      items:
        - name: PG_USER
          key: username
          type: key
        - name: PG_PASSWORD
          key: password
          type: key
```
