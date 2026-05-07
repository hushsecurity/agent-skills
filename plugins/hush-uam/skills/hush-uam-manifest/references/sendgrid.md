# sendgrid

SendGrid credentials and privileges. Dynamic credentials — provisions ephemeral scoped API keys.

## Credential

```yaml
config:
  host: https://api.sendgrid.com   # default
secretRef:
  name: <k8s-secret>
  # canonical key: api_key
```

`secretRef` keys: `api_key`.

## Privilege

```yaml
config:
  scopes: [mail.send]                   # min 1
```

**You MUST read `references/sendgrid-scopes.md` before generating a SendGrid privilege** — it contains the complete list of valid scope names organized by SendGrid product area.

## Required permissions on the auth principal

The configured API key must have the following scopes:
- `api_keys.create`
- `api_keys.read`
- `api_keys.delete`
