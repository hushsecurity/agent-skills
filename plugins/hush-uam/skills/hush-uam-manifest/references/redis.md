# redis

Redis credentials and privileges. Dynamic credentials — provisions ephemeral Redis users via ACL.

Four backends, selected by `config.engine`:

- `redis` — a directly reachable Redis/Valkey server. Hush connects with a root user (username/password) and mints ephemeral ACL users on it.
- `elasticache` — an AWS ElastiCache replication group. Hush authenticates to AWS and manages users through an ElastiCache user group.
- `aiven` — an Aiven-managed Valkey service. Hush connects with an Aiven REST API token and mints the user via the Aiven API; it resolves the host/port itself, so no connection fields are supplied. Requires hush-uam ≥ v0.17.0.
- `azure_managed_redis` — an Azure Managed Redis cluster (`Microsoft.Cache/redisEnterprise`). AMR has no password users, so each credential is an **Entra ID application** instead of a Redis ACL user; Hush resolves the endpoint from ARM. Requires hush-uam ≥ v0.18.0, which is **not released yet**.

`engine` selects which other fields are valid, and is **fixed at create** — it cannot be changed later (ignored on update). Each engine accepts only its own fields: supplying a field that belongs to another engine is rejected, and every field the chosen engine requires must be present at create.

## Credential

### `engine: redis`

```yaml
config:
  engine: redis               # redis | elasticache | aiven | azure_managed_redis
  host: <hostname>            # required
  port: 6379                  # default
  username: <root-username>   # optional
  database: 0                 # default
  tls: false                  # default
  tls_ca: <optional-pem>
secretRef:
  name: <k8s-secret>
  # canonical key: password (required)
```

Required at create: `host`, `password`. `cache_engine` must not be set; AWS-, Aiven- and Azure-only fields must not be set.

`secretRef` keys: `password`.

### `engine: elasticache`

```yaml
config:
  engine: elasticache
  host: <hostname>                            # required (configuration endpoint)
  cache_engine: redis                         # required; redis | valkey
  region: <aws-region>                        # required
  user_group_id: <elasticache-user-group-id>  # required
  access_key_id: <aws-access-key-id>          # optional; with secret_access_key
  tls: false                                  # default
  tls_ca: <optional-pem>
secretRef:
  name: <k8s-secret>
  # canonical key: secret_access_key (only with access_key_id)
```

Required at create: `host`, `cache_engine` (one of `redis`, `valkey`), `region`, `user_group_id`. `password` must not be set, and neither may the Aiven- or Azure-only fields.

`access_key_id` + `secret_access_key` are both-or-neither: omit both to use workload identity federation / instance role; provide both to use static AWS keys.

`secretRef` keys: `secret_access_key` (only when `access_key_id` is set).

### `engine: aiven`

```yaml
config:
  engine: aiven
  project: <aiven-project>         # required; Aiven project name
  service_name: <aiven-service>    # required; Aiven service name
secretRef:
  name: <k8s-secret>
  # canonical key: token (required)
```

Required at create: `project`, `service_name`, `token`. None of the redis/elasticache connection or auth fields (`host`, `port`, `password`, `username`, `database`, `tls`, `tls_ca`, `cache_engine`, `region`, `user_group_id`, `access_key_id`, `secret_access_key`) and none of the Azure fields (`tenant_id`, `client_id`, `client_secret`, `subscription_id`, `resource_group`, `cluster_name`) may be set — Hush resolves the endpoint and mints the user via the Aiven API.

`secretRef` keys: `token` (an Aiven REST API token).

> The aiven engine takes **no `cache_engine`**. Aiven provisions only valkey-family services (post-2024 Redis relicensing), and Hush resolves the actual variant from the live service — the ACL model is identical either way. Supplying `cache_engine` on an aiven credential is rejected.

### `engine: azure_managed_redis`

```yaml
config:
  engine: azure_managed_redis
  tenant_id: <uuid>                    # required; Entra tenant of the root app
  subscription_id: <uuid>              # required; subscription holding the cluster
  resource_group: <rg-name>            # required; 1-90 chars, ARM naming rules
  cluster_name: <amr-cluster>          # required; 1-60 chars, alphanumeric + single hyphens
  client_id: <root-app-client-id>      # optional; both-or-neither with client_secret
secretRef:
  name: <k8s-secret>
  # canonical key: client_secret (only with client_id)
```

Required at create: `tenant_id`, `subscription_id`, `resource_group`, `cluster_name` — all four must be present, and none of them can be unset later.

Field constraints (validated by the API, so a bad value is rejected at reconcile, not at apply):

- `tenant_id`, `subscription_id` — must be UUIDs.
- `resource_group` — 1-90 characters matching ARM's rule: letters, digits, `_`, `-`, `.`, `(`, `)`, and it may not end with a period.
- `cluster_name` — 1-60 characters, alphanumeric segments joined by single hyphens (`^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$`): no leading or trailing hyphen, no consecutive hyphens, no underscores or periods.
- `client_id` — a 1-256 character string. It is *not* validated as a UUID, even though Entra app IDs are UUIDs in practice.

