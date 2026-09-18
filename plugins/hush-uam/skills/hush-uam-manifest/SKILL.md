---
name: hush-uam-manifest
description: Author Hush UAM (Universal Access Management) resources — AccessCredential, AccessPrivilege and AccessPolicy — as Kubernetes CRD manifests for the hush-uam operator, or as Terraform HCL for the hushsecurity/hush provider. Use this skill whenever the user asks about Hush, hush-am, hush-uam, Hush policies/credentials/privileges, the `am.hush.security` API group, `hush_access_policy` or any `hush_*_access_credential`/`hush_*_access_privilege` resource, terraform-provider-hush, or wants to create/generate/scaffold k8s YAML or Terraform for any access credential, access privilege, or access policy in a Hush deployment.
---

# Hush UAM Manifest Author

Generate well-formed Hush UAM (Universal Access Management) resources from Hush Security.
UAM covers three things — an **AccessCredential** (how Hush reaches a target system), an
**AccessPrivilege** (what the provisioned credential may do there), and an **AccessPolicy**
(which workload gets it, and how it is delivered).

These exist in two forms, and this skill writes both:

- **Kubernetes** — CRDs under `am.hush.security/v1alpha1`, reconciled by the hush-uam
  operator. See [`references/kubernetes.md`](references/kubernetes.md).
- **Terraform** — resources in the `hushsecurity/hush` provider. See
  [`references/terraform.md`](references/terraform.md).

The underlying model is the same either way: same credential types, same attestation
criteria, same delivery modes, same privilege shapes, same permissions needed on the auth
principal. Everything in this file applies to both. The two reference files above carry
what differs.

## Step 1: pick the target

**Always establish the target before anything else.** It changes the syntax, the secret
handling, and several structural decisions — generating the wrong one wastes the whole
interview.

Infer it from the repo when the evidence is clear, and say which you picked:

- `*.tf` files, a `.terraform/` directory, `terraform.tfstate`, or an existing
  `hush_*` resource → **Terraform**
- `kustomization.yaml`, `Chart.yaml`, a `k8s/` or `manifests/` directory, or existing
  `am.hush.security` YAML → **Kubernetes**
- Both, or neither → **ask**, with `AskUserQuestion`.

The user's own words override any inference: "terraform", "HCL", "provider" mean Terraform;
"manifest", "CRD", "kubectl", "GitOps" mean Kubernetes.

**Then read the matching reference file before emitting anything.** This is as binding as
the per-type rule below — the targets differ in ways you will get wrong from memory.

## Step 2: read the type reference

Every supported credential type has a reference file at `references/<type>.md` documenting
the credential schema, the matching privilege schema (or "no privilege type" note), the
auth-principal permissions, and any type-specific notes. **You MUST read the matching
`references/<type>.md` before emitting anything** for that type — values are not
interchangeable and inventing names produces broken output.

See the **Type catalog** below for the full list. Some privilege types have very large
enumerated value lists in their own files (`datadog-scopes.md`, `sendgrid-scopes.md`,
`twilio-permissions.md`, `redis-commands.md`, `snowflake-privileges.md`); the per-type file
points you to them when needed.

A type's reference file describes the shared model. Where its Terraform argument names or
enums diverge, the file says so under a `## Terraform` heading; if it has no such section,
the names match one-for-one.

## Compatibility

Most of what this skill generates works against any reasonably recent installation. A few
features have floors, and **the two targets fail differently**, which changes what you tell
the user.

### Kubernetes

- **Gated fields** (`remoteName`) fail at **apply** time — the CRD doesn't know the field,
  so `kubectl apply` itself errors. You can avoid this by offering a different manifest
  shape.
- **Gated `type`/`engine` values** fail at **reconcile** time — the CRD accepts them and
  the Hush API rejects the create afterwards. There is no alternative shape here, so
  generate what the user asked for and warn.

