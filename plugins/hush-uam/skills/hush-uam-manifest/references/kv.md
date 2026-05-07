# kv

Static key-value credential — multiple named secret values. **No privilege type, no auth principal.**

## Credential

```yaml
config:
  items:
    - key: <name1>             # pattern: ^[a-zA-Z0-9_]{1,64}$; cannot start with _hush or __hush
    - key: <name2>
secretRef:
  name: <k8s-secret>
  # canonical keys: one per items[].key
```

`secretRef` keys: keys named after each `items[].key`; values are the per-item secret strings.

## Privilege

**No privilege type for `kv`.** Static credentials cannot have privileges. Policies must omit `accessPrivilegeRefs`.

## Required permissions on the auth principal

Not applicable — there's no auth principal. The credential stores user-supplied secrets; nothing is provisioned dynamically.
