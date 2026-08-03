# redis

Redis credentials and privileges. Dynamic credentials — provisions ephemeral Redis users via ACL.

Three backends, selected by `config.engine`:

- `redis` — a directly reachable Redis/Valkey server. Hush connects with a root user (username/password) and mints ephemeral ACL users on it.
- `elasticache` — an AWS ElastiCache replication group. Hush authenticates to AWS and manages users through an ElastiCache user group.
- `aiven` — an Aiven-managed Valkey service. Hush connects with an Aiven REST API token and mints the user via the Aiven API; it resolves the host/port itself, so no connection fields are supplied. Requires hush-uam ≥ v0.17.0.

`engine` selects which other fields are valid, and is **fixed at create** — it cannot be changed later (ignored on update). Each engine accepts only its own fields: supplying a field that belongs to another engine is rejected, and every field the chosen engine requires must be present at create.

## Credential

### `engine: redis`

```yaml
config:
  engine: redis               # redis | elasticache | aiven
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

Required at create: `host`, `password`. `cache_engine` must not be set; AWS- and Aiven-only fields must not be set.

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

Required at create: `host`, `cache_engine` (one of `redis`, `valkey`), `region`, `user_group_id`. `password` must not be set.

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

Required at create: `project`, `service_name`, `token`. None of the redis/elasticache connection or auth fields (`host`, `port`, `password`, `username`, `database`, `tls`, `tls_ca`, `cache_engine`, `region`, `user_group_id`, `access_key_id`, `secret_access_key`) may be set — Hush resolves the endpoint and mints the user via the Aiven API.

`secretRef` keys: `token` (an Aiven REST API token).

> The aiven engine takes **no `cache_engine`**. Aiven provisions only valkey-family services (post-2024 Redis relicensing), and Hush resolves the actual variant from the live service — the ACL model is identical either way. Supplying `cache_engine` on an aiven credential is rejected.

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

The privilege schema is the same for all three engines.

## Required permissions on the auth principal

- **`engine: redis`** — the configured root user must have the `@admin` ACL category (full administrative access) to provision and manage ephemeral users.
- **`engine: elasticache`** — the AWS principal (static keys, or the federated/instance role when keys are omitted) must be authorized to manage ElastiCache users and the target ElastiCache user group.
- **`engine: aiven`** — the `token` must be an Aiven REST API token whose account has operator/admin rights on the project, enough to create service users on the target service.

## Connection-string template

```
redis://${username}:${password}@${host}:${port}/${database}
```

- `engine: elasticache` — `${password}` is unavailable (ElastiCache uses AWS auth); adjust accordingly.
- `engine: aiven` — `${username}`, `${password}`, `${host}`, `${port}` are auto-generated / resolved by Hush and available in templates, but there is no `${database}` (no selectable DB) and `tls_ca` is not delivered (the project CA is supplied out of band). `engine`, `project`, and `service_name` are also available.
