# twilio

Twilio credentials and privileges. Dynamic credentials — provisions ephemeral API keys.

## Credential

```yaml
config:
  account_sid: <twilio-account-sid>
  api_key_sid: <root-api-key-sid>
secretRef:
  name: <k8s-secret>
  # canonical key: api_key_secret
```

`secretRef` keys: `api_key_secret`.

## Privilege

```yaml
config:
  permission_type: Restricted           # one of: Standard, Restricted
  permissions:                          # required when permission_type=Restricted
    - /twilio/messaging/messages/list
    - /twilio/messaging/messages/create
```

When `permission_type: Standard`, omit `permissions` (full access).

**For `permission_type: Restricted`, you MUST read `references/twilio-permissions.md` before generating** — it contains the complete list of valid permission paths organized by Twilio product (Messaging, Voice, Video, Verify, TaskRouter, etc.).

## Required permissions on the auth principal

The configured API key must include at minimum:
- `/twilio/iam/api:keys/create`
- `/twilio/iam/api:keys/delete`
- `/twilio/iam/api:keys/view`
