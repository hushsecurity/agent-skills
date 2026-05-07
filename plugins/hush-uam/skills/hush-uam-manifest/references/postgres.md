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
  grants:
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

## Connection-string template

```
postgresql://${username}:${password}@${host}:${port}/${db_name}
```

Use with `deliveryConfig.type: env` (or `volume`/`sdk`) and `items[].type: template`.
