# plaintext

Static credential — a single secret string. **No privilege type, no auth principal.**

## Credential

```yaml
# omit `config` entirely — plaintext has no config fields
secretRef:
  name: <k8s-secret>
  # canonical key: secret
```

`secretRef` keys: `secret` (the credential's sensitive field name) holds the single secret value. Use `keyMappings` if the existing Secret uses a different key.

**Do not emit `config: {}`** — for `plaintext`, the `config` field should be omitted entirely from `spec`.

## Privilege

**No privilege type for `plaintext`.** Static credentials cannot have privileges. Policies must omit `accessPrivilegeRefs`.

## Required permissions on the auth principal

Not applicable — there's no auth principal. The credential is a static secret stored in Hush; nothing is provisioned dynamically.

## Notes

- `PLAINTEXT_ACCESS_CREDS_DEFAULT_KEY = "data"` is the *delivery-side* default when a delivery `items[].key` is omitted — unrelated to the secretRef key.
