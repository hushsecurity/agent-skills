# azure_wif

Azure Workload Identity Federation credential. **No privilege type, no `secretRef`.**

The workload exchanges Hush-issued tokens for Azure tokens via federated credentials on an Azure AD application.

## Credential

```yaml
config: {}                     # no user-supplied fields — system-generated
# no secretRef
```

## Privilege

**No privilege type for `azure_wif`.** Policies referencing an Azure WIF credential must omit `accessPrivilegeRefs`.

## Delivery

Use `deliveryConfig.type: azure_wif`. The credential type and delivery type must match for WIF.

```yaml
deliveryConfig:
  type: azure_wif
  config:
    tenant_id: <uuid>
    client_id: <client-id>
    subject_kind: hush_subject          # or service_account
    subject: my-subject                 # required when subject_kind=hush_subject
```

WIF constraints:
- `k8s:container-name` attestation is **not** allowed with WIF delivery.
- `subject_kind: service_account` requires both `k8s:ns` and `k8s:sa` attestation criteria.

## Subject and cloud-side trust

Hush is the OIDC issuer; the credential's `issuer_url` and `audience` are visible in the
Hush UI or API once it exists (not in the CR status). On the Entra application named by
the delivery config's `tenant_id` / `client_id`, add a **federated credential** with
`issuer` = that `issuer_url`, `audience` = that `audience`, and `subject` = the JWT
subject: `hush:federation:<subject>` for `subject_kind: hush_subject`, or
`system:serviceaccount:<k8s:ns value>:<k8s:sa value>` for `subject_kind: service_account`.
Entra caps `issuer`, `subject` and `audience` at 600 characters each.

## Required permissions on the auth principal

Not applicable — there is nothing for Hush to provision. Access is whatever roles the
Entra application holds; the federated credential above only decides who may act as it.