`cluster_name` is the **Azure Managed Redis** cluster (`Microsoft.Cache/redisEnterprise`). This engine does **not** support classic Azure Cache for Redis (`Microsoft.Cache/Redis`).

`client_id` + `client_secret` are the **root** credential Hush uses to drive the Graph and ARM calls, and are both-or-neither: omit both to use the provider default credential chain (the workload identity hush-uam itself runs as); supplying only one is rejected. On update, changing **either `client_id` or `tenant_id`** requires supplying a matching `client_secret` in the same change: the stored secret is issued for one app in one tenant, so moving either half needs a new one. The other three locators (`subscription_id`, `resource_group`, `cluster_name`) are exempt — one root app can legitimately drive several clusters. Re-sending an unchanged `client_id`/`tenant_id` is a no-op. Rotating `client_secret` triggers a full re-provision (a fresh Entra identity is minted).

None of the redis/elasticache/aiven fields (`host`, `port`, `password`, `username`, `database`, `tls`, `tls_ca`, `cache_engine`, `region`, `user_group_id`, `access_key_id`, `secret_access_key`, `token`, `project`, `service_name`) may be set — Hush reads the cluster endpoint and port from ARM. AMR clusters carry a single database, always named `default`, so there is no `database` to select.

> The rejection is **presence-based**, not value-based: emitting one of those keys with an explicit empty/null value (e.g. `host: null`) is rejected just the same. Omit the key entirely.

`secretRef` keys: `client_secret` (only when `client_id` is set).

## Adding an engine (maintainers)

Field exclusivity is stated per engine above, in one of two styles, and the choice is deliberate: `redis` and `elasticache` describe the fields they exclude in prose ("Aiven- or Azure-only fields"), while `aiven` and `azure_managed_redis` enumerate every excluded field by name. The enumeration exists where it earns its cost — those two engines resolve the endpoint themselves, and a model writing *any* redis credential has a strong prior that it needs a `host` and `port`, so the section has to say outright that it must not supply them.

So when adding an engine here:

- **If Hush resolves the endpoint for it, enumerate the common connection fields as forbidden** — `host`, `port`, `password`, `username`, `database`, `tls`, `tls_ca` — plus the other engines' own fields. Omitting them is the one gap that actually misleads: the skill will invent a `host` for an engine that takes none. Prose alone is not enough for this class of engine.
- If it takes a `host` like `redis`/`elasticache` do, prose naming the other engines' field groups is sufficient. Nothing prompts a model to add `tenant_id` to a host-based credential.
- Update the sibling sections' exclusion lists with the new engine's fields, add the engine to the backend list at the top of this file, and record any version floor in the `## Compatibility` table in `SKILL.md`.

## Privilege

```yaml
config:
  grants:                              # min 1
    - type: category                   # or "command"
      action: include                  # or "exclude"
      name: read                       # category or command name (lowercase)
  keys: ["*"]                          # min 1; key glob patterns (each: no whitespace)
  channels: ["*"]                      # optional; pubsub channel patterns (each: no whitespace)
```

Valid categories: `read`, `write`, `keyspace`, `string`, `hash`, `list`, `set`, `sortedset`, `stream`, `pubsub`, `admin`, `fast`, `slow`, `blocking`, `dangerous`, `connection`, `transaction`, `scripting`, `bitmap`, `hyperloglog`, `geo`, `all`.

**For `type: command`, you MUST read `references/redis-commands.md` before generating** — it contains the complete list of valid command names.

Combining categories and commands is supported (e.g. include category `read`, exclude command `keys`).

Each `keys` and `channels` entry must be a single whitespace-free ACL-rule token: a pattern like `user:*` is fine, but a value containing spaces (e.g. `"foo bar"`) is rejected.

The privilege schema is the same for all four engines. For `azure_managed_redis` the grants are carried by an AMR access policy assignment rather than a Redis ACL user; Hush passes the rule through as the assignment's access string and always scopes channels explicitly, so the grant does not depend on the cluster's `acl-pubsub-default`. Authentication-related ACL tokens have no meaning there (Entra owns authentication) and are dropped.

A consequence worth raising with the user: **a privilege that names no `channels` grants none.** Pub/sub must be granted by naming patterns explicitly (e.g. `events:*`), which arrive verbatim after the reset. A privilege written for a cluster set to `allchannels` may have been relying on channels it never named — those deliver nothing here.

## Required permissions on the auth principal

