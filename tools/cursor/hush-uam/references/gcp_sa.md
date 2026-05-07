# gcp_sa

GCP Service Account credentials and privileges. Dynamic credentials — provisions ephemeral SA keys.

## Credential

```yaml
config: {}                       # no config fields required
secretRef:                       # OPTIONAL — see auth choice below
  name: <k8s-secret>
  # canonical key: service_account_key
```

`secretRef` keys: `service_account_key` (optional, GCP SA JSON).

### GCP authentication choice

Same pattern as `gemini` and `apigee`:

- **Workload identity federation** — when the workload runs on GCP, the Hush agent authenticates using federated identity tokens. **Omit `secretRef` entirely**.
- **Uploaded service account key** — provide the GCP SA JSON via `secretRef`. Use when the workload doesn't run on GCP or the user prefers to upload a key explicitly.

## Privilege

```yaml
config:
  project_id: <gcp-project-id>
  # exactly one of:
  sa_email: my-sa@my-project.iam.gserviceaccount.com
  # OR
  sa_conf:
    display_name: my-sa
    roles:                              # min 1; GCP role names
      - roles/storage.objectViewer
```

`roles[]` must match `^(roles/<name>|(projects|organizations)/<id>/roles/<name>)$`.

## Required permissions on the auth principal

The Hush agent's service account must hold these IAM roles on the target GCP project to manage service account keys:
- `roles/iam.serviceAccountAdmin` — create and manage service accounts
- `roles/iam.serviceAccountKeyAdmin` — create and manage service account keys
- `roles/resourcemanager.projectIamAdmin` — manage IAM policies on the project
