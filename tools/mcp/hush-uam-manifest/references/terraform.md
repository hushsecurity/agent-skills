# Terraform target

How Hush UAM resources are expressed in HCL, using the `hushsecurity/hush` Terraform
provider. Read this before emitting any `.tf` — then read the matching
`references/<type>.md` for the credential type's fields.

The **semantics** are identical to the Kubernetes target: same credential types, same
attestation criteria, same delivery modes, same privilege shapes, same required
permissions on the auth principal. Only the syntax and a few structural concepts differ,
and those are what this file covers.

## Provider configuration

```hcl
terraform {
  required_providers {
    hush = {
      source  = "hushsecurity/hush"
      version = "~> 1.24"
    }
  }
}

provider "hush" {
  api_key_id     = var.hush_api_key_id
  api_key_secret = var.hush_api_key_secret
  realm          = "US" # or "EU"
}

variable "hush_api_key_id" {
  type      = string
  sensitive = true
}

variable "hush_api_key_secret" {
  type      = string
  sensitive = true
}
```

- `api_key_id` and `api_key_secret` are required; `realm` is optional and defaults to
  `US`. All three fall back to `HUSH_API_KEY_ID`, `HUSH_API_KEY_SECRET` and `HUSH_REALM`,
  so the two `variable` blocks can be dropped in favour of the environment.
- **`realm` is case-sensitive** — only `US` and `EU` are accepted, uppercase. `us` fails
  at plan time.
- The repo's own examples pin no version. **Always emit a `version` constraint** — the
  provider adds resources and arguments regularly, and an unpinned `source` silently
  upgrades. Note what the operator means: `~> 1.24` is `>= 1.24.0, < 2.0.0`, so minor
  releases still arrive. Use `~> 1.24.0` to hold at 1.24 patch releases.
- **If the repo already declares `hush` in a `required_providers` block, do not emit a
  second one.** Terraform rejects two declarations of the same provider with
  `Duplicate required providers configuration`, even across files. Add the `version` to
  the existing block, or, if that file is out of scope, leave the block alone and
  recommend the pin in the post-generation note.
- Auth is OAuth2 client credentials; the base URL is derived from the realm.

**Terraform version:** the provider declares `>= 1.3`, but the write-only secret pattern
below needs **Terraform >= 1.11**. If the user is on an older Terraform, they must use the
plain sensitive attributes instead and accept secrets in state — say so explicitly rather
than emitting `_wo` arguments that will not parse.

## Resource shape

There is no `type` argument and no `config` block. **The credential type is the resource
type name**, and every CRD `spec.config.<field>` is a top-level argument of the same name:

| Kubernetes | Terraform |
| --- | --- |
| `kind: AccessCredential` + `spec.type: postgres` | `resource "hush_postgres_access_credential"` |
| `kind: AccessPrivilege` + `spec.type: postgres` | `resource "hush_postgres_access_privilege"` |
| `kind: AccessPolicy` | `resource "hush_access_policy"` |
| `spec.name` | `name` |
| `spec.description` | `description` |
| `spec.config.host` | `host` |

`type` and `kind` exist on credential resources as **read-only computed attributes** —
never set them.

Where a type's Terraform argument names differ from the CRD field names, the divergence is
recorded in that type's `references/<type>.md` under a `## Terraform` heading. If the file
has no such section, the names match one-for-one.

Every resource also has a matching **data source** of the same name for reading existing
objects, and supports `terraform import` by platform ID.

## Secrets — `_wo` and `_wo_version`

There is no `secretRef`, no companion `Secret`, and no `keyMappings`. Sensitive values are
arguments on the resource, in two forms:

- **`<field>`** (e.g. `password`, `api_key`, `secret`) — marked sensitive, but **stored in
  Terraform state**.
- **`<field>_wo`** — a Terraform *write-only* argument, never persisted to state.

`<field>` and `<field>_wo` always conflict — never set both. Whether one of them is
*required* varies, and the absence of `ExactlyOneOf` does **not** mean the secret is
optional. 16 of the 29 types mark the pair `ExactlyOneOf`; of the rest:

- **Omittable, but only as a whole pair** — `apigee`, `aws_access_key`, `azure_app`,
  `bedrock`, `gcp_sa`. Leaving the credential *entirely* without one is legitimate and
  often correct: a federated `gcp_sa` with no uploaded key, or an `aws_access_key`
  credential using the access manager's own IAM identity. But `aws_access_key`,
  `azure_app` and `bedrock` pair the secret with an ID field
  (`access_key_id_value`/`access_key_id`, `client_id`) and the API rejects one without the
  other, so **omit both or supply both** — never the ID alone. `apigee` and `gcp_sa` have
  a single secret and no pairing.
