# datadog

Datadog credentials and privileges. Dynamic credentials — provisions ephemeral API/Application keys.

## Credential

```yaml
config:
  site: datadoghq.com           # default
secretRef:
  name: <k8s-secret>
  # canonical keys: api_key, app_key
```

`secretRef` keys: `api_key`, `app_key`.

## Privilege

```yaml
config:
  key_type: application_key             # one of: api_key, application_key, both
  scopes: [dashboards_read]             # only allowed when key_type != api_key
```

**You MUST read `references/datadog-scopes.md` before generating a Datadog privilege with scopes** — it contains the complete list of valid scope names organized by Datadog product area.

## Required permissions on the auth principal

The Application Key configured above must belong to a user with at least these scopes:
- `api_keys_read`
- `api_keys_write`
- `api_keys_delete`
- `user_app_keys_read`
- `user_app_keys_write`
