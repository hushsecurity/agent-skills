# cloudflare_r2

Cloudflare R2 credentials and privileges. Dynamic credentials: provisions an ephemeral Cloudflare account API token per policy version, through the Cloudflare API, and delivers the S3 credentials derived from it. The token is deleted when the version is revoked.

## Credential

```yaml
config:
  account_id: <account-id>   # 32 lowercase hex characters
secretRef:
  name: <k8s-secret>
  # canonical key: api_token
```

`secretRef` keys: `api_token`.

- `account_id` -- the 32 lowercase hex characters on the account's home page and in the dashboard URL. Any other value is rejected.
- `api_token` -- the root token. Hush creates and deletes the workloads' R2 tokens with it; it never reaches a workload. See the permissions below.

A new `account_id` needs a new `api_token` in the same change, since a root token works only in its own account. The API refuses to change the account (409) while any policy or dynamic credential uses the credential. To move to another account, create a credential for it.

## Privilege

```yaml
config:
  permission: object_read_write   # required
  buckets: [photos, exports]      # object permissions only, and required for them
  jurisdiction: default           # default (when omitted), eu, fedramp or us
```

| `permission` | Cloudflare permission group | Reaches |
| --- | --- | --- |
| `object_read_write` | Workers R2 Storage Bucket Item Write | the objects of `buckets` |
| `object_read_only` | Workers R2 Storage Bucket Item Read | the objects of `buckets` |
| `admin_read_write` | Workers R2 Storage Write | the whole account; can also manage buckets |
| `admin_read_only` | Workers R2 Storage Read | the whole account |

- `buckets` -- 1 to 1000 unique R2 bucket names. **An object permission must set the key:** a list, or `null` for every bucket of the account, including buckets created later. Omitting it is rejected, so the widest grant never comes by default; offer `null` only when the user asks for every bucket. On Kubernetes, `null` needs server-side apply; see below. Never an empty list. An admin permission takes no buckets: omit the key, as a list is rejected.
- Bucket names are not checked against the account: the root token cannot list buckets. A misspelled name, or the wrong `jurisdiction`, gives keys that S3 refuses on the real bucket (`404 NoSuchBucket` or `403 AccessDenied`). Confirm the exact names with the user.
- `jurisdiction` -- must match the buckets' jurisdiction. A bucket in a jurisdiction answers only on that jurisdiction's S3 endpoint, so one privilege covers one jurisdiction. A workload with buckets in two jurisdictions gets two policies, delivered under different env names.

There are no predefined privileges.

### Every bucket on Kubernetes

The operator sends `buckets: null` to the API as it is, but plain `kubectl apply` removes it before the operator sees it:

- On create, the request has no `buckets`, and the API refuses it with `buckets is required with an object permission`.
- On a change from a list, the key is gone, so Hush UAM keeps the old list, with no error.

`null` survives only server-side apply: `kubectl apply --server-side`, or in Argo CD the sync option `ServerSideApply=true`, for the whole application or for this resource alone with the annotation `argocd.argoproj.io/sync-options: ServerSideApply=true`. So emit `buckets: null` only with a post-generation note that says to apply the AccessPrivilege server-side, and why.

When the user cannot apply server-side, do not emit `buckets: null`. List the buckets instead, or create the privilege outside Kubernetes, with the Hush API (`"buckets": null`) or Terraform (`all_buckets = true`), and have the AccessPolicy reference it by `id` or by `remoteName` + `type`. Tell the user why.

A change from an object permission to an admin one has the same need. Unless the change sends `buckets: null`, the API keeps the stored list and refuses the change: `is account wide and takes no buckets`. Write `buckets: null` next to the admin permission and apply server-side. Without server-side apply, create a new AccessPrivilege under a new `metadata.name` and point the policy at it.

## Required permissions on the auth principal

The `api_token` must be an **account API token** (dashboard: **Manage Account > Account API Tokens**), created as a custom token with:

- **Permissions**: `Account` | `Account API Tokens` | `Edit`. The API calls it "Account API Tokens Write". It needs no R2 permission.
- **Account Resources**: the account that holds the buckets.

The dashboard user who creates it must be allowed to manage account API tokens. With this one permission the token can create R2 tokens of any level, so treat it like an admin key.

- A token limited to client IP addresses must allow the access manager's egress address.
- A token with an expiry must be replaced before then. Once it expires, new versions and revocations fail with an authentication error.

## Cloudflare limits

- **Token quota.** An account holds at most 500 account API tokens. Each live policy version holds one, named `hush-am-r2-<policy id>-<version>`, and a policy holds two or more while older versions wait for their pods to stop. Plan for about 250 policies per account, minus the account's other tokens. These tokens must not be edited or deleted by hand: pods that use a deleted one lose access until they restart on a new version.
- **Network egress.** The access manager must reach `api.cloudflare.com` on 443. Workloads must reach the S3 endpoint on 443: `https://<account_id>.r2.cloudflarestorage.com`, or `https://<account_id>.<jurisdiction>.r2.cloudflarestorage.com` for `eu`, `fedramp` and `us`.
- **Errors are not retried.** When Cloudflare answers a `4xx` other than `429`, or offers no permission group for the `permission`, the policy fails and stays failed until the credential or the privilege is corrected.

## Connection-string template

None. The workload gets three generated items, and only these: `access_key_id`, `secret_access_key` and `endpoint`, the S3 endpoint of the jurisdiction. Templates can use only them; `account_id` and `api_token` are never delivered. The default delivery uses the names every AWS SDK reads:

| Env var | Field |
| --- | --- |
| `AWS_ACCESS_KEY_ID` | `access_key_id` |
| `AWS_SECRET_ACCESS_KEY` | `secret_access_key` |
| `AWS_ENDPOINT_URL_S3` | `endpoint` |

## Workload setup

Raise these in the post-generation note; the delivery does none of them.

- **The default names replace the pod's own.** Ask whether the pod also calls AWS before emitting them. If it does, its AWS SDK would send the R2 key to AWS (`403 InvalidClientTokenId`) and its S3 calls to R2. Deliver under other names, such as `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` and `R2_ENDPOINT`, and have the app build its R2 client from them.
- **Region.** Hush does not deliver one. R2 takes `auto`, and `us-east-1` as an alias; it answers any other AWS region with `400 InvalidRegionName`. The AWS SDK for Go v2 fails without a region: set `AWS_REGION=auto` in the pod spec, or the region in code. boto3 works without one, but a pod that sets `AWS_DEFAULT_REGION` to an AWS region must give the R2 client `region_name="auto"`.
- **Retry the first call.** S3 refuses a new key with `401` for a few seconds, up to about 6.5 seconds in testing. The workload should retry a `401` at start for up to about 10 seconds, after a new policy or a rotation alike.

## Terraform

`hush_cloudflare_r2_access_credential` takes `account_id` and `api_token` / `api_token_wo` + `api_token_wo_version`. A change to `account_id` fails the plan unless the same change sets a new `api_token` or bumps `api_token_wo_version`.

`hush_cloudflare_r2_access_privilege` takes the privilege's fields as top-level arguments; `buckets` is a set and `jurisdiction` defaults to `default`. **Every bucket is `all_buckets = true`, not a null `buckets`.** An object permission needs `buckets` or `all_buckets = true`, not both, and an admin permission takes neither; the plan checks both rules. Unlike Kubernetes, a change between a list and `all_buckets` needs no special apply.

Both need a provider release after 1.41.0.
