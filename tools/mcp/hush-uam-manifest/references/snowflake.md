# snowflake

Snowflake credentials and privileges. Dynamic credentials — provisions ephemeral users via Snowflake SQL.

## Credential

```yaml
config:
  account: <snowflake-account>
  warehouse: <warehouse-name>
  database: <database-name>
  schema: PUBLIC              # default
  role: <optional-role>
  username: <root-username>
  auth_method: password       # or "key-pair"
secretRef:
  name: <k8s-secret>
  # canonical key depends on auth_method:
  #   password (auth_method=password)
  #   private_key (auth_method=key-pair)
```

`secretRef` keys: `password` when `auth_method=password`; `private_key` when `auth_method=key-pair`.

## Privilege

```yaml
config:
  grants:                               # min 1
    - privileges: [SELECT]              # or ["ALL"]
      resource_type: table              # see list below
      resource_names: [my_table]        # forbidden for resource_type=database/schema
```

Valid `resource_type`: `database`, `schema`, `table`, `view`, `warehouse`, `dynamic_table`, `external_table`, `file_format`, `function`, `materialized_view`, `pipe`, `procedure`, `sequence`, `stage`, `stream`, `task`.

**You MUST read `references/snowflake-privileges.md` before generating** — it contains the complete privilege list per resource type.

Use `["ALL"]` to grant every privilege valid for the resource type. When `resource_names` is omitted on schema-scoped object types (e.g. `table`, `view`, `function`), the grant covers all current and future objects of that type in the schema.

## Required permissions on the auth principal

The user's active role must have:
- `CREATE USER` — create new users
- `CREATE ROLE` — create new roles
- `MANAGE GRANTS` — manage grants to users and privileges on objects
- `USAGE ON WAREHOUSE` — execute queries
- `USAGE ON DATABASE` — reference the database in grants
- `USAGE ON SCHEMA` — reference the schema in grants

## Connection-string template

```
snowflake://${username}@${account}/${database}/${schema}?warehouse=${warehouse}&role=${role}
```

For `auth_method: key-pair`, `${password}` won't resolve — use a separate item or omit credential auth from the connection string.
