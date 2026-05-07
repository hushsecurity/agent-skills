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
secretRef:
  name: <k8s-secret>
  # canonical key: password
```

`secretRef` keys: `password`.

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
