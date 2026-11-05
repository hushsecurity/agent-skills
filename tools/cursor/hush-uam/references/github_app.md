# github_app

GitHub App credentials and privileges. Dynamic credentials — Hush mints short-lived
(about one hour) GitHub App installation tokens, narrowed to the privilege's repositories
and permissions, and keeps a fresh one in the pod. github.com only: GitHub Enterprise
Server is not supported.

## Credential

```yaml
config:
  client_id: Iv23liAbCdEfGhIjKlMn   # the App's client ID, or its numeric App ID
  installation_id: "176836371"      # a string -- quote it
secretRef:
  name: <k8s-secret>
  # canonical key: private_key
```

`secretRef` keys: `private_key`.

- `client_id`: 1-64 letters, digits and dots. Take it from the App's settings page
  (`Iv23...`, or `Iv1.<hex>` for an older App). The App's numeric App ID, on the same
  page, works too.
- `installation_id`: digits only, no leading zero, and it **must be a string**. An
  unquoted YAML number is sent as a JSON number and rejected. It is the number at the end of the installation's
  URL: `https://github.com/organizations/<org>/settings/installations/<id>` for an
  organization, `https://github.com/settings/installations/<id>` for a personal account.
- `private_key`: the unencrypted RSA private key in PEM, as downloaded from the App's
  settings (PKCS#1 `BEGIN RSA PRIVATE KEY` or PKCS#8 `BEGIN PRIVATE KEY`). An encrypted or
  non-RSA key is rejected. Create the Secret from the file so the newlines survive:
  `kubectl create secret generic <k8s-secret> --from-file=private_key=<app>.private-key.pem`.

## Privilege

```yaml
config:
  repositories: [api, web]   # optional; omit or [] for every repository of the installation
  permissions:               # required, min 1
    contents: read
    pull_requests: write
```

- `repositories`: bare repository names, **without the owner** (`api`, not `acme/api`).
  Unique, at most 500, each 1-100 characters of `[A-Za-z0-9._-]`, and not `.` or `..`. Empty or omitted means
  every repository the installation can reach -- ask before leaving it empty.
- `permissions`: a map of GitHub App permission name to level. Names are GitHub's REST
  names (`pull_requests`, not "Pull requests"); an unknown name is rejected. Levels:

| Levels accepted | Permissions |
| --- | --- |
| `read` only | `organization_copilot_requests`, `organization_events`, `organization_plan` |
| `write` only | `profile`, `workflows` |
| `read`, `write`, `admin` | `enterprise_custom_properties_for_organizations`, `organization_custom_properties`, `organization_external_properties_for_repos`, `organization_projects`, `repository_projects` |
| `read`, `write` | every other name: `actions`, `administration`, `artifact_metadata`, `attestations`, `checks`, `code_quality`, `codespaces`, `contents`, `custom_properties_for_organizations`, `dependabot_secrets`, `deployments`, `discussions`, `email_addresses`, `environments`, `followers`, `git_ssh_keys`, `gpg_keys`, `interaction_limits`, `issues`, `members`, `merge_queues`, `metadata`, `organization_administration`, `organization_announcement_banners`, `organization_copilot_agent_settings`, `organization_copilot_seat_management`, `organization_custom_org_roles`, `organization_custom_roles`, `organization_hooks`, `organization_packages`, `organization_personal_access_token_requests`, `organization_personal_access_tokens`, `organization_secrets`, `organization_self_hosted_runners`, `organization_user_blocking`, `packages`, `pages`, `pull_requests`, `repository_custom_properties`, `repository_hooks`, `secret_scanning_alerts`, `secrets`, `security_events`, `single_file`, `starring`, `statuses`, `vulnerability_alerts` |

Common shapes: clone/pull -- `contents: read`; push -- `contents: write`; open PRs --
`contents: write` + `pull_requests: write`; edit workflow files -- add `workflows: write`.

## Delivery

`github_app` is the **only** delivery this credential accepts, and no other credential
type accepts it. It has no items: the token is not a credential field an `env`, `volume`
or `sdk` mapping could name.

```yaml
deliveryConfig:
  type: github_app
  config:
    git_credential_helper: true   # default; config: {} is the same
```

Constraint (enforced by the API on both targets): `k8s:container-name` attestation is
**not** allowed -- the token is delivered to the whole pod.

A pod gets one token. The API accepts several `github_app` policies matching the same pod;
the one with the higher `priority` is delivered, and a tie at the top is reported as a
conflict when the pod starts. See *Overlapping policies* in `SKILL.md`.

What the workload gets, in every container: the token in
`/var/run/secrets/hush.security/federation/github/token` (refreshed by a sidecar, so read
the file on each use rather than caching it), `HUSH_GITHUB_TOKEN_FILE` pointing at it, and
`GH_CONFIG_DIR` with a `gh` config logged in to github.com, so the `gh` CLI works as is.
With `git_credential_helper: true`, `GIT_CONFIG_*` variables make git use the token for
`https://github.com` -- this needs git 2.31 or later, plus `/bin/sh` and `cat` in the
image. It replaces any credential helper the image configured for github.com. Set it to
`false` when the workload configures git itself.

The git helper is skipped for a container that has any `envFrom` source, or that sets
`GIT_CONFIG_COUNT` from a `valueFrom` reference or to a value that is not a number. The
only sign is a warning in the access manager's log: `git clone` runs unauthenticated
while the token file, `HUSH_GITHUB_TOKEN_FILE` and the `gh` login are still delivered.
`envFrom` from a ConfigMap or Secret is common, so check for it. Either set those
variables with `env` instead of `envFrom`, or set `git_credential_helper: false` and
configure git from `HUSH_GITHUB_TOKEN_FILE`.

Hush does not set `GH_TOKEN` or `GITHUB_TOKEN`. A container that sets either one itself
overrides the token for `gh`, so remove it from the workload. Point other tools that want
a token at `HUSH_GITHUB_TOKEN_FILE`.

## Required permissions on the auth principal

The auth principal is the GitHub App itself:

- The App must be **installed** on the account or organization, and `installation_id`
  must be that installation.
- Every permission in a privilege must be granted to the App at that level or higher. A
  privilege can only narrow what the installation already has; asking for more fails
  when the token is minted ("not granted"), not when the privilege is created.
- Every repository listed must be in the installation's repository selection.
- The Hush access manager's pods mint the tokens, so they must reach
  `https://api.github.com`, and their clocks must be in sync, since the App signs a
  short-lived JWT. The workload pods need no GitHub API access of their own beyond what
  they use the token for.

Deleting a credential, privilege or policy does not revoke tokens already minted; they
stay valid until they expire, within an hour.

Suspending the installation stops every token at once. A policy created, changed or
rotated while it is suspended fails with a permission error ("This installation has been
suspended") and stays failed after the installation is unsuspended: rotate it with
`POST /v1/access_policies/{id}/rotate` to apply it again. That works for a policy managed
from Kubernetes or Terraform too, since it leaves the spec alone. Policies applied before
the suspension, and their pods, recover on their own.

## Terraform

`hush_github_app_access_credential` takes `client_id`, `installation_id` (a string) and
`private_key` / `private_key_wo` + `private_key_wo_version`. Use `file("app.pem")` or a
secret source for the key, never an inline heredoc in the repo.

`hush_github_app_access_privilege` takes `repositories` (a list of bare names) and
`permissions` (a map):

```hcl
resource "hush_github_app_access_privilege" "ci" {
  name         = "ci-repo-read"
  repositories = ["api", "web"]
  permissions = {
    contents      = "read"
    pull_requests = "write"
  }
}
```

`hush_access_policy` takes a `github_app_delivery_config` block:

```hcl
github_app_delivery_config {
  git_credential_helper = true # default
}
```

At plan time the provider checks the repository names, that `repositories` has no
duplicates, that `permissions` is non-empty, that each name looks like a permission name
and that each level is `read`, `write` or `admin`. It does not check whether a name is a
GitHub App permission, which levels that permission accepts (`workflows: read` passes the
plan), or the `k8s:container-name` rule; the API rejects those at apply. Apply them when
authoring.

These resources and the block are not in provider 1.38.0 or older; they need a later
release.