- **Required per engine, checked at plan** — `kafka` and `redis` enforce it in a
  `CustomizeDiff`: `kafka` needs `password` for `engine = "native"` and `token` for
  `"aiven"`; `redis` needs `password` for `engine = "redis"` and `token` for `"aiven"`.
  The other two redis engines take a *different* secret, both-or-neither:
  `elasticache` forbids `password` but pairs `access_key_id` with `secret_access_key`
  (omit both for AWS workload identity federation), and `azure_managed_redis` pairs
  `client_id` with `client_secret` (omit both to use the access manager's own Azure
  credentials).
- **Required as a pair** — `mongodb_atlas` demands exactly one of `client_id` +
  `client_secret` or `public_key` + `private_key`; supplying neither fails. Checked at
  plan on create only, so an update that drops the pair fails at apply instead.
- **Required by the API but unchecked by the provider** — `snowflake` needs `password`
  when `auth_method = "password"` and `private_key` when `"key-pair"`, and **forbids the
  other one**. Omitting both, or supplying both, plans cleanly and is rejected at apply.

- The remaining four types have no secret argument at all: `aws_wif`, `gcp_wif` and
  `azure_wif` are system-generated, and `kv` carries its values inline in `items` (with no
  write-only form — see `references/kv.md`).

Check `references/<type>.md` rather than guessing from the schema.

**`<field>_wo` and `<field>_wo_version` are `RequiredWith` each other — both or neither.**
Emitting `password_wo` without `password_wo_version` fails at plan time with
`"password_wo": all of 'password_wo,password_wo_version' must be specified`. This is the
single most common mistake; always emit the pair.

```hcl
resource "hush_postgres_access_credential" "app" {
  name           = "pg-prod"
  deployment_ids = [hush_deployment.prod.id]
  db_name        = "app"
  host           = "pg.internal"
  port           = 5432
  ssl_mode       = "require"
  username       = "app_user"

  password_wo         = var.pg_password
  password_wo_version = "1"
}

variable "pg_password" {
  type      = string
  sensitive = true
}
```

**Default to the `_wo` form.** To rotate the value, change the variable *and* increment
`_wo_version` — the version is what tells Terraform to re-send a value it cannot read
back. Leaving the version unchanged means the new secret is never sent.

Which fields are sensitive varies by type; `references/<type>.md` lists them.

## `deployment_ids` — required, exactly one

The CRD has no deployment concept: the operator infers it, and every CR lives in the fixed
`hush-security` namespace. **Terraform has no namespace at all**; the equivalent is an
explicit `deployment_ids` argument, required on `hush_access_policy` and on **every**
credential resource.

- Exactly one element (`MinItems: 1, MaxItems: 1`), each matching `^dep-`.
- A policy's deployment must be one its credential also has.
- **Effectively immutable on credentials** — a `CustomizeDiff` refuses the change outright
  (`delete and recreate the resource to change its deployment set`) rather than planning a
  replacement. The three WIF credential types are exempt.
- **Privileges have no `deployment_ids`** — they are deployment-agnostic and reusable.

Three ways to supply it, in order of preference:

```hcl
# 1. Manage the deployment in the same configuration
resource "hush_deployment" "prod" {
  name     = "prod-cluster"
  kind     = "k8s"
  env_type = "prod"
}
# ... deployment_ids = [hush_deployment.prod.id]

# 2. Look up a deployment created elsewhere, by name or id
data "hush_deployment" "prod" {
  name = "prod-cluster"
}
# ... deployment_ids = [data.hush_deployment.prod.id]

# 3. A literal id, when the user has one and wants no lookup
# ... deployment_ids = ["dep-01h8z9p7q2r5x3v6"]
```

Only `k8s` deployments can carry UAM policies — the API rejects a policy on any other
deployment kind, and refuses a mix of kinds.

`hush_deployment` exposes `password`, `token` and `image_pull_secret` as **sensitive
computed** attributes. Never write them into an `output` without `sensitive = true`.

## `hush_secret_store` — no Kubernetes counterpart

Where the access manager *materializes* the rotated secret. Orthogonal to delivery:
delivery says how a workload receives the value, the store says where Hush persists it.
Entirely absent from the CRD model.