"Generate and warn" is for version gates only. When a request is something the target
cannot express at all — a provider gap, a blocked enum, a connection string for an engine
that has no `${password}` — do not emit it. Substitute the nearest working shape and say
plainly what was asked for and why it changed.

| Feature | Min hush-uam | Min `hush-am` chart |
| --- | --- | --- |
| `remoteName` + `type` cred/privilege ref | v0.11.0 | 0.16.0 |
| `kafka` credential type | v0.15.0 | 0.19.0 |
| `redis` engine `aiven` | v0.17.0 | 0.21.0 |
| `redis` engine `azure_managed_redis` | v0.18.0 | 0.22.1 |
| `temporal_cloud` credential type | — | 0.18.0 |
| `sendgrid` credential type | — | 0.15.0 |
| `salesforce` credential type | — | 0.14.0 |
| `azure_wif` credential type | — | 0.14.0 |
| `redis` engine `elasticache` | — | 0.14.0 |
| `rabbitmq` `auto_rotate_root` | — | 0.19.1 |
| a secret store at all *(Terraform only)* | — | 0.21.0 |
| an extended secret-store prefix *(Terraform only)* | — | 0.27.0 |

Every other credential type needs `hush-am` >= 0.13.0, the baseline. A `—` in the
hush-uam column means there is no separate operator floor — the API enforces it against
the access-manager version alone. Those rows apply to both targets **except** the two
marked *Terraform only*: secret stores have no Kubernetes counterpart at all.

### Terraform

- **Terraform >= 1.11** for the write-only secret pattern (`<field>_wo`). The provider
  itself declares `>= 1.3`; on an older Terraform the user must accept secrets in state.
- The type/engine floors above apply here too, but **only the `hush-am` chart column**.
  `hush-uam` is the Kubernetes operator; a Terraform-only customer does not run it, and
  quoting its version at them describes a requirement they do not have. These floors are
  enforced by the API against the access-manager version, so they surface at
  `terraform apply` after a clean plan.

Pin a provider version (`version = "~> 1.24"`); the repo's own examples do not, and an
unpinned `source` upgrades silently.

## Inputs to confirm before generating

Walk through these with the user in this order. Skip what doesn't apply.

**Policy-first when the prompt is policy-shaped.** When the user says "create a policy for
X", they care about *the policy* — who gets access and how creds are delivered. Ask the
policy plumbing first (attestation, delivery), then the credential details, then the
privilege. Don't bury the policy questions behind a wall of credential field prompts.

**Finish a resource before starting the next.** This is a strict rule. When gathering
inputs for a resource, collect *both* the structural decisions *and* the specific values
for it before moving on. Don't ask a structural question for one resource in the same round
as a structural question for another. Worse, don't defer the values: if the user picks
`k8s:ns + k8s:sa` for attestation, ask in the same round (or the very next) for the
workload namespace and SA name.

### How to ask — use `AskUserQuestion` for everything

Use `AskUserQuestion` for **every** input, not just multiple-choice decisions. It always
offers an `Other` option for free-form values, so it works equally well for metadata names,
project IDs, hostnames and env var names. The user gets one consistent UI instead of being
toggled between structured choices and "reply with numbers" prose.

Rules:

- **Always batch** up to 4 questions per call. Cap is 4 — fire a second call when there's
  more to gather.
- **Each question gets 2-4 named options.** Mark the most likely `(Recommended)` and put it
  first. The tool auto-adds `Other` — don't list it yourself.
- **For free-form fields with a sensible default** (e.g. a cred name like `gemini-prod`),
  present the default as the recommended option and a generic alternative second.
- **For required fields with no sensible default** (GCP `project_id`, hostnames, account
  ARNs), don't fake a default, and don't offer an option whose label is a promise rather
  than a value — `I'll provide it now` gets clicked, comes back as the answer, and has to
  be asked again. Say in the question text "pick Other and type it", and list only
  concrete options: a contextual guess (`billing` for the namespace of a billing service)
  or a clearly marked placeholder (`db.billing.internal — placeholder, replace before
  apply`). Don't lump these into a `defaults` shortcut.
