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
```

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
  - Role assignment (target DB): `grantRole`

## Connection-string template

```
mongodb://${username}:${password}@${host}:${port}/${db_name}?authSource=${auth_source}
```