```hcl
resource "hush_secret_store" "prod" {
  name           = "prod-aws-sm"
  deployment_ids = [hush_deployment.prod.id]

  aws_sm {
    prefix     = "hush"
    region     = "eu-west-1"
    kms_key_id = "arn:aws:kms:eu-west-1:123456789012:key/abcd1234-..." # optional
  }
}
```

Then wire it to a credential with `secret_store_id = hush_secret_store.prod.id`. The
argument is optional and exists on every credential resource.

- Exactly one backend block: `aws_sm`, `aws_ssm`, `gcp_sm` or `k8s_secrets`
  (`ExactlyOneOf`). All four are `ForceNew` — **any change to the block replaces the
  store.**
- `deployment_ids` here is **not** capped at one, unlike credentials and policies.
- Required per kind: `aws_sm`/`aws_ssm` take `prefix` + `region` (optional `kms_key_id`);
  `gcp_sm` takes `prefix` + `project_id`; `k8s_secrets` takes `prefix` (optional
  `namespace`, defaulting to the access-manager namespace).

> ⚠️ **Version-sensitive.** The per-kind prefix rules below are in the provider's
> `[Unreleased]` section — they are **not** in 1.24.x. On 1.24.x the validator is a single
> `^[a-z][a-z0-9]{0,9}$` for every kind, so a segmented prefix like `hush/prod` is refused
> at **plan** time. Use a plain `prefix = "hush"` unless you know the user is on a release
> that carries HUSH-7027.

Once released, `prefix` is validated at plan time per backend — lowercase, each segment
starts and ends alphanumeric, `-` allowed everywhere, `.` may not repeat. The 80-character
maximum is **not** checked by the provider; the API enforces it:

| block | separator | punctuation besides `-` | extra rules |
| --- | --- | --- | --- |
| `aws_sm` | `/` | `_ . + = @` | — |
| `aws_ssm` | `/` | `_ .` | may not start with `aws` or `ssm`; max 9 segments |
| `gcp_sm` | `-` | `_` | — |
| `k8s_secrets` | `-` | `.` | punctuation may not repeat |

**Version floors:** using a secret store at all needs access manager **>= 0.21.0**. A
prefix outside the old `^[a-z][a-z0-9]{0,9}$` rule needs access manager **>= 0.27.0** on
every attached deployment — and on a provider new enough to accept such a prefix at plan
time, that shortfall is refused at *apply* time after a clean plan.

## Referencing credentials and privileges

The CRD's three ref forms (`name`, `id`, `remoteName` + `type`) collapse to plain ID
strings:

```hcl
access_credential_id = hush_postgres_access_credential.app.id
access_privilege_ids = [hush_postgres_access_privilege.readonly.id]
```

`access_privilege_ids` is a list capped at one element — the same one-privilege-per-policy
rule, expressed as a list. Omit it entirely for the types that take no privilege.

**There is no `remoteName` equivalent.** Credential and privilege data sources look up by
`id` only — they have no `name` argument. To reference something created outside
Terraform you need its `acr-` / `apr-` ID, or you `terraform import` it into state first.
(`hush_deployment`, `hush_secret_store`, the integrations and `hush_notification_channel`
*do* support name lookup; credentials and privileges do not.)

## Delivery — six blocks, exactly one

`deliveryConfig: {type: X, config: {...}}` becomes six named blocks under `ExactlyOneOf`:
`env_delivery_config`, `volume_delivery_config`, `sdk_delivery_config`,
`aws_wif_delivery_config`, `gcp_wif_delivery_config`, `azure_wif_delivery_config`.
Exactly one must be present — the docs group them under "Optional", but a policy with none
is rejected.

**The three item-bearing blocks are not shaped alike.** This catches people out:

| Mode | Shape |
| --- | --- |
| `env` | **Repeat the whole block once per variable.** No wrapping list, no nested item block. |
| `volume` | One block, with `mount_point` and a nested **`item`** block (singular) repeated per file. |
| `sdk` | One block, with `secret_name` and a nested **`items`** block (plural) repeated per key. |

```hcl
# env — one block per variable
env_delivery_config {
  name = "PG_USER"
  key  = "username"
}

env_delivery_config {
  name = "PG_PASSWORD"
  key  = "password"
}
```

```hcl
# volume — nested `item`, singular
volume_delivery_config {
  mount_point = "/var/run/secrets/db"

  item {
    path = "username"
    key  = "username"
  }
}
```

