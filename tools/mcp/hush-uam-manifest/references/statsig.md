# statsig

Statsig credentials and privileges. Dynamic credentials — provisions an ephemeral Statsig server secret key or client API key per workload, through the Console API, and deletes it when the credential rotates.

## Credential

```yaml
secretRef:
  name: <k8s-secret>
  # canonical key: api_key
```

`secretRef` keys: `api_key`.

The credential has no config fields: the key alone names the Statsig project.

## Privilege

```yaml
config:
  key_type: server                      # server (default) or client
  environments: [production]            # optional; omit for every environment
  target_app_id: <app-id>               # optional; omit for every target app
  secondary_target_app_ids: [<app-id>]  # optional
```

- `key_type` — `server` mints a **server secret key**, for a server SDK; `client` mints a **client API key**, for a browser or mobile SDK. There is no console key: a workload never gets the API that manages keys. A client key is public by design, so a short-lived one rarely helps an app that ships it in a bundle; ask whether the workload hands it to a browser at runtime before emitting `client`. A workload that needs both gets two policies.
- `environments` — names from the Statsig project's own environments (by default `development`, `staging`, `production`). Omit for every environment. Never an empty list, and no duplicates. A name the project does not have passes the API and fails the policy when Statsig refuses the key.
- `target_app_id` / `secondary_target_app_ids` — Statsig target app IDs the key is limited to. Omit for every target app.

Predefined privileges: **Server Secret Key** (`key_type: server`) and **Client API Key** (`key_type: client`), both for every environment and target app.

## Required permissions on the auth principal

The `api_key` must be a **Console API key** (it starts with `console-`) with the scopes:

- `omni_read_write`
- `can_access_keys` — without it Statsig refuses to create or list keys (403), and the policy fails with a permission error.

A server secret key or client API key does not work here: Statsig refuses it on the Console API.

## Statsig limits

- Statsig takes up to about five minutes to accept a new key everywhere. Until then `statsigapi.net` and the CDN (`api.statsigcdn.com`) answer 401 on some requests and 200 on others, so a workload that starts on a fresh key, after a new policy or a rotation, can fail its SDK initialization and must retry. Pods already running keep the previous key through the rotation grace. Deleting a key takes effect at once.

## Connection-string template

None. The default delivery exposes:

| Env var | Field |
| --- | --- |
| `STATSIG_API_KEY` | `api_key` |

## Terraform

`hush_statsig_access_credential` takes `api_key` / `api_key_wo` + `api_key_wo_version`. `hush_statsig_access_privilege` takes the privilege's fields as top-level arguments; `environments` and `secondary_target_app_ids` are sets. Removing an optional argument widens the key again. Both need a provider release after 1.41.0.
