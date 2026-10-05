# Kubernetes target

How Hush UAM resources are expressed as CRD manifests for the hush-uam operator. Read this
before emitting any YAML — then read the matching `references/<type>.md` for the credential
type's fields.

The CRDs live under the API group `am.hush.security/v1alpha1` and cover three kinds:
`AccessCredential`, `AccessPrivilege`, `AccessPolicy`. The operator forwards `spec.config`
straight to the Hush API, so the keys inside `config` must match what the API expects for
the chosen `type`.

## ⚠️ CRITICAL: the CRs live in the hush-am namespace

The api-controller watches **only the namespace the `hush-am` chart is installed in**. It
reads that namespace from its own pod, and its RBAC is a namespaced Role, so it cannot see
CRs or Secrets anywhere else. Resources placed in another namespace are simply ignored — no
error, no status, nothing syncs.

In a standard installation that namespace is **`hush-security`**, and every manifest you
generate MUST use `metadata.namespace: hush-security`. This applies to:

- `AccessCredential`, `AccessPrivilege`, `AccessPolicy` CRs
- Any companion `Secret` you generate alongside — the operator reads it from the CR's own
  namespace and nowhere else

**Do not** ask the user which namespace to use, and never put the CRs in the workload's
namespace. If the user asks for a different namespace, push back and explain the above.
The one legitimate exception is evidence in the repo that hush-am itself is installed
elsewhere — a `HelmRelease`, an Argo `Application`, or a values file for the `hush-am`
chart naming another namespace. Then use that namespace, and say why.

**Note:** this constraint is about *where the CRs live*. It is NOT the same as the
workload's namespace, which appears in `attestationCriteria` entries of type `k8s:ns` and
refers to where the *workload consuming the credential* runs. Those two namespaces are
independent — the workload almost always lives in a different namespace than
`hush-security`.

There is no deployment field in any CRD: the operator runs inside one deployment scope and
the platform infers it from the operator's identity. (The Terraform target has no namespace
at all and an explicit `deployment_ids` argument instead.)

## CRD shape

### AccessCredential

```yaml
apiVersion: am.hush.security/v1alpha1
kind: AccessCredential
metadata:
  name: <metadata-name>             # decoupled from spec.name
  namespace: hush-security          # the hush-am install namespace; hush-security in a standard install
spec:
  name: <display-name>              # what the API sees
  type: <type>                      # see the Type catalog in SKILL.md
  description: <optional>
  config:                           # non-sensitive fields; OMIT entirely for `plaintext`
    <field>: <value>
  secretRef:                        # only if the type has sensitive fields
    name: <k8s-secret-name>
    keyMappings:                    # see "How keyMappings behaves" below
      <expected-field>: <secret-key>
```

### AccessPrivilege

```yaml
apiVersion: am.hush.security/v1alpha1
kind: AccessPrivilege
metadata:
  name: <metadata-name>
  namespace: hush-security          # the hush-am install namespace; hush-security in a standard install
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
  namespace: hush-security          # the hush-am install namespace, NOT the workload's
spec:
  name: <display-name>
  description: <optional>
  # enabled: true                 # OPTIONAL — see "How enabled interacts with drift correction"
  accessCredentialRef:            # exactly one of `name`, `id`, or `remoteName`+`type`
    name: <cred-cr-name>
  accessPrivilegeRefs:            # OMIT for types that don't take privileges
    - name: <priv-cr-name>        # exactly one of `name`, `id`, or `remoteName`+`type` per entry
  attestationCriteria:            # min 1
    - type: k8s:ns                # k8s:ns, k8s:sa, k8s:pod-label, k8s:pod-name, k8s:container-name
      value: <workload-namespace> # the *workload's* namespace — NOT hush-security
    - type: k8s:pod-label
      key: <label-key>            # required only for k8s:pod-label
      value: <label-value>
  deliveryConfig:
    type: env                     # env, volume, sdk, aws_wif, gcp_wif, azure_wif
    config:
      <delivery-type-specific>
```