```hcl
# sdk — nested `items`, plural
sdk_delivery_config {
  secret_name = "prod/db/credentials"

  items {
    name = "username"
    key  = "username"
  }
}
```

In all three, `type` is `key` (default) or `template`, and `key` holds either a credential
field name or a template string.

WIF blocks take their config directly:

```hcl
aws_wif_delivery_config {
  role_arn     = "arn:aws:iam::123456789012:role/my-role"
  subject_kind = "hush_subject" # default
  subject      = "my-workload-identity"
}
```

`gcp_wif_delivery_config` takes `subject_kind`, `subject`, `service_account` and
`service_account_token_lifetime` (default 3600); `azure_wif_delivery_config` requires
`tenant_id` and `client_id` alongside `subject_kind` / `subject`.

## Templates must escape `$` as `$$`

HCL uses `${...}` for its own interpolation, so every Hush template placeholder is written
`$${...}`. Server-side semantics are unchanged — still Python `string.Template`.

```hcl
env_delivery_config {
  name = "DATABASE_URL"
  type = "template"
  key  = "postgresql://$${username}:$${password}@$${host}:$${port}/$${db_name}"
}
```

The connection-string table in `SKILL.md` is written in CRD form; double every `$` when
emitting HCL. A single `$` makes Terraform try to resolve the name as a Terraform
variable, which fails at plan time — or worse, silently resolves to something wrong.

## `enabled` behaves differently here

On the Kubernetes side, **omitting** `spec.enabled` opts that field out of drift
correction, which is why the skill defaults to omitting it.

**That advice does not carry over.** In Terraform `enabled` is a plain optional boolean
defaulting to `true`, and Terraform always reconciles it. There is no way to declare a
policy while leaving enable/disable to the console — flipping it there produces drift that
the next `terraform apply` reverts. Do not tell the user otherwise.

## The provider validates far less than the CRD

`hush_access_policy` has **no `CustomizeDiff` and no cross-field validators**. These rules
are real and enforced — but only by the API, at `terraform apply`, after a clean plan:

- WIF delivery must match the credential type (`aws_wif` ↔ `aws_wif`), and WIF credentials
  cannot use `env`/`volume`/`sdk`.
- `k8s:container-name` is forbidden in any policy with WIF delivery.
- `subject_kind = "service_account"` requires **both** a `k8s:ns` and a `k8s:sa` criterion.
- `key` is required for `k8s:pod-label` and **must be absent** for the other four criterion
  types. Terraform accepts `key` on any of them.
- Env var names must match `^[a-zA-Z_][a-zA-Z0-9_]*$`; `_HUSH` / `__HUSH` prefixes are
  reserved.
- Volume `mount_point` must be absolute, `path` relative; neither may contain `..` or
  `hush.security`.
- Static credentials (`plaintext`, `kv`) reject privileges; types that require a privilege
  reject a policy without one; the privilege type must equal the credential type.
- Template variables must name real fields on the credential.

**Apply every one of these when authoring.** A clean `terraform plan` means nothing here.

What the provider *does* check client-side: the attestation `type` enum, `subject_kind`
enum, delivery `type` enum, the sdk name regex and length, `^dep-` on deployment IDs,
name/description lengths, the delivery-block `ExactlyOneOf`, and the secret-store prefix
rules.

## Provider gaps to warn the user about

Things the API supports that Terraform cannot express. When a user asks for one, say so
rather than emitting HCL that will not work:

- **No `hush_mariadb_access_privilege`.** MariaDB credentials work; the privilege type
  exists in the API but has no Terraform resource. A MariaDB policy needing a privilege
  has to create it outside Terraform and reference the `apr-` ID.
- **`hush_postgres_access_privilege.object_type` accepts only 5 of the API's 16 values** —
  `TABLE`, `SEQUENCE`, `FUNCTION`, `SCHEMA`, `DATABASE`. `VIEW`, `PROCEDURE`, `ROUTINE`,
  `LARGE OBJECT`, `TABLESPACE`, `DOMAIN`, `TYPE`, `LANGUAGE`, `FOREIGN DATA WRAPPER`,
  `FOREIGN SERVER` and `PARAMETER` are unreachable, though `references/postgres.md`
  documents them for the CRD target.
- **`hush_azure_app_access_privilege` cannot set `graph_api_permissions`** — the block
  exposes `display_name` and `roles` only.
