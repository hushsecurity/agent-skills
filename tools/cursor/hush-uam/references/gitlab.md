# gitlab

GitLab credentials and privileges. Dynamic credentials — provisions ephemeral group/project access tokens.

## Credential

```yaml
config:
  base_url: https://gitlab.com    # default
  resource_type: group            # or "project"
  resource_id: <group-or-project-id>
secretRef:
  name: <k8s-secret>
  # canonical key: token
```

`secretRef` keys: `token`.

## Privilege

```yaml
config:
  scopes: [read_api, read_repository]   # min 1
  access_level: Reporter                 # one of: Guest, Reporter, Developer, Maintainer, Owner
```

Valid scopes: `api`, `read_api`, `read_repository`, `write_repository`, `read_registry`, `write_registry`, `read_virtual_registry`, `write_virtual_registry`, `create_runner`, `manage_runner`, `ai_features`, `k8s_proxy`, `self_rotate`.

## Required permissions on the auth principal

The configured token must have at least **Reporter** access level on the target group/project, with these scopes:
- `read_api`
- `read_repository`