## How `keyMappings` behaves

`keyMappings` is **not just a rename map — it's also a filter.** The two modes:

- **Without `keyMappings`:** the operator forwards **every key** in the Secret to the Hush
  API as-is. If the Secret has any keys the API doesn't recognize for that credential type
  (e.g. `username`, `created_at`, `rotation_id`, audit metadata, an unrelated key the team
  stored there), the create/update call **will fail**. This works only when the Secret was
  specifically created with exactly the canonical key names and nothing else.

- **With `keyMappings`:** only the keys mentioned in the mapping are forwarded. Everything
  else in the Secret is ignored. Each entry is `<expected-field>: <secret-key>` — the left
  side is what the Hush API expects, the right side is the actual key in the K8s Secret.
  Even an *identity* mapping (e.g. `password: password`) is valid and useful — it
  explicitly opts in to that one key and filters out the rest.

Three details the operator enforces on top of that:

- **A mapped key missing from the Secret fails the sync** (`secret "x" missing key "y"`),
  so every entry must name a key that actually exists.
- **`plaintext` is special.** Without `keyMappings` the Secret must hold exactly **one**
  entry; its key name is irrelevant and the value becomes the credential's `secret`. Two
  or more entries are rejected as ambiguous — add `keyMappings: {secret: <key>}` to pick
  one.
- **`kv` maps to item names.** Each entry `<item-key>: <secret-key>` becomes one
  credential item called `<item-key>`; without `keyMappings` every Secret key becomes an
  item under its own name.

### Recommended pattern

- **Generating the Secret alongside the manifest** → use canonical key names (`password`,
  `api_key`, etc.), skip `keyMappings`. You control the Secret, so there are no extra keys.
- **Referring to an existing Secret** → learn the actual key names — read the Secret's
  manifest if it is in the repo, ask otherwise — and **always emit `keyMappings`**, even if
  every entry is identity. This avoids silent failures when the Secret has extra keys, and
  makes the manifest self-documenting.

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

## How `enabled` interacts with drift correction

The Hush operator reconciles the policy on the platform back to whatever the manifest
declares — if someone changes a managed field via the Hush API, UI, or Terraform, the
operator restores it. **`enabled` is the one field this can be opted out of**, because
flipping a policy on/off is often an operational action (e.g. on-call temporarily disabling
a misbehaving policy) that shouldn't fight the controller.

The rule is based on whether `spec.enabled` is present in the manifest:

- **`enabled` omitted** (default, recommended) — the operator does not reconcile this
  field. Anyone can flip the policy on/off via the Hush API/UI/Terraform without the
  operator restoring it. Use this when the manifest is the source of truth for *what* the
  policy is, but enable/disable is controlled elsewhere.
- **`enabled: true` or `enabled: false`** — the operator reconciles this field too. If it
  drifts (someone disables a policy declared `enabled: true`), the operator flips it back.
  Use this when you want declarative control over enable/disable as well, e.g. when the
  policy is defined alongside an app deployment that should always start enabled.

All other policy fields (`accessCredentialRef`, `accessPrivilegeRefs`,
`attestationCriteria`, `deliveryConfig`, etc.) are always reconciled — drift on those
fields is always restored to the manifest value.

**Default to omitting `enabled`.** Only include it when the user explicitly says they want
declarative on/off control.

**This is Kubernetes-only.** In Terraform `enabled` is a plain boolean defaulting to `true`
and is always reconciled; there is no opt-out. Do not carry this advice across targets.

## Referencing credentials and privileges

`accessCredentialRef` and each entry of `accessPrivilegeRefs` accept **exactly one** of
three forms — not zero, not more than one:

1. **`name`** — when the credential or privilege is also being managed in Kubernetes as a
   CR in the same namespace. The operator resolves it to its underlying ID.