- **No user-claims support.** `user_claims` and `user_claims_authority_id` on the policy
  API have no provider equivalent.
- **Elasticsearch API-key auth is unreachable.** The API supports either basic auth or an
  API key; the provider has no `api_key` argument and marks `username` required. Only
  username + password works from Terraform.
- **`hush_gemini_access_credential` cannot set `service_account_bound`.** Terraform-managed
  Gemini credentials are always unbound. The `references/gemini.md` decision about binding
  generated API keys to a Hush-managed service account has no Terraform expression.
- **`hush_sendgrid_access_credential` cannot select the EU host.** The API's `host` is
  absent from the provider and defaults to `https://api.sendgrid.com`, so EU SendGrid is
  unreachable.

Two enum mismatches where the provider and API disagree outright — emitting the value the
provider accepts produces an apply-time failure:

- **`hush_mysql_access_credential.ssl_mode`** — the provider accepts `verify_ca` /
  `verify_identity` (underscores) but the API expects `verify-ca` / `verify-identity`
  (hyphens). Both spellings fail, one at plan and one at apply, so **MySQL certificate
  verification cannot be configured from Terraform at all.** Use `disabled`, `preferred`
  or `required` and tell the user the verify modes are blocked. (`mariadb` is unaffected —
  its enum is correct.)
- **`hush_rabbitmq_access_privilege.tags`** — the provider also accepts `none`, which the
  API rejects. Never emit it; the five valid tags are `administrator`, `monitoring`,
  `policymaker`, `management`, `impersonator`.

## Worked example — a WIF pair

Federation types have no config fields, no secret and no privilege. The whole credential is
a name and a deployment, and the policy's delivery block carries the cloud-side detail.

```hcl
resource "hush_aws_wif_access_credential" "uploader" {
  name           = "aws-wif-media"
  deployment_ids = [hush_deployment.prod.id]
}

resource "hush_access_policy" "uploader" {
  name                 = "uploader-wif-policy"
  access_credential_id = hush_aws_wif_access_credential.uploader.id
  deployment_ids       = [hush_deployment.prod.id]
  # no access_privilege_ids — federation types take none

  # subject_kind = "service_account" needs both k8s:ns and k8s:sa;
  # k8s:container-name is forbidden with any WIF delivery.
  attestation_criteria {
    type  = "k8s:ns"
    value = "media"
  }

  attestation_criteria {
    type  = "k8s:sa"
    value = "uploader"
  }

  aws_wif_delivery_config {
    role_arn     = "arn:aws:iam::123456789012:role/uploader"
    subject_kind = "service_account"
  }
}
```

What the role may *do* is not a Hush privilege. It is the IAM permissions policy on the
role itself, managed with the `aws` provider or outside Terraform.

## Worked example — the postgres trio

```hcl
resource "hush_deployment" "prod" {
  name     = "prod-cluster"
  kind     = "k8s"
  env_type = "prod"
}

resource "hush_postgres_access_credential" "app" {
  name           = "pg-prod"
  description    = "Production application database"
  deployment_ids = [hush_deployment.prod.id]

  db_name  = "app"
  host     = "pg.internal"
  port     = 5432
  ssl_mode = "require"
  username = "app_user"

  password_wo         = var.pg_root_password
  password_wo_version = "1"
}

resource "hush_postgres_access_privilege" "readonly" {
  name        = "pg-readonly"
  description = "Read-only on the public schema"

  grants {
    privileges    = ["SELECT"]
    object_type   = "TABLE"
    object_names  = ["public"]
    all_in_schema = true
  }
}

resource "hush_access_policy" "app" {
  name                 = "pg-app-policy"
  access_credential_id = hush_postgres_access_credential.app.id
  access_privilege_ids = [hush_postgres_access_privilege.readonly.id]
  deployment_ids       = [hush_deployment.prod.id]

  attestation_criteria {
    type  = "k8s:ns"
    value = "app-namespace"
  }

  attestation_criteria {
    type  = "k8s:sa"
    value = "app-sa"
  }

  env_delivery_config {
    name = "DATABASE_URL"
    type = "template"
    key  = "postgresql://$${username}:$${password}@$${host}:$${port}/$${db_name}"
  }
}

variable "pg_root_password" {
  type      = string
  sensitive = true
}
```

Note `object_names` on the grant: the provider marks it optional, but the API **requires**
at least one identifier, so a grant without it plans cleanly and fails at apply. Always
emit it.
