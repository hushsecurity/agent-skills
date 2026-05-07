# aws_access_key

AWS access key credentials and privileges. Dynamic credentials — provisions ephemeral IAM users + access keys.

## Credential

```yaml
config:
  access_key_id: <aws-access-key-id>   # optional; pair with secret_access_key
secretRef:                             # only if access_key_id is set
  name: <k8s-secret>
  # canonical key: secret_access_key
```

`secretRef` keys: `secret_access_key` (paired with `access_key_id`; both must be set or both omitted).

## Privilege

```yaml
config:
  policies:                             # min 1; AWS IAM policy ARNs (must be unique)
    - arn:aws:iam::aws:policy/ReadOnlyAccess
```

ARN pattern: `^arn:aws[^:]*:iam::[^:]*:policy/.+$`.

## Required permissions on the auth principal

Either AWS's built-in IAM administration policy, or a custom policy granting:
- `iam:CreateUser`
- `iam:DeleteUser`
- `iam:CreateAccessKey`
- `iam:DeleteAccessKey`
- `iam:AttachUserPolicy`
- `iam:DetachUserPolicy`
- `iam:TagUser`
- `iam:ListAttachedUserPolicies`
- `iam:ListAccessKeys`
