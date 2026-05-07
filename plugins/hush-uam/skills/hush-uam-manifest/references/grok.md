# grok

xAI Grok credentials and privileges. Dynamic credentials — provisions ephemeral team API keys.

## Credential

```yaml
config:
  team_id: <grok-team-id>
secretRef:
  name: <k8s-secret>
  # canonical key: api_key
```

`secretRef` keys: `api_key`.

## Privilege

```yaml
config:
  endpoints: [Chat, Embed]              # optional; omit to grant all endpoints
  models: [grok-beta]                   # optional; omit to grant all models
```

Valid `endpoints`: `Chat`, `Batch`, `Embed`, `Files`, `Image`, `Models`, `Sample`, `Video`, `Voice`, `Tokenize`, `Documents`.

Both lists must contain unique values when set.

## Required permissions on the auth principal

The configured API key must have:
- `ListApiKeys` — list existing API keys in the team
- `CreateApiKey` — create new short-lived API keys
- `DeleteApiKey` — revoke expired API keys
