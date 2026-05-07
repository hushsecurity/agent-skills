# redis

Redis credentials and privileges. Dynamic credentials — provisions ephemeral Redis users via ACL.

## Credential

```yaml
config:
  host: <hostname>
  port: 6379                  # default
  username: <root-username>   # optional
  database: 0                 # default
  tls: false                  # default
  tls_ca: <optional-pem>
  engine: redis               # or "elasticache"
  # When engine=elasticache, also:
  cache_engine: <engine>
  region: <aws-region>
  user_group_id: <elasticache-user-group-id>
  access_key_id: <aws-access-key-id>
secretRef:
  name: <k8s-secret>
  # canonical keys:
  #   password (required when engine=redis)
  #   secret_access_key (when AWS auth is used)
```

`secretRef` keys: `password` (required when `engine=redis`); `secret_access_key` (when AWS auth is used).

## Privilege

```yaml
config:
  grants:                              # min 1
    - type: category                   # or "command"
      action: include                  # or "exclude"
      name: read                       # category or command name (lowercase)
  keys: ["*"]                          # min 1; key glob patterns
  channels: ["*"]                      # optional; pubsub channel patterns
```

Valid categories: `read`, `write`, `keyspace`, `string`, `hash`, `list`, `set`, `sortedset`, `stream`, `pubsub`, `admin`, `fast`, `slow`, `blocking`, `dangerous`, `connection`, `transaction`, `scripting`, `bitmap`, `hyperloglog`, `geo`, `all`.

**For `type: command`, you MUST read `references/redis-commands.md` before generating** — it contains the complete list of valid command names.

Combining categories and commands is supported (e.g. include category `read`, exclude command `keys`).

## Required permissions on the auth principal

The configured user must have the `@admin` ACL category — full administrative access required to provision and manage ephemeral users.

## Connection-string template

```
redis://${username}:${password}@${host}:${port}/${database}
```

For `engine=elasticache`, `${password}` is unavailable (ElastiCache uses AWS auth) — adjust accordingly.
