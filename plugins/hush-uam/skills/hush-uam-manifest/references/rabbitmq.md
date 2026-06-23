# rabbitmq

RabbitMQ credentials and privileges. Dynamic credentials — provisions ephemeral users via the Management API.

## Credential

```yaml
config:
  host: <hostname>
  port: 5672                  # default
  management_port: 15672      # default
  username: <root-username>   # optional
  vhost: "/"                  # default
  tls: false                  # default
  tls_ca: <optional-pem>
  auto_rotate_root: false     # default; opt-in periodic rotation of the root credential
secretRef:
  name: <k8s-secret>
  # canonical key: password
```

`secretRef` keys: `password`.

### `auto_rotate_root`

When `true`, Hush periodically rotates the **root/admin credential itself** (the `password` in `secretRef`), not just the ephemeral per-workload users. RabbitMQ is currently the only credential type that supports root rotation; the rotation interval is 30 days. Defaults to `false` — leave it off unless the user explicitly wants Hush to manage the root password lifecycle.

For rotation to work the configured root user must be able to change its own password, which the required `administrator` tag (below) already covers. The field can be flipped on or off later via a credential update.

## Privilege

```yaml
config:
  permissions:                          # min 1
    - vhost: "/"
      configure: ".*"                   # regex; default ""
      write: ".*"
      read: ".*"
  tags: [administrator]                 # optional
```

Valid tags: `administrator`, `monitoring`, `policymaker`, `management`, `impersonator`.

## Required permissions on the auth principal

- The **RabbitMQ Management Plugin** must be installed and enabled on the server.
- The configured user must have the **`administrator` tag** for full management access.

## Connection-string template

```
amqp://${username}:${password}@${host}:${port}/${vhost}
```
