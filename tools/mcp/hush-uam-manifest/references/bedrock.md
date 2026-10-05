# bedrock

AWS Bedrock credentials. **No privilege type** — policies for `bedrock` must omit `accessPrivilegeRefs`.

## Credential

```yaml
config:
  region: <aws-region>
  access_key_id: <aws-access-key-id>   # optional; pair with secret_access_key
secretRef:                             # only if access_key_id is set
  name: <k8s-secret>
  # canonical key: secret_access_key
```

`secretRef` keys: `secret_access_key` (only if `access_key_id` is set; both must be set or both omitted).

## Privilege

**No privilege type for `bedrock`.** Policies referencing a Bedrock credential must omit `accessPrivilegeRefs`.

## Required permissions on the auth principal

The IAM user or role must have:
- `iam:CreateServiceSpecificCredential` — create service-specific credentials
- `iam:ListServiceSpecificCredentials` — list existing credentials
- `iam:UpdateServiceSpecificCredential` — update credential status
- `iam:DeleteServiceSpecificCredential` — delete credentials
- `iam:ResetServiceSpecificCredential` — reset credential passwords
- `iam:CreateUser` — create IAM users
