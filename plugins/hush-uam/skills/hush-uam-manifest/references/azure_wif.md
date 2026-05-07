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

## Required permissions on the auth principal

Not directly applicable — federation is workload-side; access is enforced by Azure AD via federated credentials configured on the target application. The Azure AD application must be configured with a federated credential trusting Hush's OIDC issuer.
