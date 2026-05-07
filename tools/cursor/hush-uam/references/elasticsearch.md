# elasticsearch

Elasticsearch credentials and privileges. Dynamic credentials — provisions ephemeral users or API keys.

## Credential

```yaml
config:
  host: <hostname>
  port: 9200                  # default
  username: <root-username>   # optional (basic auth)
  tls: false                  # default
  tls_ca: <optional-pem>
secretRef:
  name: <k8s-secret>
  # canonical keys (exactly one of):
  #   username + password    (basic auth)
  #   api_key                (API key auth)
```

`secretRef` keys: exactly one of (`username` + `password`) OR `api_key`.

## Privilege

```yaml
config:
  grant:                                # singular — one grant object
    cluster: [monitor]                  # optional; or ["all"]
    indices:                            # optional
      - names: ["my-index-*"]
        privileges: [read, write]       # or ["all"]
```

At least one of `cluster` or `indices` must be set.

Valid cluster privileges:

`all`, `cancel_task`, `create_snapshot`, `cross_cluster_replication`, `cross_cluster_search`, `delegate_pki`, `grant_api_key`, `manage`, `manage_api_key`, `manage_autoscaling`, `manage_behavioral_analytics`, `manage_ccr`, `manage_data_frame_transforms`, `manage_data_stream_global_retention`, `manage_enrich`, `manage_ilm`, `manage_index_templates`, `manage_inference`, `manage_ingest_pipelines`, `manage_logstash_pipelines`, `manage_ml`, `manage_oidc`, `manage_own_api_key`, `manage_pipeline`, `manage_rollup`, `manage_saml`, `manage_search_application`, `manage_search_query_rules`, `manage_search_synonyms`, `manage_security`, `manage_service_account`, `manage_slm`, `manage_token`, `manage_transform`, `manage_user_profile`, `manage_watcher`, `monitor`, `monitor_data_frame_transforms`, `monitor_data_stream_global_retention`, `monitor_enrich`, `monitor_inference`, `monitor_ml`, `monitor_rollup`, `monitor_snapshot`, `monitor_text_structure`, `monitor_transform`, `monitor_watcher`, `none`, `post_behavioral_analytics_event`, `read_ccr`, `read_connector_secrets`, `read_fleet_secrets`, `read_ilm`, `read_pipeline`, `read_security`, `read_slm`, `transport_client`, `write_connector_secrets`, `write_fleet_secrets`.

Valid index privileges:

`all`, `auto_configure`, `create`, `create_doc`, `create_index`, `cross_cluster_replication`, `cross_cluster_replication_internal`, `delete`, `delete_index`, `index`, `maintenance`, `manage`, `manage_data_stream_lifecycle`, `manage_follow_index`, `manage_ilm`, `manage_leader_index`, `monitor`, `none`, `read`, `read_cross_cluster`, `view_index_metadata`, `write`.

## Required permissions on the auth principal

The configured root credentials must have the cluster privilege:
- `manage_security` — required to create, update, and delete users, roles, and API keys.

## Connection-string template

```
http://${username}:${password}@${host}:${port}
```
