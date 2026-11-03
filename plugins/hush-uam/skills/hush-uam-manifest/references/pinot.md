# pinot

Apache Pinot credentials and privileges. Dynamic credentials — provisions an ephemeral Pinot `USER` per workload on the broker, through the controller's `/users` API. The user can query; it gets no controller access.

## Credential

```yaml
config:
  host: <controller-hostname>  # the controller, not a broker
  port: 9000                    # default; the controller port
  username: <root-username>     # required; an ADMIN user
  tls: false                    # default
  tls_ca: <optional-pem>
  broker_url: <optional-url>    # e.g. http://pinot-broker:8099
secretRef:
  name: <k8s-secret>
  # canonical key: password
```

`secretRef` keys: `password`.

`host` and `port` name the **controller**: that is where Hush writes users. Queries go to a broker, which is what `broker_url` names. It is optional, but set it whenever the cluster has a broker the workload queries:

- Hush uses it to check, after each write, that the broker refuses a wrong password and accepts the generated one. Without it, a broker that does not read users from ZooKeeper goes unnoticed and the workload gets a credential that does not work.
- It is the only way to give the workload a query URL in a template (see below).

`broker_url` must be an `http://` or `https://` URL with no username, password, query, fragment or whitespace, and a valid port; a trailing `/` is dropped. Behind a load balancer the check reaches one broker only. Pinot 1.0 answers a wrong password the same way as a user without table access, so there the check proves only that the broker enforces authentication.

`tls` sets only the controller's scheme; `broker_url` carries its own. `tls_ca` verifies the broker as well as the controller, in place of the system CAs, so an `https://` broker needs a certificate from that CA too. With `tls: true` and no `tls_ca`, neither certificate is verified. A broker certificate that does not verify fails the check with a connection error, which is retried rather than reported as a configuration error: when a policy with an `https://` broker never becomes ready, check `tls_ca` first.

## Privilege

```yaml
config:
  grant:                                # singular — one grant object
    tables: [orders, customers]         # optional; omit for all tables
    exclude_tables: [payroll]           # optional
```

The grant names tables only. `grant: {}` queries all tables. There is no `components`, `permissions` or role: the user is a broker `USER`, and the API rejects any other field. Pinot's controller checks neither role nor tables on its `/users` API, so a controller user could make itself `ADMIN`.

- `tables` — **omit it for all tables.** An empty list is rejected, since Pinot would read it as all tables too.
- `exclude_tables` — tables denied even when `tables` is omitted. Also never an empty list. Needs Pinot **1.4.0** or later. An older Pinot ignores the field and would grant every table, so Hush refuses to provision it there and the policy fails, as it does when the controller's `/version` does not tell its version; the privilege itself is accepted. Ask the user's Pinot version before emitting it.
  - Hush reads the controller's version only, but the brokers enforce the field. Pinot upgrades the controller first, so while a broker still runs an older Pinot, a user written in that window can read the excluded tables through it, until that broker is upgraded.
  - Spell each name exactly as the table is named. Pinot matches the list case-sensitively, so `Events` does not exclude `events`, and a typo excludes nothing.
- Name tables without their `_OFFLINE` / `_REALTIME` suffix; the API rejects a suffixed name, since Pinot matches raw table names.

Predefined privilege: **Query All Tables** (`grant: {}`).

## Required permissions on the auth principal

- The cluster must keep its users in ZooKeeper: `controller.admin.access.control.factory.class` set to `org.apache.pinot.controller.api.access.ZkBasicAuthAccessControlFactory`, and `pinot.broker.access.control.class` set to `org.apache.pinot.broker.broker.ZkBasicAuthAccessControlFactory`. Under static (`BasicAuthAccessControlFactory`) or no auth, a user write succeeds and grants nothing, so Hush refuses the controller and the policy fails.
- The root user must have role **`ADMIN`** on the `CONTROLLER` component: it creates and deletes users, and reads the controller's `/appconfigs`, which is how Hush checks the factory above. Nothing in between (a proxy, an ingress rule) may block `/appconfigs` or `/users`.

## Pinot limits

These hold whatever the grant says; mention them when the user relies on `tables` or `exclude_tables` to keep data private.

- With the time series engine enabled (`pinot.timeseries.languages`), the broker checks neither the credential nor the tables on `/query/timeseries` and `/timeseries/api/v1/*`.
- Below Pinot 1.6, a query on a granted table can read any dimension table through `lookUp()`.

## Connection-string template

There is no single connection string — Pinot clients take a URL and a basic-auth pair. The default delivery exposes:

| Env var | Field |
| --- | --- |
| `PINOT_USERNAME` | `username` |
| `PINOT_PASSWORD` | `password` |

When the credential has a `broker_url`, a query URL is available as a template:

```
${broker_url}/query/sql
```

Only offer it when `broker_url` is set — the credential has no other field that names a broker.

## Terraform

There are no `hush_pinot_access_credential` / `hush_pinot_access_privilege` resources yet. See *Provider gaps* in [`terraform.md`](terraform.md): on the Terraform target, do not emit Pinot HCL.