- **`engine: redis`** — the configured root user must have the `@admin` ACL category (full administrative access) to provision and manage ephemeral users.
- **`engine: elasticache`** — the AWS principal (static keys, or the federated/instance role when keys are omitted) must be authorized to manage ElastiCache users and the target ElastiCache user group.
- **`engine: aiven`** — the `token` must be an Aiven REST API token whose account has operator/admin rights on the project, enough to create service users on the target service.
- **`engine: azure_managed_redis`** — the root principal (the `client_id`/`client_secret` pair, or the workload identity when both are omitted) needs all of:
  - **Microsoft Graph:** `Application.ReadWrite.OwnedBy` as an **application** permission, with admin consent. Hush creates and deletes Entra applications, reads them back, creates service principals, and adds/removes passwords — and only ever touches applications it created itself, which this permission covers because it makes the caller the owner of every application it registers. Grant the broader `Application.ReadWrite.All` **only** if the same root credential also backs an `azure_app` credential managing a pre-existing application; `OwnedBy` cannot reach an app Hush did not create.
  - **ARM actions on the cluster** (built-in role that includes them, or a custom role), scoped to the cluster or its resource group — subscription-wide is not required:
    ```
    Microsoft.Cache/redisEnterprise/read
    Microsoft.Cache/redisEnterprise/databases/read
    Microsoft.Cache/redisEnterprise/databases/accessPolicyAssignments/read
    Microsoft.Cache/redisEnterprise/databases/accessPolicyAssignments/write
    Microsoft.Cache/redisEnterprise/databases/accessPolicyAssignments/delete
    ```
  - **Network egress** from hush-uam to `login.microsoftonline.com`, `graph.microsoft.com`, and `management.azure.com`.
  - **API version availability:** access policy assignments are created against the `2026-05-01-preview` version of `Microsoft.Cache` (the stable versions grant full access only), so the subscription must be able to serve that version. Only the assignment operations need it — cluster and database reads, which resolve the endpoint host and port, use the stable `2025-07-01` version, so the preview dependency is confined to granting access, not to reaching the cluster.

  Misconfiguration here fails **permanently** — a `403` maps to a permission error, `400`/`404` to a configuration error, and a failed token acquisition (a bad or expired `client_secret`, a wrong `client_id`/`tenant_id`, blocked egress to `login.microsoftonline.com`) to a connection error. None of the three is retried while provisioning, despite "connection error" sounding transient. The credential stays failed until the Azure side is fixed and the credential is re-created. Note that Entra app secrets expire, so a credential that has been working will fail this way once the root app's secret lapses. Surface this to the user when generating an `azure_managed_redis` credential.

## Connection-string template

```
redis://${username}:${password}@${host}:${port}/${database}
```

- `engine: elasticache` — `${password}` is unavailable (ElastiCache uses AWS auth); adjust accordingly.
- `engine: aiven` — `${username}`, `${password}`, `${host}`, `${port}` are auto-generated / resolved by Hush and available in templates, but there is no `${database}` (no selectable DB) and `tls_ca` is not delivered (the project CA is supplied out of band). `engine`, `project`, and `service_name` are also available.
- `engine: azure_managed_redis` — **there is no connection-string template.** No `${password}` exists: the workload exchanges the delivered client pair for an Entra token scoped to `https://redis.azure.com/.default` and AUTHs with `username` plus that token. Use split delivery items (below), never a template.

## Delivery notes — `engine: azure_managed_redis`

The default delivery exposes the per-lease identity under the names `DefaultAzureCredential` already reads, so an Azure SDK in the workload picks them up with no extra wiring:

| Env var | Credential field |
|---|---|
| `AZURE_TENANT_ID` | `tenant_id` |
| `AZURE_CLIENT_ID` | `client_id` |
| `AZURE_CLIENT_SECRET` | `client_secret` |
| `REDIS_USERNAME` | `username` |
| `REDIS_HOST` | `host` |
| `REDIS_PORT` | `port` |

Available fields for custom delivery items:

- **Auto-generated per lease:** `client_id`, `client_secret`, `username`, `host`, `port`, `tls`.
- **Static (from `config`):** `engine`, `tenant_id`, `subscription_id`, `resource_group`, `cluster_name`.

There is **no `password`**, no `database`, and no `tls_ca` to deliver.

> The delivered `client_id`/`client_secret` are **not** the root pair from the credential's `config`/`secretRef` — they are the freshly minted per-credential Entra application. `username` is that application's service principal object ID. Don't conflate the two when writing delivery items.

Two behaviours worth telling the user about:

- **TLS is always on, but the default delivery doesn't carry it.** AMR accepts only TLS connections and `tls` is delivered as `"true"` — but it is *not* one of the six default env vars above, so a workload reading only those gets no TLS signal and must enable TLS in its own client config. Add an explicit `tls` item if the workload keys off it. (No redis engine delivers TLS as an env var; this is a property of the delivery defaults, not of this engine.)
- **Retry the first token acquisition.** Hush waits for the access policy assignment to report success before delivering, but that is a control-plane signal — it confirms the assignment exists, not that the new client pair can already get a token. Entra propagation lags, so a workload that authenticates the instant it receives the secret may fail for a short period. Nothing in the apply path closes this gap.
