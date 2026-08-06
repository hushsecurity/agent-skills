# kv

Static key-value credential — multiple named secret values. **No privilege type, no auth principal.**

## Credential

```yaml
# omit `config` entirely — the operator derives the key-value items from the Secret
secretRef:
  name: <k8s-secret>
  # every Secret key becomes a credential key; use keyMappings to select/rename
```

`secretRef` keys: each key in the Secret becomes one credential key (pattern: `^[a-zA-Z0-9_]{1,64}$`; cannot start with `_hush` or `__hush`), and its value is that key's secret string. With `keyMappings` (`<credential-key>: <secret-key>`), only the mapped entries are forwarded — required whenever the Secret holds unrelated keys.

Non-sensitive values may optionally be inlined as full pairs under `config.items` (plaintext in the manifest); they are merged with the Secret-derived items:

```yaml
config:
  items:
    - key: <name>
      value: <non-secret-value>
secretRef:                       # optional when config.items is present
  name: <k8s-secret>
```

At least one source (`config.items` or `secretRef`) must yield an item, and a key appearing in both is rejected as a duplicate.

## Privilege

**No privilege type for `kv`.** Static credentials cannot have privileges. Policies must omit `accessPrivilegeRefs`.

## Required permissions on the auth principal

Not applicable — there's no auth principal. The credential stores user-supplied secrets; nothing is provisioned dynamically.

## Notes

- `keys` exists only in API *responses* (server-derived, read-only); it is never sent.
- Renaming or removing a Secret key changes the credential's key set on the next reconcile; the API rejects removing a key still referenced by a policy's delivery config.