2. **`id`** — when the credential or privilege was created outside Kubernetes (e.g. via the
   Hush API or UI) and exists only on the platform side, not as a CR. Use this when the
   user has the platform ID handy.
3. **`remoteName` + `type`** — when the credential or privilege was created outside
   Kubernetes and the user only knows it by its display name on the platform. The
   api-controller resolves the `remoteName`/`type` pair to an ID via Hush UAM within the
   deployment's scope. `type` is required here to disambiguate. **Requires:** hush-uam ≥
   v0.11.0, helm chart `hush-am` ≥ 0.16.0 — older clusters' CRDs reject this field.

You can mix the three forms freely within a single policy — e.g. reference the credential
by `name` (CR in this namespace) and the privilege by `remoteName` + `type`.

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
  id: acr-abc123
accessPrivilegeRefs:
  - id: apr-xyz789
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

When the user is unclear, default to `name` if you're also generating the matching
credential/privilege CR; otherwise ask whether they have the platform `id` or only the
display name (`remoteName`).

If the cluster is below the `remoteName` floor and the user has no `id` either, do not
emit `remoteName`. Emit `id` with a clearly marked placeholder, tell the user where to find
the real value (the Hush UI or API, or `kubectl get accesscredential` if it is also a CR),
and mention that upgrading past the floor would let them use the display name instead.

### `remoteName` ambiguity → error status

`remoteName` + `type` is resolved by Hush UAM at reconcile time. If **more than one**
credential (or privilege) with that exact display name *and* that exact type exists in the
deployment's scope, the resolution is ambiguous and the policy's status will turn to
**error** — the operator won't pick one arbitrarily. When you generate a manifest that uses
`remoteName`, surface this risk to the user in a short post-manifest note so they can
confirm the name is unique before applying.

(Terraform has no `remoteName` equivalent: credential and privilege data sources look up by
`id` only.)

## deliveryConfig variants

```yaml
# env — inject as environment variables
deliveryConfig:
  type: env
  config:
    items:                         # min 1
      - name: POSTGRES_USERNAME    # env var name; must match ^[a-zA-Z_][a-zA-Z0-9_]*$
        key: username              # credential field name
        type: key                  # or "template" — see "Templated values" in SKILL.md
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

## Templated delivery — worked examples

The template rules live in `SKILL.md`; these are the two shapes in CRD form.

```yaml
# env delivery: a single DATABASE_URL built from credential fields
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

You can mix `key` and `template` items in the same `items[]` list — e.g. expose username
and password as separate env vars *and* a combined `DATABASE_URL`.

## What the operator does after apply

- **Apply order does not matter.** A policy whose `name` refs point at a credential or
  privilege CR that exists but has not synced yet goes to `Pending` (`waiting for
  dependency`); one whose ref names a CR that does not exist yet shows `Error`
  (`resolving references: ... not found`). Both retry every few seconds until the
  dependency is `Ready`. Apply the whole trio in one `kubectl apply -f` and let it settle.
- **Editing the Secret alone does not re-sync the credential.** The operator does watch
  the referenced Secret, but the reconcile it queues is dropped when the CR's generation
  and the object's `modified_at` in Hush are both unchanged — and a Secret edit changes
  neither. To push a rotated root secret, change the Secret **and** make a `spec` change on
  the credential CR in the same commit (bumping `spec.description` is enough; annotations
  do not count, the controller filters on generation). When the Secret is not in the repo
  (an external secrets operator, a sealed secret, a manual `kubectl create`), say so: the
  Secret changes wherever it is managed, and the CR still needs its `spec` nudge.
- **Deleting a CR deletes the Hush object.** Each CR carries a finalizer; on delete the
  operator removes the credential, privilege or policy from Hush UAM. Pruning a manifest
  in GitOps is a real deletion. A credential or privilege still referenced by a policy
  cannot go yet — its CR sits in `Deleting` (`credential still referenced by a policy, will
  retry`, or the privilege equivalent) until the policy is gone too.
