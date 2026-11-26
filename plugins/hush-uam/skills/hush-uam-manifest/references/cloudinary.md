# cloudinary

Cloudinary credentials and privileges. Dynamic credentials — provisions an ephemeral Cloudinary product environment API key (key and secret) per workload, through the Provisioning API, gives it a role through the Permissions API, and deletes it when the credential rotates.

## Credential

```yaml
config:
  account_id: <cloudinary-account-id>   # Console: Settings > Account Management Keys
secretRef:
  name: <k8s-secret>
  # canonical keys: api_key, api_secret
```

`secretRef` keys: `api_key`, `api_secret` — an **account management key** and its secret, not a product environment key.

- `account_id` — letters, digits, `-` and `_` only. Changing it needs a new `api_key` and `api_secret` in the same change, since an account management key works only in its own account, and is refused while any access policy uses the credential: Hush could not revoke the old account's keys.

## Privilege

```yaml
config:
  cloud_name: <product-environment-cloud-name>
  role_id: cld::role::prodenv::editor      # either a built-in role ...
  # system_policy_ids:                     # ... or system policies, never both
  #   - cld::policy::global::folder_and_asset_management::create_asset
```

- `cloud_name` — the product environment the key lives in, as it appears in its delivery URLs (`res.cloudinary.com/<cloud_name>/...`). 2-128 letters, digits and hyphens, starting with a letter; matched case-insensitively.
- Exactly one of:
  - `role_id` — one of Cloudinary's built-in product environment roles: `cld::role::prodenv::master_admin`, `admin`, `tech_admin`, `mediaflows_admin`, `ml_admin`, `ml_user`, `reports`, `viewer`, `contributor`, `editor`, `moderator`, `access_to_delivery_url`, `can_create_collections`, `proof_manager`, `owned_collections_distributor` (each with the `cld::role::prodenv::` prefix). A custom role of the customer's is not accepted; use `system_policy_ids`.
  - `system_policy_ids` — Cloudinary system policy IDs from its role catalog, `cld::policy::global::...` only (content and saved-search policies need a folder or collection the privilege cannot name). 1-200, no duplicates; order does not matter. Hush creates one custom role per privilege version from them, named `hush_<privilege id>_<version>`, shares it across every policy and rotation of that version, and deletes it with its last key.

**API key access is accepted but defeats revocation.** The four admin roles (`master_admin`, `admin`, `tech_admin`, `mediaflows_admin`) and `cld::policy::global::api_keys::manage` let a workload create API keys of its own; Hush never revokes those, so they outlive rotation and the policy. `cld::policy::global::api_keys::view` lets it read every key's secret, the environment's own keys included. Pick a role without them (`editor` covers most asset work). Emit one only when the user asks for it, with a post-generation note saying so.

Some `cld::policy::global::...` policies are account policies (`scope_type: account` in the catalog), such as `account_api_keys::manage`, `users_and_groups::manage` or `billing::view`. The API refuses them ("is an account policy"): a product environment role does not hold them. Use only policies the catalog lists with `scope_type: prodenv`. Use only policies the catalog lists with `scope_type: prodenv`.

To switch a privilege between `role_id` and `system_policy_ids`, set the old one to `null` in the same change that sets the other; on Kubernetes that needs server-side apply, see below. Any change to `cloud_name`, `role_id` or `system_policy_ids` issues new keys to every policy using the privilege.

No predefined privileges: `cloud_name` differs per customer.

### Switching grants on Kubernetes

The operator sends `null` to the API as it is, but plain `kubectl apply` removes it before the operator sees it, and the operator leaves a missing key alone in Hush. So a switch from `role_id` to `system_policy_ids`, or back, keeps the old grant next to the new one, and the API refuses the change: `set exactly one of role_id and system_policy_ids`. An empty value does not help: `system_policy_ids: []` and an empty `role_id` are both refused.

`null` survives only server-side apply: `kubectl apply --server-side`, or in Argo CD the sync option `ServerSideApply=true`, for the whole application or for this resource alone with the annotation `argocd.argoproj.io/sync-options: ServerSideApply=true`. So emit the old grant as `null` (`role_id: null` or `system_policy_ids: null`) only with a post-generation note that says to apply the AccessPrivilege server-side, and why.

When the user cannot apply server-side, do not edit the existing AccessPrivilege. Create a new one under a new `metadata.name` with the new grant, and point the AccessPolicy at it. Tell the user why.

Changing `cloud_name`, or replacing one `role_id` or one list of `system_policy_ids` with another, needs no `null` and works with plain apply.

## Required permissions on the auth principal

- The account must be on Cloudinary's **Enterprise** plan with the **Provisioning API enabled** (Cloudinary enables it on request). Lower plans have no account management keys and no Permissions API, so the credential cannot work there.
- The account management key must itself hold **every role or policy a privilege hands out** in that product environment: Cloudinary refuses (403) to assign more than the assigner has, and the policy fails with a permission error.
- Hush reaches `api.cloudinary.com` from the cluster.

## Cloudinary limits

- Cloudinary refuses to delete the last active key of a product environment; the environment's own keys keep that from mattering.
- How soon a new key and its role work has not been measured; a workload that fails its first call on a fresh key should retry.

## Connection-string template

None. The default delivery exposes:

| Env var | Field |
| --- | --- |
| `CLOUDINARY_URL` | `cloudinary_url` (`cloudinary://<api_key>:<api_secret>@<cloud_name>`) |

Cloudinary's SDKs configure from `CLOUDINARY_URL` alone. The fields `cloud_name`, `api_key` and `api_secret` can also be delivered on their own. `account_id` never reaches a workload.

## Terraform

`hush_cloudinary_access_credential` takes `account_id`, `api_key` / `api_key_wo` + `api_key_wo_version` and `api_secret` / `api_secret_wo` + `api_secret_wo_version`; changing `account_id` fails the plan unless the same change carries a new key and secret (or bumps both versions). `hush_cloudinary_access_privilege` takes `cloud_name` and exactly one of `role_id` or `system_policy_ids` as top-level arguments. Both need a provider release after 1.41.0.
