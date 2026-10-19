# mongodb

MongoDB credentials and privileges. Dynamic credentials — the operator provisions ephemeral DB users.

## Credential

```yaml
config:
  db_name: <database-name>
  host: <hostname>
  port: 27017                 # default
  username: <root-username>
  auth_source: admin          # default
  tls: false                  # default
  tls_ca: <optional-pem>
secretRef:
  name: <k8s-secret>
  # canonical key: password
```

`secretRef` keys: `password`.

## Privilege

```yaml
config:
  grants:
    - privileges: [find, insert]      # or ["all"] (lowercase)
      resource_type: collection        # or "database"
      resource_names: [my_collection]  # forbidden when resource_type=database
      all_databases: false             # default; true applies to every database
```

`all_databases: true` applies the grant to every database instead of the credential's `db_name`. With `resource_names` it means those collections in every database; without, every collection in every database except system collections. That includes `admin`; only `config` and `local` stay out of reach. Grants without it keep the credential's database, so one privilege can mix both.

`all_databases` exists only on `mongodb` grants: a `mongodb_atlas` grant has no such field, and the API rejects it.

Such a grant reaches every database on the server, so prefer `resource_names` with read actions. The read actions are those of MongoDB's built-in `read` role: `changeStream`, `collStats`, `dbHash`, `dbStats`, `find`, `killCursors`, `listCollections`, `listIndexes`, `listSearchIndexes` and `planCacheRead`. Before emitting any other action, or `all`, with `all_databases: true`, confirm with the user and name the reach: every database on the server, `admin` included, with only `config`, `local` and system collections out of reach. The Hush portal asks about the same actions.

MongoDB allows a grant on all databases only in a role scoped to `admin`, so the policy's credential must have `auth_source: admin`. The API rejects:

- a policy pairing such a privilege with a credential whose `auth_source` is not `admin`;
- adding `all_databases` to a privilege that a policy already pairs with a credential whose `auth_source` is not `admin`;
- changing a credential's `auth_source` from `admin` while a policy pairs it with such a privilege.

On Kubernetes, `kubectl apply` succeeds and the rejection shows as a sync error on the resource. On Terraform, it shows at `terraform apply`.

Use `all` to grant every action allowed for the resource type (cannot be mixed with specific privileges).

Valid privileges for `resource_type: database`:

`analyze`, `applicationMessage`, `bypassDocumentValidation`, `bypassWriteBlockingMode`, `changeStream`, `cleanupStructuredEncryptionData`, `collMod`, `collStats`, `compact`, `compactStructuredEncryptionData`, `convertToCapped`, `createCollection`, `createIndex`, `createSearchIndexes`, `dbCheck`, `dbHash`, `dbStats`, `dropCollection`, `dropDatabase`, `dropIndex`, `dropSearchIndex`, `enableProfiler`, `exportCollection`, `find`, `importCollection`, `insert`, `killAnyCursor`, `killCursors`, `listCollections`, `listIndexes`, `listSearchIndexes`, `planCacheIndexFilter`, `planCacheRead`, `planCacheWrite`, `reIndex`, `remove`, `renameCollectionSameDB`, `setUserWriteBlockMode`, `storageDetails`, `unlock`, `update`, `updateSearchIndex`, `validate`, `viewRole`, `viewUser`.

Valid privileges for `resource_type: collection` (subset of the above):

`analyze`, `bypassDocumentValidation`, `changeStream`, `cleanupStructuredEncryptionData`, `collMod`, `collStats`, `compact`, `compactStructuredEncryptionData`, `convertToCapped`, `createCollection`, `createIndex`, `createSearchIndexes`, `dbCheck`, `dbHash`, `dbStats`, `dropCollection`, `dropIndex`, `dropSearchIndex`, `enableProfiler`, `exportCollection`, `find`, `importCollection`, `insert`, `killAnyCursor`, `killCursors`, `listCollections`, `listIndexes`, `listSearchIndexes`, `planCacheIndexFilter`, `planCacheRead`, `planCacheWrite`, `reIndex`, `remove`, `renameCollectionSameDB`, `storageDetails`, `update`, `updateSearchIndex`, `validate`.

## Required permissions on the auth principal

The root user creates dynamic users in the auth-source database. Choose one:

- **Built-in role (recommended):** `userAdminAnyDatabase` on the auth-source database.
- **Custom role** — actions:
  - User management (auth-source DB): `createUser`, `dropUser`, `viewUser`
  - Role management (auth-source DB): `createRole`, `dropRole`, `viewRole`
  - Role assignment (target DB): `grantRole`. For a privilege with `all_databases`, also `grantRole` on `admin`: MongoDB requires it to grant a privilege that spans databases, and `createRole` fails without it.

## Connection-string template

```
mongodb://${username}:${password}@${host}:${port}/${db_name}?authSource=${auth_source}
```
