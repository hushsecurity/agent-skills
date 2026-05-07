# mariadb

MariaDB credentials and privileges. Dynamic credentials — the operator provisions ephemeral DB users.

## Credential

Identical schema to `mysql`:

```yaml
config:
  db_name: <database-name>
  host: <hostname>
  port: 3306                  # default
  username: <root-username>
  ssl_mode: PREFERRED         # default
  ssl_ca: <optional-pem>
secretRef:
  name: <k8s-secret>
  # canonical key: password
```

`secretRef` keys: `password`.

## Privilege

```yaml
config:
  grants:
    - privileges: [SELECT]            # or [ALL]
      resource_type: table             # or "database"
      resource_names: [my_table]       # forbidden when resource_type=database
```

Valid privileges:
- `database`: `ALL`, `CREATE`, `CREATE ROUTINE`, `CREATE TEMPORARY TABLES`, `DROP`, `EVENT`, `LOCK TABLES`
- `table`: `ALL`, `ALTER`, `CREATE`, `CREATE VIEW`, `DELETE`, `DELETE HISTORY`, `DROP`, `INDEX`, `INSERT`, `REFERENCES`, `SELECT`, `SHOW VIEW`, `TRIGGER`, `UPDATE`

## Required permissions on the auth principal

The root user must hold:
- `GRANT OPTION` — grant privileges to other users
- `CREATE USER` — create new database users
- `DROP USER` — remove existing database users
- `CREATE ROLE` — create new roles
- `DROP ROLE` — remove existing roles

## Connection-string template

```
mariadb://${username}:${password}@${host}:${port}/${db_name}
```