- **Names are identities.** The operator records the CR's `metadata.name` on the Hush
  object. Re-creating a CR with the same name and type adopts the existing object rather
  than creating a duplicate; renaming a CR creates a new object and deletes the old one —
  for a dynamic credential, new provisioned users and revocation of the old ones. Warn
  before renaming. Adoption is scoped to the deployment the operator runs in.
- **`spec.config` must not set `foreign_id`.** The controller owns that field and refuses
  a manifest that names it.

## Verifying after apply

```
kubectl -n hush-security get accesscredential,accessprivilege,accesspolicy
```

The `STATUS` column is the operator's sync state, one of `Syncing`, `Pending` (waiting on
a `name` ref), `Ready`, `Error`, `Deleting`. `UAM STATUS`, `STATUS CODE` and `STATUS
DETAIL` are what Hush UAM reports about the object itself once it exists — a credential
can be `Ready` on the operator side and still failing to provision on the Hush side, and
that is where it shows. Those three columns are filled only when the installed CRDs carry
the status fields (chart `hush-am` >= 0.15.0); on older CRDs they stay blank. `kubectl
describe` lists the same as Events (`SyncError`, `Pending`, `Adopted`, and `SyncConflict`,
whose text names the usual cause: a second object of this deployment already holding this
manifest name), and `status.message` carries the API's error text for an `Error`. A
version floor rejected at reconcile time lands here too. Tell the user to check this after
applying.

## Kubernetes-only validation gotchas

These are on top of the shared rules in SKILL.md:

- `accessCredentialRef` and each entry of `accessPrivilegeRefs` accept exactly one of
  `name`, `id`, or `remoteName`+`type` (never two, never none). `remoteName` must be paired
  with `type`.
- `remoteName` is only accepted by **hush-uam ≥ v0.11.0** / chart `hush-am` ≥ 0.16.0; older
  CRDs reject the field at **apply** time.
- **Secret with extra keys + no `keyMappings` → API failure.** Emit `keyMappings` (identity
  is fine) whenever you reference a Secret you didn't generate.
- **Wrong namespace → silent sync failure.** All CRs and companion Secrets MUST live in
  the namespace hush-am is installed in, `hush-security` in a standard installation.
  Resources placed elsewhere are simply ignored — no error, just nothing happens.
- **`plaintext` with a multi-entry Secret and no `keyMappings` → sync error.** Pick the
  entry with `keyMappings: {secret: <key>}`.
- **`spec.config.foreign_id` → refused.** The controller sets it itself.

## Example: Postgres trio

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

### Variant: referencing an existing Secret

When `pg-creds` already exists and may contain other keys (e.g. `username`, `created_at`,
rotation metadata), drop the inline `Secret` document above and use `keyMappings` on the
credential to filter and map explicitly:

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

## Example: Gemini (no privilege)

GCP auth via identity federation, generated API keys unbound — the simplest combination. No
`secretRef`.

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

### Variant: Gemini with uploaded SA key + bound API keys

GCP auth via uploaded service account key, generated API keys bound to a Hush-managed
service account. Both decisions opted in. (`service_account_bound` has no Terraform
equivalent — it is reachable only from Kubernetes or the API.)

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

## Example: Policy referencing an externally-managed credential

When the credential and privilege already exist on the Hush platform (created via API or
UI), the policy refers to them by `id` — no companion CRs needed.

```yaml
apiVersion: am.hush.security/v1alpha1
kind: AccessPolicy
metadata:
  name: external-pg-policy
  namespace: hush-security
spec:
  name: external-pg-policy
  enabled: true                    # included here to demonstrate K8s-managed enable/disable;
                                   # the operator will restore drift on this field
  accessCredentialRef:
    id: acr-01h8z9p7q2r5x3v6t4y2k1m9w8
  accessPrivilegeRefs:
    - id: apr-01h8z9p7q2r5x3v6t4y2k1m9w9
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
