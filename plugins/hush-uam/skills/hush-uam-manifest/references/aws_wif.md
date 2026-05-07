# aws_wif

AWS Workload Identity Federation credential. **No privilege type, no `secretRef`.**

The credential is system-generated (Hush issues OIDC tokens); the workload exchanges them for AWS credentials via STS at runtime.

## Credential

```yaml
config: {}                     # no user-supplied fields — system-generated
# no secretRef
```

## Privilege

**No privilege type for `aws_wif`.** Policies referencing an AWS WIF credential must omit `accessPrivilegeRefs`.

## Delivery

Use `deliveryConfig.type: aws_wif`. The credential type and delivery type must match for WIF.

```yaml
deliveryConfig:
  type: aws_wif
  config:
    role_arn: arn:aws:iam::123:role/my-role
    subject_kind: hush_subject          # or service_account
    subject: my-subject                 # required when subject_kind=hush_subject
```

WIF constraints:
- `k8s:container-name` attestation is **not** allowed with WIF delivery.
- `subject_kind: service_account` requires both `k8s:ns` and `k8s:sa` attestation criteria.

## Required permissions on the auth principal

Not directly applicable — federation is workload-side; access is enforced by AWS via the role's trust policy. The role's trust policy must accept tokens from Hush's OIDC issuer.
