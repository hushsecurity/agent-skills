# azure_app

Azure Application (App Registration) credentials and privileges. Dynamic credentials — provisions ephemeral client secrets.

## Credential

```yaml
config:
  tenant_id: <uuid>
  client_id: <azure-client-id>     # optional; pair with client_secret
secretRef:                         # only if client_id is set
  name: <k8s-secret>
  # canonical key: client_secret
```

`secretRef` keys: `client_secret` (paired with `client_id`; both must be set or both omitted).

## Privilege

```yaml
config:
  # exactly one of:
  app_id: <uuid>
  # OR
  app_config:
    display_name: my-app
    roles:                              # optional
      - name: Reader
        scope: /subscriptions/<sub>/resourceGroups/<rg>
    graph_api_permissions: [User.Read]  # optional
```

## Required permissions on the auth principal

The configured Service Principal (App Registration) must be granted the following Microsoft Graph **Application** permissions on the Azure AD tenant:
- `Application.ReadWrite.All` — create, update, and delete app registrations
- `Application.ReadWrite.OwnedBy` — manage owned app registrations
- `AppRoleAssignment.ReadWrite.All` — manage app role assignments

These permissions require **Admin Consent** from a Global Administrator or Privileged Role Administrator.
