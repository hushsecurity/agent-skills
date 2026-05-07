# gcp_wif

GCP Workload Identity Federation credential. **No privilege type, no `secretRef`.**

The workload exchanges Hush-issued tokens for GCP credentials via the Workload Identity Pool.

## Credential

```yaml
config:
  project_number: <gcp-project-number>
  pool_id: <workload-identity-pool-id>
  workload_provider_id: <provider-id>
  audience: <optional-audience>
# no secretRef
```

## Privilege

**No privilege type for `gcp_wif`.** Policies referencing a GCP WIF credential must omit `accessPrivilegeRefs`.

## Delivery

Use `deliveryConfig.type: gcp_wif`. The credential type and delivery type must match for WIF.

```yaml
deliveryConfig:
  type: gcp_wif
  config:
    subject_kind: hush_subject          # or service_account
    subject: my-subject                 # required when subject_kind=hush_subject
    service_account: optional@proj.iam.gserviceaccount.com
    service_account_token_lifetime: 3600
```

WIF constraints:
- `k8s:container-name` attestation is **not** allowed with WIF delivery.
- `subject_kind: service_account` requires both `k8s:ns` and `k8s:sa` attestation criteria.

## Required permissions on the auth principal

The service account associated with your Workload Identity Provider must hold:
- `roles/iam.workloadIdentityUser` — on the Workload Identity Pool
- `roles/iam.serviceAccountTokenCreator` — on the target service accounts
