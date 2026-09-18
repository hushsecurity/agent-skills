# plaintext

Static credential — a single secret string. **No privilege type, no auth principal.**

## Credential

```yaml
# omit `config` entirely — plaintext has no config fields
secretRef:
  name: <k8s-secret>
  # exactly one entry; its key name does not matter
```

`secretRef` keys: `secret` is the credential's single sensitive field, but the operator does not require that key name. Without `keyMappings` the Secret must hold **exactly one entry**, whatever its key, and that value becomes `secret`. A Secret with more than one entry is rejected as ambiguous — select the right one with `keyMappings: {secret: <key>}`.

**Do not emit `config: {}`** — for `plaintext`, the `config` field should be omitted entirely from `spec`.

## Privilege

**No privilege type for `plaintext`.** Static credentials cannot have privileges. Policies must omit `accessPrivilegeRefs`.

## Required permissions on the auth principal

Not applicable — there's no auth principal. The credential is a static secret stored in Hush; nothing is provisioned dynamically.

## Notes

- `PLAINTEXT_ACCESS_CREDS_DEFAULT_KEY = "data"` is the *delivery-side* default when a delivery `items[].key` is omitted — unrelated to the secretRef key.
- A plaintext credential has exactly one value, so the API does not validate delivery `key` names for it. **Omit `key` on the delivery item** (both targets) rather than guessing a field name; keep `type: key`, and only `name`/`path` matters.

## Terraform

There is no `secretRef`. `hush_plaintext_access_credential` takes the value inline as
`secret`, or write-only as `secret_wo` + `secret_wo_version`.
