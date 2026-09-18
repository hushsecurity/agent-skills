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

## Subject and cloud-side trust

Hush is the OIDC issuer; the credential's `issuer_url` is visible in the Hush UI or API
once it exists (not in the CR status). Register it as the OIDC provider of the Workload
Identity Pool named by `pool_id` / `workload_provider_id`. GCP requires the token `aud` to
be `https://iam.googleapis.com/projects/<project_number>/locations/global/workloadIdentityPools/<pool_id>/providers/<workload_provider_id>`,
which is what Hush emits when `audience` is left unset — set `audience` only when the
provider was configured with a custom one.

The JWT `sub` depends on `subject_kind`: `hush_subject` gives `hush:federation:<subject>`,
`service_account` gives `system:serviceaccount:<k8s:ns value>:<k8s:sa value>`. The pool
provider's attribute mapping and the grants on the pool and on any `service_account` the
delivery impersonates are GCP-side configuration; the permissions below are what Hush
documents for them.

## Required permissions on the auth principal

The service account associated with your Workload Identity Provider must hold:
- `roles/iam.workloadIdentityUser` — on the Workload Identity Pool
- `roles/iam.serviceAccountTokenCreator` — on the target service accounts
