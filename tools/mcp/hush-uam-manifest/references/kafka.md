# kafka

Kafka credentials and privileges. Dynamic credentials — provisions an ephemeral per-workload Kafka user (one principal per credential rotation) and grants it the requested ACLs. Requires hush-uam ≥ v0.15.0.

Two backends, selected by `config.engine`:

- `native` — a self-hosted / self-managed Kafka cluster. Hush connects with an admin SASL user and mints SCRAM users + ACLs directly on the brokers.
- `aiven` — an Aiven-managed Kafka service. Hush connects with an Aiven API token and creates Aiven service users + native ACLs via the Aiven API.

`engine` is a **required** field in `config` that selects which other fields are valid. It is **fixed at create** — you cannot change a credential's engine later (the field is ignored on update). Each engine accepts only its own fields: supplying a field that belongs to the *other* engine is rejected, and every field the chosen engine requires must be present at create.

> The Hush operator flattens `spec.config` into the API request (each key becomes a top-level field), so although the backend model is flat (no nested `config` object), the **manifest still nests these fields under `config`** — exactly like `postgres`, `redis`, and every other type.

## Credential

### `engine: native`

```yaml
config:
  engine: native
  bootstrap_servers: broker1:9092,broker2:9092   # required; comma-separated host:port list
  username: <admin-username>                      # required; admin SASL user
  sasl_mechanism: SCRAM-SHA-256                   # required; PLAIN | SCRAM-SHA-256 | SCRAM-SHA-512
  tls: false                                      # optional; defaults to false
  tls_ca: <optional-pem>                          # optional; custom CA for broker TLS
secretRef:
  name: <k8s-secret>
  # canonical key: password (required)
```

Required at create: `engine`, `bootstrap_servers`, `username`, `sasl_mechanism`, `password`. `tls` (defaults `false`) and `tls_ca` are optional.

`secretRef` keys: `password` (the admin SASL user's password).

`sasl_mechanism` here is the mechanism Hush's **admin** connection uses and must match what the brokers accept for that user. The mechanism delivered to the workload is chosen by Hush (SCRAM) and is independent of this value.

### `engine: aiven`

```yaml
config:
  engine: aiven
  project: <aiven-project>          # required; Aiven project name
  service_name: <aiven-service>     # required; Aiven Kafka service name
secretRef:
  name: <k8s-secret>
  # canonical key: token (required)
```

Required at create: `engine`, `project`, `service_name`, `token`.

`secretRef` keys: `token` (an Aiven API token).

There is no `bootstrap_servers`/`tls` for the Aiven engine — Hush resolves the service's SASL and mTLS bootstrap endpoints from the Aiven API at provision time.

## Privilege

The privilege schema is the same for both engines — a list of Kafka ACL entries.

```yaml
config:
  acls:                                  # min 1
    - resource_type: Topic               # Topic | Group | Cluster | TransactionalID | DelegationToken | User
      resource_name: "*"                 # name or pattern; "kafka-cluster" for Cluster
      pattern_type: LITERAL              # LITERAL | PREFIXED
      operation: Read                    # Read | Write | Create | Delete | Alter | Describe |
                                         #   ClusterAction | DescribeConfigs | AlterConfigs |
                                         #   IdempotentWrite | All
      permission_type: ALLOW             # ALLOW | DENY
      host: "*"                          # default "*"
```

- `pattern_type` and `permission_type` are validated against the fixed sets above (uppercase).
- `resource_type` and `operation` are passed through to the broker / Aiven API, which rejects unknown values. Use the capitalized forms above (e.g. `Topic`, `Read`). The value sets are large and evolving — these are the common ones.
- For a `Cluster` ACL the conventional `resource_name` is `kafka-cluster`.

### Predefined presets

Offer these well-known shapes before hand-rolling ACLs:

- **Consumer** — read all topics and consumer groups:
  ```yaml
  acls:
    - {resource_type: Topic, resource_name: "*", pattern_type: LITERAL, operation: Read, permission_type: ALLOW, host: "*"}
    - {resource_type: Group, resource_name: "*", pattern_type: LITERAL, operation: Read, permission_type: ALLOW, host: "*"}
  ```
- **Producer** — write and create all topics:
  ```yaml
  acls:
    - {resource_type: Topic, resource_name: "*", pattern_type: LITERAL, operation: Write,  permission_type: ALLOW, host: "*"}
    - {resource_type: Topic, resource_name: "*", pattern_type: LITERAL, operation: Create, permission_type: ALLOW, host: "*"}
  ```
- **Full access** — all operations on topics, groups, and the cluster:
  ```yaml
  acls:
    - {resource_type: Topic,   resource_name: "*",            pattern_type: LITERAL, operation: All, permission_type: ALLOW, host: "*"}
    - {resource_type: Group,   resource_name: "*",            pattern_type: LITERAL, operation: All, permission_type: ALLOW, host: "*"}
    - {resource_type: Cluster, resource_name: "kafka-cluster", pattern_type: LITERAL, operation: All, permission_type: ALLOW, host: "*"}
  ```

## Required permissions on the auth principal

### `engine: native`

- The brokers must have **SASL/SCRAM authentication** and an **ACL authorizer** enabled (e.g. KRaft `StandardAuthorizer` or the ZooKeeper `AclAuthorizer`).
- The admin SASL user supplied via `username` / `secretRef.password` must be authorized to **manage SCRAM user credentials** (`AlterUserScramCredentials`) and to **create and delete ACLs** cluster-wide — i.e. `Alter` on the `Cluster` resource. In practice this means listing the user in the broker's `super.users`, or granting it the equivalent cluster-level ACLs.

### `engine: aiven`

- The `token` must be an Aiven API token (personal or application token) whose account has **admin/operator** rights on the project — enough to create Kafka **service users** and add **native Kafka ACLs** on the target service.
- The Aiven Kafka service must have **native ACL** support enabled (`kafka_authorization_method: acl`).

## Delivery notes

There is no single connection-string template — Kafka clients take discrete settings. Hush delivers a fresh per-workload SASL user; the default delivery exposes these as env vars:

| Env var | Credential field |
|---|---|
| `KAFKA_SASL_USERNAME` | `username` |
| `KAFKA_SASL_PASSWORD` | `password` |
| `KAFKA_SASL_MECHANISM` | `sasl_mechanism` |

Available fields for custom delivery items (e.g. mapping to client config or a properties file):

- **Both engines:** `username`, `password`, `sasl_mechanism` (auto-generated), plus `engine`.
- **native:** `bootstrap_servers`, `tls`, `tls_ca`.
- **aiven:** `bootstrap_servers` (SASL endpoint), `access_bootstrap_servers` (mTLS endpoint), `access_cert`, `access_key` (the mTLS pair Aiven mints alongside the SASL user), plus `project`, `service_name`.
