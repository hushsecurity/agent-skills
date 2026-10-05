# temporal_cloud

Temporal Cloud credentials and privileges. Dynamic credentials — provisions ephemeral API keys via the Temporal Cloud API.

## Credential

```yaml
# omit `config` entirely — all credential input is the admin API key in secretRef
secretRef:
  name: <k8s-secret>
  # canonical key: api_key
```

`secretRef` keys: `api_key`.

The `api_key` is an **admin** Temporal Cloud API key that Hush uses to provision and rotate ephemeral per-workload API keys; it is not the key delivered to the workload.

## Privilege

```yaml
config:
  grants:                              # min 1; namespaces must be unique
    - namespace: <temporal-namespace>  # e.g. prod.acme, staging.acme
      permission: read                 # one of: read, write, admin
```

Valid `permission` values: `read`, `write`, `admin`.

Each entry grants the listed permission on a single Temporal Cloud namespace. Listing the same namespace twice is rejected.

## Required permissions on the auth principal

The admin API key supplied via `secretRef.api_key` must belong to a Temporal Cloud account role with permission to manage API keys and namespace permissions for the target namespaces — typically the **Global Admin** account role, or a custom role with API-key-management and namespace-permission-management capabilities.
