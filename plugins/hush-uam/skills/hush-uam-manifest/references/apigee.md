# apigee

Google Apigee credentials and privileges. Dynamic credentials — provisions ephemeral developer apps and consumer keys.

## Credential

```yaml
config: {}                       # no config fields required
secretRef:                       # OPTIONAL — see auth choice below
  name: <k8s-secret>
  # canonical key: service_account_key
```

`secretRef` keys: `service_account_key` (optional, GCP SA JSON).

### GCP authentication choice

Same pattern as `gemini` and `gcp_sa`:

- **Workload identity federation** — when the workload runs on GCP, the Hush agent authenticates using federated identity tokens. **Omit `secretRef` entirely**.
- **Uploaded service account key** — provide the GCP SA JSON via `secretRef`. Use when the workload doesn't run on GCP or the user prefers to upload a key explicitly.

## Privilege

```yaml
config:
  developer_email: dev@example.com
  project_id: my-gcp-project
  api_products: [my-product]            # min 1
  # exactly one of:
  app_name: my-app
  # OR
  app_config:
    display_name: my-app
```

## Required permissions on the auth principal

Both authentication methods (federated SA and uploaded SA key) require the GCP service account to have these IAM permissions in the target project:
- `apigee.developerapps.create`
- `apigee.developerapps.delete`
- `apigee.developerapps.get`
- `apigee.developerapps.list`
- `apigee.appkeys.manage`
- `apigee.appkeys.create`
- `apigee.appkeys.delete`

The predefined role `roles/apigee.developerAdmin` includes all of the above.
