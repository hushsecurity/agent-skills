# gemini

Google Gemini credentials. **No privilege type** — policies for `gemini` must omit `accessPrivilegeRefs`.

## Credential

```yaml
config:
  project_id: <gcp-project-id>
  service_account_bound: false   # default
secretRef:                       # OPTIONAL — see auth choice below
  name: <k8s-secret>
  # canonical key: service_account_key
```

`secretRef` keys: `service_account_key` (optional, GCP SA JSON).

### Two independent decisions

Ask the user about **both**. Don't conflate them; either one can be on or off regardless of the other.

#### 1. How does the Hush agent authenticate to GCP to provision API keys?

- **Workload identity federation** — when the workload runs on GCP and consumes a GCP service (Gemini in this case), the Hush agent authenticates using GCP-issued federated identity tokens. No service account key file is needed. **Omit `secretRef` entirely** in the manifest. This is the cleaner option when the workload itself is running on GCP.
- **Uploaded service account key** — the user provides a GCP service account JSON. Use `secretRef` with a Secret holding the JSON under key `service_account_key`. Use this when the workload doesn't run on GCP (so federated tokens aren't available), or when the user prefers to provide a key explicitly.

#### 2. Should the ephemeral API keys Hush generates be bound to a GCP Service Account?

- `service_account_bound: false` (default) — generated API keys are unbound. Simpler, no extra GCP SA created.
- `service_account_bound: true` — Hush also creates a GCP service account and binds the generated API keys to it. Useful when you need the API key tied to a workload identity for IAM/audit purposes.

Decision matrix: any combination is valid (federation + unbound, federation + bound, uploaded key + unbound, uploaded key + bound).

## Privilege

**No privilege type for `gemini`.** Policies referencing a Gemini credential must omit `accessPrivilegeRefs`.

## Required permissions on the auth principal

The service account (provided via `secretRef` or via federated identity) must have these IAM permissions on the GCP project that hosts the API keys. The SA itself may live in a different project, provided it has the permissions on the target project.
- `apikeys.keys.create`
- `apikeys.keys.delete`
- `apikeys.keys.get`
- `apikeys.keys.getKeyString`
- `apikeys.keys.list`

### Required GCP APIs to enable on the project

- `generativelanguage.googleapis.com` (Gemini API / Generative Language API) — lets Hush create API keys that can call Gemini.
- `apikeys.googleapis.com` (API Keys API) — lets Hush create and manage the API keys.

### Additional requirements when `service_account_bound: true`

- The org policy `constraints/iam.managed.disableServiceAccountApiKeyCreation` must be set to **Off**. Modifying this policy requires the project to be associated with an organization resource — projects without an organization are not supported. ([GCP docs](https://docs.cloud.google.com/docs/authentication/api-keys))
- The **Identity and Access Management (IAM) API** (`iam.googleapis.com`) must be enabled.
- The auth-principal SA needs additional permissions — either the predefined role `roles/iam.serviceAccountAdmin` **or** these individual permissions:
  - `iam.serviceAccounts.create`
  - `iam.serviceAccounts.delete`
  - `iam.serviceAccounts.get`
  - `iam.serviceAccountApiKeyBindings.create`
