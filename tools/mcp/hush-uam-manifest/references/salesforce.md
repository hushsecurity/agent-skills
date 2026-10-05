# salesforce

Salesforce credentials and privileges. Dynamic credentials — provisions ephemeral managed External Client Applications (ECAs).

## Credential

```yaml
config:
  instance_url: https://<org>.my.salesforce.com   # https URL
  client_id: <root-eca-client-id>
secretRef:
  name: <k8s-secret>
  # canonical key: client_secret
```

`secretRef` keys: `client_secret`.

## Privilege

```yaml
config:
  run_as_user: user@example.com
  scopes: [Api, RefreshToken]           # min 1
```

Valid scopes: `Api`, `Web`, `Full`, `RefreshToken`, `OpenID`, `Profile`, `Email`, `Address`, `Phone`, `OfflineAccess`, `CustomPermissions`, `Lightning`, `Content`, `Chatter`, `Wave`, `Eclair`, `Pardot`, `CDPIngest`, `CDPProfile`, `CDPQuery`, `Chatbot`, `CDPSegment`, `CDPIdentityResolution`, `CDPCalculatedInsight`, `SFApiPlatform`, `Interaction`, `CDP`, `EinsteinGPT`, `PwdlessLogin`, `ForgotPassword`, `UserRegistration`, `MCP`, `SCRT`.

## Required permissions on the auth principal

The configured root credentials are used to create, rotate, and revoke managed External Client Applications (ECAs) via the OAuth 2.0 Client Credentials Flow. The customer must create a dedicated **root ECA** with:

- **OAuth enabled** with **Client Credentials Flow** enabled
- **Run-As User** configured
- **API Enabled** — required for API access
- **Modify Metadata Through Metadata API Functions** (or **Modify All Data**) — required to deploy `ExternalClientApplication`, `ExtlClntAppOauthSettings`, `ExtlClntAppOauthConfigurablePolicies`, and `ExtlClntAppGlobalOauthSettings` metadata
- **Customize Application** / **Manage Connected Apps** — required to manage ECAs and read their consumer key/secret
- **OAuth scopes** — sufficient to grant the scopes the managed ECAs will request (e.g. `Api`, `RefreshToken`, `OfflineAccess`)
