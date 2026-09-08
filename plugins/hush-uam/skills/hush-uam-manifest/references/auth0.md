# auth0

Auth0 credentials and privileges. Dynamic credentials — rotates a Private Key JWT keypair in place on an Auth0 application the customer already owns, delivering a fresh private key each version while the application's `client_id` stays the same.

## Credential

```yaml
config:
  domain: <tenant>.<region>.auth0.com  # canonical tenant domain, must end in .auth0.com
  custom_domain: auth.example.com      # optional
  client_id: <management-app-client-id>
secretRef:
  name: <k8s-secret>
  # canonical key: client_secret
```

`secretRef` keys: `client_secret`.

`config.domain` **must be the tenant's canonical Auth0 domain**, ending in `.auth0.com` — the one shown under Settings > General in the Auth0 dashboard. A custom domain is rejected. The Management API audience is the identifier of a registered resource server, fixed at tenant creation as `https://{canonical}/api/v2/`, and it does not move when a custom domain is added; deriving it from a custom domain makes every apply fail with `403 access_denied`.

`config.custom_domain` is optional. When set, the Management API and token requests are routed through that host and it is the domain delivered to the workload, while the audience is still derived from `config.domain`. Set it when the tenant has a custom domain configured — for example when egress rules or a proxy allowlist only permit that host.

`client_id` and `client_secret` identify an Auth0 machine-to-machine **application** authorized for the Management API, not a personal or user credential. There is no long-lived API token alternative: Management API tokens expire within 24 hours, so Hush exchanges the application for one on every apply.

The workload receives `domain`, the **target application's** `client_id` and a `private_key` — never the management application's own credentials.

## Privilege

```yaml
config:
  application_id: <client-id-of-the-target-application>
```

That is the whole schema. `application_id` is the client ID of an Auth0 application the customer already owns, 1–256 characters. Hush rotates a Private Key JWT credential on it and never creates, deletes or reconfigures the application itself.

Hush also never touches the application's **client grants**. Its authorization is the customer's to manage in Auth0, which means a Hush manifest cannot state what the credential can reach — that answer lives in the tenant.

Three preconditions on the named application. All three are refused at apply time with a configuration error rather than failing silently:

- **It must already be configured for Private Key JWT authentication**, and switching it over is the customer's step, not Hush's — it stops every consumer still authenticating with the client secret, and only they know whether those have been cut over. No keypair is needed for it: Auth0 accepts Private Key JWT with an empty credential list, and Hush installs the first key. Over the Management API the switch needs `token_endpoint_auth_method` set to `null` in the same `PATCH` that sets `client_authentication_methods`, or Auth0 refuses it; the dashboard's Credentials tab does this for you.

  An application that arrives already carrying one key of the customer's own is also accepted: the first apply takes that slot over and deletes the key, which is logged. Exactly one — two customer keys leaves Hush no room and is refused.

- **Its credentials must not be used for anything else.** The two-credential limit counts the application's whole collection, not a bucket per usage, so a key registered for JWT-Secured Authorization Requests (JAR) or mTLS permanently holds one of the two and rotation can never overlap. Such an application is refused at the first apply rather than accepted and left unable to rotate later. An application doing JAR cannot be a Hush auth0 target.
- **It must not be granted the Auth0 Management API.** A workload holding a credential for such an application could administer the tenant.
- **It may back only one access policy.** Auth0 allows two credentials per application and a rotating policy needs both, so a second policy on the same application could never rotate.

The workload signs a client assertion instead of posting a secret, so it needs an Auth0 SDK or an OAuth client that supports `private_key_jwt`. A generic OAuth2 client or plain `curl` cannot do this:

```
POST https://{AUTH0_DOMAIN}/oauth/token
  grant_type=client_credentials
  &client_id={AUTH0_CLIENT_ID}
  &audience=https://api.example.com
  &client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer
  &client_assertion={RS256 JWT signed with AUTH0_PRIVATE_KEY,
                     iss=sub={AUTH0_CLIENT_ID}, aud=https://{AUTH0_DOMAIN}/}
```

The audience is not part of the credential. The calling application supplies whichever of its granted APIs it is calling.

## Required permissions on the auth principal

The machine-to-machine application configured above must be authorized for the **Auth0 Management API** (`https://{domain}/api/v2/`) with exactly these scopes:

- `read:clients`
- `read:client_grants`
- `create:client_credentials`
- `read:client_credentials`
- `update:client_credentials`
- `delete:client_credentials`

Grant them in the Auth0 dashboard: Applications > Applications > create a Machine-to-Machine application > authorize it for the Auth0 Management API > select the scopes. The dashboard creates the client grant; there is no separate step.

`update:client_credentials` is the one that looks unnecessary and is not: activating a new key is a `PATCH` of the application's `client_authentication_methods`, and that field is gated on this scope rather than on `update:clients`.

Deliberately **not** required: `create:clients` and `delete:clients` (Hush does not create or remove applications), the `client_grants` write scopes (it does not change authorization), and `read:client_keys` (nothing in the lifecycle reads a client secret). An under-scoped application fails with `403 insufficient_scope`, which is a permanent error, so grant exactly this set before the first apply.

## Rotation and capacity

An Auth0 application holds at most **two** credentials. A rotation needs both at once — the draining version and the new one — so the cap is reached by design during every rotation window and released once the old version's pods have drained and Hush has reclaimed it.

If a workload never restarts, the old version never drains, and the rotation window is skipped rather than failed. Once it has been blocked long enough the access policy says so in its own status; the credential keeps working throughout, it is simply not rotating.

`403` with `errorCode: too_many_entities` is Auth0's answer to at least three different conditions — the two-per-application limit, the tenant-wide **Application Credentials** entity limit, and a duplicate credential name on one application — so it is reported as a limit error rather than a permission failure, and the message does not claim which one it was.

That tenant-wide limit is the one that binds at scale, and it is the credential count, not the application count:

| | Application Credentials consumed |
|---|---|
| one policy at rest | 1 |
| one policy during its rotation window | 2 |

Auth0 documents 2,000 on Enterprise and publishes no figure for Free or Self-service; a Free tenant was observed to allow **2**, which is enough for exactly one Hush auth0 policy and nothing else in the tenant using application credentials.

Unlike a design that mints an application per version, this consumes no application quota at all: the tenant's application count is unchanged by onboarding a Hush credential.