- **Group by resource.** All policy questions first, then credential, then privilege.
  Within a resource, structural choices come right before the values they unlock.
- **Skip what you already know** from the prompt — but be conservative. `type` is genuinely
  pinned by "policy for postgres". **Scope is *not* pinned** by mentioning a policy: always
  ask scope when a policy is involved, presenting the trio as Recommended — unless the type
  takes no privilege or the credential already exists, in which case recommend the fitting
  narrower scope (see *Canonical input order*) — but list the alternatives so the user can
  opt out.
- **Never ask which namespace the CRs go in** — it is the namespace hush-am is installed
  in, `hush-security` in a standard installation; `references/kubernetes.md` names the one
  evidence-based exception. The *workload's* namespace, the `k8s:ns` attestation value, is
  a different thing and you always ask for it. (Terraform has no CR namespace; it has `deployment_ids` instead,
  which you *do* ask about.)

### `defaults` shortcut

Offer a `defaults` shortcut **only** for fields that genuinely have defaults — resource
names, attestation pattern, env var name, delivery type. Required-no-default values
(`project_id`, `host`, the workload's namespace and SA, the deployment for Terraform) must
be asked individually; never silently fill them in.

### Canonical input order

#### 0. Meta

- **Target** — Kubernetes or Terraform (step 1 above). Establish this first, always.
- **Scope** — always ask when a policy is involved:
  - Full trio: credential + privilege + policy (Recommended for greenfield)
  - Credential + policy (privilege already exists or isn't needed for this type)
  - Policy only (credential and privilege already exist)
  - Single resource

  When the type is already pinned and takes no privilege, drop the trio and recommend
  credential + policy. When the prompt says the credential already *exists*, recommend
  policy only instead of the trio.
- **Deployment** — *Terraform only, required.* `deployment_ids` is mandatory on every
  credential and policy, exactly one, and effectively immutable on credentials. Ask whether
  to manage `hush_deployment` here, reference a `hush_deployment` resource the repo already
  declares, look one up with a `data` source, or use a literal `dep-` ID. Then ask for the
  name or ID that choice needs. Skip for Kubernetes, where the deployment is implicit.
- **Realm** — *Terraform only, and only when the repo has no `provider "hush"` block yet.*
  `US` (Recommended, the default) or `EU`. Skip when a provider block already exists.
- **Version probe** — *conditional.*
  - *Kubernetes:* ask only when the scope implies externally-managed refs, since that is
    the only thing the `remoteName` floor affects. Skip on the fresh-trio path. Offer
    `Latest (Recommended)` and `Older — I'll tell you the versions`. On latest, unanswered,
    or hush-uam >= v0.11.0 with chart >= 0.16.0, offer all three ref forms and still name
    the floor in the post-generation note. Below either floor, offer only `name`/`id` and
    add a one-line tip that upgrading unlocks `remoteName` + `type`.
  - *Terraform:* ask whether they're on Terraform >= 1.11, since that decides whether
    secrets can use the write-only pattern or must land in state.
- **Type** — `postgres`, `gemini`, `aws_access_key`, etc. Skip if implied by the prompt.

#### 1. Policy (skip if no policy is being generated)

- **Policy name** — default to `<type>-<purpose>-policy` (e.g. `pg-app-policy`).
- **Attestation criteria** — pattern *and* values together.
  - The pattern first: which identity dimensions to match? Common starter: `k8s:ns` +
    `k8s:sa`. Available: `k8s:ns`, `k8s:sa`, `k8s:pod-label` (requires `key`),
    `k8s:pod-name`, `k8s:container-name`. At least one required. These five are the
    complete set on both targets — there are no cloud, host or process criteria.
  - **Immediately after**, ask for each chosen criterion's value — workload namespace, SA
    name, label key+value.
- **Delivery config** — type *and* item details together.
  - The type first: `env` (split vars), `env` (connection-string template), `volume`,
    `sdk`, or the matching WIF type. For DB-style creds the template is usually right.
  - **Immediately after**, ask the item-level details the choice unlocks: one env var name
    per field, or the single var name for a template, or mount point + file paths, or the
    SDK secret name + key names, or the WIF role/pool details.
- **`enabled`** — **target-dependent, and the advice is opposite.**
  - *Kubernetes:* default to omitting it, which opts out of drift correction.
  - *Terraform:* it defaults to `true` and is always reconciled; there is no opt-out. Don't
    offer one.

#### 2. Credential (skip if none is being generated)

- **Credential name** — default to `<type>-<env>` style (e.g. `pg-prod`).
- **Type-specific structural decisions** — see `references/<type>.md`: GCP auth method for
  `gemini`/`gcp_sa`/`apigee`, `auth_method` (`password` or `key-pair`) for `snowflake`, `engine` for `redis` and
  `kafka` (immutable after create), the auth pair for `mongodb_atlas`, etc. Ask the
  structural choice and immediately follow with any values it requires.
- **Version floor** — *conditional.* If the chosen type or engine has a row in
  [Compatibility](#compatibility), raise it here — this is the first point where type and
  engine are both known. **Never drop the user's chosen type or engine**; generate it and
  carry the floor into the post-generation note.
- **Field values** — all required non-sensitive fields. Pull the list and defaults from
  `references/<type>.md`. Volunteer defaults inline ("port — default 5432").
- **Secret handling** — **target-dependent.**
  - *Kubernetes:* sensitive fields always come from a `secretRef`; the question is whether
    to reference an existing Secret or generate a companion one. Default to generating.
    For an existing Secret, ask the exact key names and always emit `keyMappings`.
  - *Terraform:* write-only (`<field>_wo` + `<field>_wo_version`, fed from a `variable`) or
    a plain sensitive attribute that lands in state? Default to write-only, and remember
    the version companion is **required**, not optional.
- **Secret store** — *Terraform only, optional.* Ask whether to set `secret_store_id`.
  Skip for Kubernetes, which has no such concept.

#### 3. Privilege (skip for the no-privilege types)

- **Privilege name** — default to `<type>-<purpose>` (e.g. `pg-readonly`).
- **Privilege configuration** — type-specific shape from `references/<type>.md`. Offer
  well-known presets where they exist (read-only vs read-write for SQL). For the types with
  very large enumerations, confirm the names with the user and load the matching oversized
  reference file first.
- *Terraform:* there is **no `hush_mariadb_access_privilege`**. If the user wants a MariaDB
  privilege in Terraform, say so — it has to be created elsewhere and referenced by ID.

### Batching strategy

One or more `AskUserQuestion` calls per resource. **Never split a resource across rounds
with another resource's questions in between.** A typical trio:

- **Round 1 — meta**: target (if not inferred), scope, type (skip if the prompt pins it),
  deployment (Terraform only). Four at most on the Terraform path, three on Kubernetes.
  If the target itself has to be asked, deployment waits for the next round — it only
  exists once Terraform is confirmed.
- **Round 2 — policy structural**: policy name, attestation pattern, delivery type, and
  `enabled` on Kubernetes. Four on Kubernetes, three on Terraform.
- **Round 3 — policy values**: workload namespace + SA names, per-item delivery details.
- **Round 4 — credential**: name, type-specific structural choice, field values, secret
  handling, secret store (Terraform), and the Terraform >= 1.11 probe if secrets are
  involved. This exceeds 4 — split it across two calls.
- **Round 5 — privilege**: name, preset choice, specifics.

Skip rounds that don't apply. Combine where possible (cap is 4 per call) but **never
combine across resources**.

## Attestation criteria

Five types, identical on both targets:

| Type | Matches | `key` |
| --- | --- | --- |
| `k8s:ns` | the workload's namespace | must be absent |
| `k8s:sa` | its service account | must be absent |
| `k8s:pod-label` | a pod label | **required** |
| `k8s:pod-name` | the pod name | must be absent |
| `k8s:container-name` | the container name | must be absent |

At least one is required. `key` is required **if and only if** the type is
`k8s:pod-label` — supplying it on any other type is an error. Note that the namespace here
is the *workload's*, which on Kubernetes is almost never `hush-security`.

## Types that don't take privileges

For these credential types, the policy MUST omit privilege references entirely:

- `plaintext`, `kv` — static credentials.
- `gemini`, `bedrock` — privileges are not modeled for these providers.
- `aws_wif`, `gcp_wif`, `azure_wif` — federation; access is enforced by the cloud provider.

For all other dynamic types, the policy requires exactly one privilege of the matching
type. A policy carries **at most one** privilege on both targets.

## Delivery modes

Six, identical on both targets: `env`, `volume`, `sdk`, `aws_wif`, `gcp_wif`, `azure_wif`.
Exactly one per policy. A workload that needs two — say a file *and* an SDK secret — gets
two policies sharing the same credential, privilege and attestation. The syntax differs —
see the target reference file.

WIF constraints (enforced by the API on both targets):

- The credential type and the delivery type must match (`aws_wif` ↔ `aws_wif`), and WIF
  credentials cannot use `env`/`volume`/`sdk`.
- `k8s:container-name` attestation is **not** allowed with any WIF delivery.
- `subject_kind: service_account` requires both `k8s:ns` and `k8s:sa` criteria.
- `subject_kind: hush_subject` requires `subject`, and the (credential, subject) pair must
  be unique across policies.

Name and path rules, also enforced on both:

- env var names match `^[a-zA-Z_][a-zA-Z0-9_]*$`; the `_HUSH` and `__HUSH` prefixes are
  reserved.
- sdk names and `secret_name` match `^[a-zA-Z0-9/_+=.@-]+$`.
- volume `mount_point` is absolute and canonical; item paths are relative. **Neither** may
  contain `..` or `hush.security`.

## Templated values (connection strings, composite values)

Each delivery item chooses between two forms:

- **key** — the value is a credential field, delivered raw.
- **template** — the value is a string with `${field}` placeholders, rendered before
  delivery.

Templates use Python's `string.Template` syntax. Every variable must be a real field on the
credential — both *configured* fields (`host`, `port`, `db_name`) and *auto-generated* ones
(`username`, `password` for dynamic credentials). You can mix key and template items in one
policy — e.g. username and password as separate vars *and* a combined `DATABASE_URL`.

> **Terraform escaping:** HCL uses `${...}` itself, so every placeholder must be written
> `$${...}` in `.tf`. The table below is in Kubernetes form; double every `$` for Terraform.

| Credential type | Connection string template |
| --- | --- |
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

- Field names must match the credential schema exactly (`${db_name}` for postgres, **not**
  `${db}`).
- For `mongodb_atlas`, `username`/`password` are auto-generated and available in templates
  even though they're not configured fields.
- The `snowflake` template carries no `${password}` on purpose; with
  `auth_method: key-pair` there is none to resolve, so do not add one.
- For `redis` with `engine: elasticache`, `${password}` is unavailable (AWS auth).
- For `redis` with `engine: aiven`, there is no `${database}` — drop it.
- For `redis` with `engine: azure_managed_redis`, **do not use a connection string at
  all** — deliver split items instead; see [`references/redis.md`](references/redis.md).

---

# Type catalog — read the matching reference file before generating

On Terraform the type is the resource name: `hush_<type>_access_credential` and
`hush_<type>_access_privilege`. On Kubernetes it is `spec.type` on the CR.

| Type | Privilege? | Reference file | Notes |
|---|---|---|---|
| `plaintext` | no | [`references/plaintext.md`](references/plaintext.md) | Static; single secret value |
| `kv` | no | [`references/kv.md`](references/kv.md) | Static; multiple named secret values |
| `postgres` | yes | [`references/postgres.md`](references/postgres.md) | DB |
| `mysql` | yes | [`references/mysql.md`](references/mysql.md) | DB |
| `mariadb` | yes¹ | [`references/mariadb.md`](references/mariadb.md) | DB |
| `mongodb` | yes | [`references/mongodb.md`](references/mongodb.md) | DB |
| `mongodb_atlas` | yes | [`references/mongodb_atlas.md`](references/mongodb_atlas.md) | DB; OAuth or API Key auth |
| `redis` | yes | [`references/redis.md`](references/redis.md) | KV; `redis`, `elasticache`, `aiven`, or `azure_managed_redis` engine, fixed at create |
| `elasticsearch` | yes | [`references/elasticsearch.md`](references/elasticsearch.md) | Search |
| `rabbitmq` | yes | [`references/rabbitmq.md`](references/rabbitmq.md) | Messaging |
| `snowflake` | yes | [`references/snowflake.md`](references/snowflake.md) | Data warehouse; password or key-pair auth |
| `openai` | yes | [`references/openai.md`](references/openai.md) | AI |
| `gemini` | **no** | [`references/gemini.md`](references/gemini.md) | AI; GCP-backed; SA-bound option |
| `bedrock` | **no** | [`references/bedrock.md`](references/bedrock.md) | AWS-backed AI |
| `grok` | yes | [`references/grok.md`](references/grok.md) | AI |
| `gcp_sa` | yes | [`references/gcp_sa.md`](references/gcp_sa.md) | GCP Service Account |
| `azure_app` | yes | [`references/azure_app.md`](references/azure_app.md) | Azure Application |
| `aws_access_key` | yes | [`references/aws_access_key.md`](references/aws_access_key.md) | AWS IAM users |
| `apigee` | yes | [`references/apigee.md`](references/apigee.md) | GCP Apigee |
| `datadog` | yes | [`references/datadog.md`](references/datadog.md) | + `references/datadog-scopes.md` |
| `gitlab` | yes | [`references/gitlab.md`](references/gitlab.md) | |
| `salesforce` | yes | [`references/salesforce.md`](references/salesforce.md) | |
| `sendgrid` | yes | [`references/sendgrid.md`](references/sendgrid.md) | + `references/sendgrid-scopes.md` |
| `twilio` | yes | [`references/twilio.md`](references/twilio.md) | + `references/twilio-permissions.md` |
| `temporal_cloud` | yes | [`references/temporal_cloud.md`](references/temporal_cloud.md) | Admin API key in the secret |
| `kafka` | yes | [`references/kafka.md`](references/kafka.md) | Messaging; `native` or `aiven` engine, fixed at create |
| `aws_wif` | **no** | [`references/aws_wif.md`](references/aws_wif.md) | Federation |
| `gcp_wif` | **no** | [`references/gcp_wif.md`](references/gcp_wif.md) | Federation |
| `azure_wif` | **no** | [`references/azure_wif.md`](references/azure_wif.md) | Federation |

¹ `mariadb` has a privilege type on Kubernetes and the API, but **Terraform has no
`hush_mariadb_access_privilege` resource**.

## Adding a new type

Add `references/<type>.md` following the existing structure (Credential / Privilege /
Required permissions on the auth principal / notes), including a `## Terraform` section if
the argument names or enums diverge.

**When checking what the API requires, read the request model, not the storage model.**
In midgard, `midgard/api/dynamic_<type>.py` defines what a create actually accepts and is
the contract; `midgard/inventory/<type>_access_creds.py` is the stored shape and routinely
declares a field required that the request model defaults. Elasticsearch `port` and
SendGrid `host` both look mandatory in the inventory model and are defaulted by the request
model. Reading the wrong one produces a reference file that demands fields the user does
not have to supply.

Then run `scripts/check-claims.py` from the repo root. It verifies the catalog, the
secret-optionality classification, the version floors and the documented provider gaps
against the provider and midgard sources, and will tell you if the new type contradicts
any of them. Add a row to the table above. If the type or one of
its engines has a version floor, add a row to [Compatibility](#compatibility) too. No other
files need to change.

# Workflow

1. **Pick the target** and read
   [`references/kubernetes.md`](references/kubernetes.md) or
   [`references/terraform.md`](references/terraform.md).
2. **Identify what's being created.** Credential alone? All three? If the user only
   mentions the credential, ask whether they also want the matching privilege and policy.
3. **Pick the type** and read `references/<type>.md`.
4. **Gather inputs** in the order above, grouped by resource.
5. **Assemble the output.**
   - *Kubernetes:* multi-document YAML with `---` separators, every document in
     `hush-security`, plus a companion `Secret` where needed.
   - *Terraform:* one `.tf` with the provider block, any `hush_deployment` /
     `hush_secret_store`, then credential, privilege and policy wired by resource
     references — plus `variable` blocks for the secrets.
6. **Surface the required auth-principal permissions.** After the output, print a clearly
   labeled **"Required permissions on the auth principal"** block listing what the GCP SA /
   IAM role / DB user / API token needs for Hush to provision and rotate credentials. Pull
   it from `references/<type>.md`. If that file lacks one or marks it not applicable, say
   so — don't invent permissions.
7. **Add a post-generation note** covering anything version-gated or risky:
   - Any [Compatibility](#compatibility) floor the output relies on, naming whether it
     fails at apply or later.
   - *Kubernetes:* if the manifest uses `remoteName`, the uniqueness requirement. Always:
     how to check the result (`kubectl -n hush-security get accesspolicy` and the status
     columns, see `references/kubernetes.md`), that deleting or renaming a CR deletes or
     recreates the object in Hush, and that a Secret edit alone is not picked up — the
     credential's `spec` has to change too.
   - *Terraform:* that a clean `terraform plan` does **not** mean the API will accept it —
     see the validation note below.

   Ask the user to confirm before applying.

# Validation gotchas

These are enforced by the Hush API on both targets:

- `attestationCriteria` needs at least one entry; `key` is required iff the type is
  `k8s:pod-label` and must be absent otherwise.
- A policy carries at most one privilege, and the privilege type must equal the credential
  type.
- Static credentials (`plaintext`, `kv`) cannot be referenced by a policy with a privilege.
- The types listed under "Types that don't take privileges" must have none.
- WIF delivery only works with the matching WIF credential type, forbids
  `k8s:container-name`, and `subject_kind: service_account` needs both `k8s:ns` and
  `k8s:sa`.
- Delivery name and path rules as listed under "Delivery modes".
- Template variables must name real fields on the credential.

Per-target gotchas — the Kubernetes ones (namespace, `keyMappings`, ref forms) are in
[`references/kubernetes.md`](references/kubernetes.md); the Terraform ones are in
[`references/terraform.md`](references/terraform.md).

> **Terraform in particular:** the provider has no cross-field validation on
> `hush_access_policy` — none of the rules above are checked client-side. A clean
> `terraform plan` proves nothing; they all surface as API errors at `apply`. Apply them
> yourself when authoring.

# Examples

Worked end-to-end examples live with their target:

- Kubernetes — postgres trio, gemini (no privilege), and a policy referencing an
  externally-managed credential: [`references/kubernetes.md`](references/kubernetes.md).
- Terraform — the postgres trio with deployment, write-only secret and templated delivery:
  [`references/terraform.md`](references/terraform.md).
