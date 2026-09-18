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

## Subject and cloud-side trust

The credential is the OIDC issuer. Once created, Hush assigns it an `issuer_url`
(`https://<hush am host>/federation/v1/<org-id>/<acr-id>`, e.g.
`am.us.hush-security.com`) and an `audience` (`sts.amazonaws.com`). Both are visible on the credential in the Hush UI or
API — **not** in the CR status — and both go into the AWS-side trust.

The JWT `sub` depends on `subject_kind`:

| `subject_kind` | `sub` claim |
| --- | --- |
| `hush_subject` | `hush:federation:<subject>` |
| `service_account` | `system:serviceaccount:<k8s:ns value>:<k8s:sa value>` |

What the workload gets: the admission controller injects `AWS_WEB_IDENTITY_TOKEN_FILE`
(`/var/run/secrets/hush.security/federation/aws/token`) and `AWS_ROLE_ARN` into every
container, plus a sidecar that refreshes the token. The AWS SDK picks these up on its own.

AWS side, three things: an `aws_iam_openid_connect_provider` whose `url` is the
`issuer_url` and whose `client_id_list` is `["sts.amazonaws.com"]`; the role's trust
policy allowing `sts:AssumeRoleWithWebIdentity` from that provider with a `StringEquals`
on `<issuer host/path>:aud` = `sts.amazonaws.com` and a `StringLike` on
`<issuer host/path>:sub` matching the subject form above; and the role's permissions
policy, which is where what the workload *may do* lives.

## Required permissions on the auth principal

Not applicable — there is nothing for Hush to provision. Access is decided by the IAM
role's trust policy (who may assume it) and permissions policy (what it may do), both
managed on the AWS side as described above.
