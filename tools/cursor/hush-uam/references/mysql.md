# mysql

MySQL credentials and privileges. Dynamic credentials — the operator provisions ephemeral DB users.

## Credential

```yaml
config:
  db_name: <database-name>
  host: <hostname>
  port: 3306                  # default
  username: <root-username>
  ssl_mode: preferred         # default; one of: disabled, preferred, required, verify-ca, verify-identity
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
- `database`: `ALL`, `CREATE`, `CREATE ROUTINE`, `CREATE TEMPORARY TABLES`, `DROP`, `EVENT`, `EXECUTE`, `LOCK TABLES`
- `table`: `ALL`, `ALTER`, `CREATE`, `CREATE VIEW`, `DELETE`, `DROP`, `INDEX`, `INSERT`, `REFERENCES`, `SELECT`, `SHOW VIEW`, `TRIGGER`, `UPDATE`

## Required permissions on the auth principal

The root user needs:
```sql
GRANT CREATE USER ON *.* TO '<root-user>'@'%';
GRANT ALL PRIVILEGES ON <db_name>.* TO '<root-user>'@'%' WITH GRANT OPTION;
```
`CREATE USER` must be granted globally (`*.*`). `ALL PRIVILEGES ... WITH GRANT OPTION` must be granted on each target database.

## Connection-string template

```
mysql://${username}:${password}@${host}:${port}/${db_name}
```

## Terraform

⚠️ **The provider's `ssl_mode` enum is wrong.** `hush_mysql_access_credential` validates
`verify_ca` / `verify_identity` with underscores, but the API expects `verify-ca` /
`verify-identity` with hyphens. Both spellings fail — the underscore form at apply, the
hyphen form at plan — so **certificate verification cannot be configured from Terraform**.
Use `disabled`, `preferred` or `required` and tell the user. (`mariadb` is unaffected; its
enum is correct.)

Secret: `password` / `password_wo` + `password_wo_version`.
