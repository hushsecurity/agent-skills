# openai

OpenAI credentials and privileges. Dynamic credentials — provisions ephemeral project API keys.

## Credential

```yaml
config:
  project_id: <openai-project-id>
secretRef:
  name: <k8s-secret>
  # canonical key: api_key
```

`secretRef` keys: `api_key`.

## Privilege

```yaml
config:
  permission_type: Restricted           # one of: Owner, Viewer, Member, Restricted
  permissions:                          # required iff permission_type=Restricted; forbidden otherwise
    - name: Chat completions
      level: request                    # one of: read, write, request — must match name's allowed levels
```

Valid `permissions[].name`: `Models`, `Model capabilities`, `Responses`, `Text-to-speech`, `Realtime`, `Chat completions`, `Embeddings`, `Images`, `Moderations`, `Assistants`, `Threads`, `Evals`, `Fine-tuning`, `Files`, `VideoGen API`, `Vector Stores`, `Prompts`, `Agent Builder`, `Webhooks`, `Usage Dashboard and Export`, `Project API Keys`, `Project Administration`, `Project API Keys Management`, `Datasets`.

Valid `level` depends on `name`:
- `read` only: `Models`, `Usage Dashboard and Export`
- `write` only: `Responses`, `Prompts`, `Project API Keys`, `Project Administration`, `Project API Keys Management`
- `request` only: `Model capabilities`, `Text-to-speech`, `Realtime`, `Chat completions`, `Embeddings`, `Images`, `Moderations`
- `read` or `write`: `Assistants`, `Threads`, `Evals`, `Fine-tuning`, `Files`, `VideoGen API`, `Vector Stores`, `Agent Builder`, `Webhooks`, `Datasets`

## Required permissions on the auth principal

The API key must be an **Admin Key** with full permissions to manage project-scoped service accounts and API keys. Create it from your OpenAI organization settings with **all permissions** selected.
