# postgres

PostgreSQL credentials and privileges. Dynamic credentials — the operator provisions ephemeral DB users.

## Credential

```yaml
config:
  db_name: <database-name>
  host: <hostname>
  port: 5432                  # default
  ssl_mode: prefer            # default; one of: disable, allow, prefer, require, verify-ca, verify-full
  ssl_ca: <optional-pem>
  username: <root-username>
secretRef:
  name: <k8s-secret>
  # canonical key: password
```

`secretRef` keys: `password`.

## Privilege

```yaml
config:
  member_of: [app_owner]              # optional; existing roles the user joins
  grants:                             # optional when member_of is set
    - privileges: [SELECT, INSERT]    # cannot mix ALL with specific
      object_type: TABLE
      object_names: [public]
      column_names: [col1, col2]      # optional, TABLE/VIEW only
      all_in_schema: true             # only for TABLE/VIEW/SEQUENCE/FUNCTION/PROCEDURE/ROUTINE
```

Valid `object_type`: `TABLE`, `VIEW`, `SEQUENCE`, `DATABASE`, `SCHEMA`, `FUNCTION`, `PROCEDURE`, `ROUTINE`, `LARGE OBJECT`, `TABLESPACE`, `DOMAIN`, `TYPE`, `LANGUAGE`, `FOREIGN DATA WRAPPER`, `FOREIGN SERVER`, `PARAMETER`.

Valid privileges per `object_type`:
- `TABLE`, `VIEW`: `ALL`, `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `REFERENCES`, `TRIGGER`, `MAINTAIN`
- `SEQUENCE`: `ALL`, `USAGE`, `SELECT`, `UPDATE`
- `DATABASE`: `ALL`, `CREATE`, `CONNECT`, `TEMPORARY`, `TEMP`
- `SCHEMA`: `ALL`, `CREATE`, `USAGE`
- `FUNCTION`, `PROCEDURE`, `ROUTINE`: `ALL`, `EXECUTE`
- `LARGE OBJECT`: `ALL`, `SELECT`, `UPDATE`
- `TABLESPACE`: `ALL`, `CREATE`
- `PARAMETER`: `ALL`, `SET`, `ALTER SYSTEM`
- `DOMAIN`, `TYPE`, `FOREIGN DATA WRAPPER`, `FOREIGN SERVER`, `LANGUAGE`: `ALL`, `USAGE`

When `column_names` is set: only `ALL`, `SELECT`, `INSERT`, `UPDATE`, `REFERENCES` are valid.

A privilege needs `grants`, `member_of`, or both; the API rejects one with neither.

### `member_of`

Each name is an existing role the dynamic user is made a member of, with
`GRANT "<role>" TO <user>`. The user inherits the role's privileges and may
`SET ROLE` to it, which is what lets it run `ALTER ... OWNER TO <role>`: a migration
user can create tables and hand them to the application's owner role. No `SET ROLE` is
needed first; Postgres checks the membership, not the session's current role.

- Names are taken literally and quoted, so they are case-sensitive: `App_Owner` is not
  `app_owner`. Each is 1 to 63 characters; no duplicates, and not `public`.
- Hush does not create the role. It must exist before the policy is applied.
- The user gets everything the role has. A superuser role makes the credential
  superuser-equivalent through `SET ROLE`; confirm with the user before emitting one,
  and prefer a role that owns the application's objects and nothing more.
- To be able to own objects in a schema, the role itself needs `CREATE` on it. That is
  set on the role in Postgres, not in the privilege.

`member_of` needs `hush-am` 0.34.0 or later on the policy's deployment. The API checks it
when a policy with such a privilege is created or moved to another deployment, when the
privilege is attached to a policy, and when `member_of` is added to a privilege that
policies already use. On Kubernetes the rejection shows as a sync error on the resource;
on Terraform, at `terraform apply`.

A role the root user cannot grant fails the credential: the access manager reports
`permission denied to grant role`, does not retry, and creates no user. See the
permissions below.

## Required permissions on the auth principal

The configured root user must have privileges to provision dynamic credentials. Choose one:

- **Superuser** — the built-in `postgres` role works out of the box.
- **Custom role:**
  ```sql
  CREATE USER customAdmin WITH PASSWORD '...' CREATEROLE;
  ```
  Then for each target database the user will manage:
  ```sql
  GRANT ALL PRIVILEGES ON DATABASE <db_name> TO customAdmin WITH GRANT OPTION;
  ```
  For each role in a `member_of`, the root user also needs the `ADMIN` option on it:
  ```sql
  GRANT app_owner TO customAdmin WITH ADMIN OPTION;
  ```
  On Postgres 16 and later, a role's creator already has it. Granting a superuser role
  takes a superuser root.

## Connection-string template

```
postgresql://${username}:${password}@${host}:${port}/${db_name}
```

Use with `deliveryConfig.type: env` (or `volume`/`sdk`) and `items[].type: template`.

## Terraform

Two divergences on `hush_postgres_access_privilege`:

- **`object_type` accepts only 5 of the 16 values above** — `TABLE`, `SEQUENCE`,
  `FUNCTION`, `SCHEMA`, `DATABASE`. The rest are unreachable from Terraform.
- **`object_names` is marked Optional but the API requires it.** Omitting it plans cleanly
  and fails at apply. Always emit it. With `all_in_schema = true` it lists *schemas*, not
  individual objects.

`grants` is a repeated block, not a list; optional when `member_of` is set. `member_of` is
a set of strings, and needs a provider release after 1.40.0. Credential secret:
`password` / `password_wo` + `password_wo_version`.
