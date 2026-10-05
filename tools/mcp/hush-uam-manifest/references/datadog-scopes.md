# Datadog Privilege Scopes

Complete list of valid `scopes[]` values for an `AccessPrivilege` of type `datadog`. Only applicable when `key_type` is `application_key` or `both`.

## API and Application Keys

- `user_app_keys`
- `org_app_keys_read`
- `org_app_keys_write`
- `api_keys_read`
- `api_keys_write`
- `client_tokens_read`
- `client_tokens_write`
- `api_keys_delete`

## APM

- `apm_read`
- `apm_retention_filter_read`
- `apm_retention_filter_write`
- `apm_service_ingest_read`
- `apm_service_ingest_write`
- `apm_apdex_manage_write`
- `apm_tag_management_write`
- `apm_primary_operation_write`
- `debugger_write`
- `debugger_read`
- `apm_generate_metrics`
- `apm_pipelines_write`
- `apm_pipelines_read`
- `apm_service_catalog_write`
- `apm_service_catalog_read`
- `apm_remote_configuration_write`
- `apm_remote_configuration_read`
- `continuous_profiler_read`
- `debugger_capture_variables`
- `apm_api_catalog_write`
- `apm_api_catalog_read`
- `continuous_profiler_pgo_read`
- `debugger_write_pre_prod`
- `apm_service_renaming_write`

## Access Management

- `user_access_invite`
- `user_access_manage`
- `service_account_write`
- `org_management`
- `org_connections_write`
- `org_connections_read`
- `governance_console_read`
- `governance_console_write`
- `org_group_read`
- `org_group_write`

## App Builder & Workflow Automation

- `workflows_read`
- `workflows_write`
- `workflows_run`
- `connections_read`
- `connections_write`
- `connections_resolve`
- `apps_run`
- `apps_write`
- `on_prem_runner_read`
- `on_prem_runner_use`
- `on_prem_runner_write`
- `apps_datastore_read`
- `apps_datastore_write`
- `apps_datastore_manage`
- `connection_groups_write`
- `connection_groups_read`
- `actions_interface_run`
- `apps_form_read`
- `apps_form_manage`
- `agent_builder_read`
- `agent_builder_write`
- `agent_builder_run`

## Application Security

- `ai_guard_evaluate`

## Assistant

- `assistant_access`

## Billing and Usage

- `billing_read`
- `billing_edit`
- `usage_read`
- `usage_edit`
- `usage_notifications_read`
- `usage_notifications_write`

## Bits AI

- `bits_investigations_read`
- `bits_investigations_write`

## Case and Incident Management

- `incident_read`
- `incident_write`
- `incident_settings_read`
- `incident_settings_write`
- `incidents_private_global_access`
- `cases_read`
- `cases_write`
- `incident_notification_settings_read`
- `incident_notification_settings_write`
- `cases_shared_settings_write`

## Cloud Cost Management

- `cloud_cost_management_read`
- `cloud_cost_management_write`
- `generate_ccm_report_schedules`
- `manage_ccm_report_schedules`

## Cloud Network Monitoring

- `network_connections_read`
- `network_health_insights_read`

## Cloud Security Platform

- `security_monitoring_rules_read`
- `security_monitoring_rules_write`
- `security_monitoring_signals_read`
- `security_monitoring_signals_write`
- `security_monitoring_filters_read`
- `security_monitoring_filters_write`
- `appsec_event_rule_read`
- `appsec_event_rule_write`
- `security_monitoring_notification_profiles_read`
- `security_monitoring_notification_profiles_write`
- `security_monitoring_cws_agent_rules_read`
- `security_monitoring_cws_agent_rules_write`
- `appsec_protect_read`
- `appsec_protect_write`
- `appsec_activation_read`
- `appsec_activation_write`
- `security_monitoring_findings_read`
- `security_monitoring_findings_write`
- `appsec_vm_write`
- `security_monitoring_suppressions_read`
- `security_monitoring_suppressions_write`
- `appsec_vm_read`
- `security_pipelines_read`
- `security_pipelines_write`
- `security_monitoring_cws_agent_rules_actions`
- `security_comments_write`
- `security_comments_read`
- `security_monitoring_datasets_read`
- `security_monitoring_datasets_write`
- `bits_security_analyst_write`
- `bits_security_analyst_config_write`

## CoTerm

- `coterm_write`
- `coterm_read`

## Compliance

- `audit_logs_read`
- `audit_logs_write`
- `data_scanner_read`
- `data_scanner_write`
- `data_scanner_unmask`

## Containers

- `containers_generate_image_metrics`

## Cross-Product Features

- `saved_views_write`
- `facets_write`
- `generate_log_reports`
- `manage_log_reports`

## DDSQL Editor

- `ddsql_editor_read`

## Dashboards

- `dashboards_read`
- `dashboards_write`
- `dashboards_public_share`
- `generate_dashboard_reports`
- `dashboards_invite_share`
- `dashboards_embed_share`
- `embeddable_graphs_share`

## Data Streams Monitoring

- `data_streams_monitoring_capture_messages`
- `data_streams_kafka_produce_message`

## Database Monitoring

- `dbm_read`
- `dbm_parameterized_queries_read`

## Disaster Recovery

- `disaster_recovery_status_read`
- `disaster_recovery_status_write`

## Error Tracking

- `error_tracking_write`
- `error_tracking_settings_write`
- `error_tracking_exclusion_filters_write`
- `error_tracking_read`

## Events

- `event_correlation_config_read`
- `event_correlation_config_write`
- `event_config_write`

## Feature Flags

- `feature_flag_config_write`
- `feature_flag_config_read`
- `feature_flag_environment_config_write`
- `feature_flag_environment_config_read`

## Fleet Automation

- `agent_flare_collection`
- `agent_upgrade_write`
- `fleet_policies_write`

## Infrastructure

- `cloudcraft_read`
- `infrastructure_resource_policies_read`
- `infrastructure_resource_policies_write`

## Integrations

- `aws_configurations_manage`
- `azure_configurations_manage`
- `gcp_configurations_manage`
- `manage_integrations`
- `integrations_read`
- `oci_configurations_manage`
- `aws_configuration_read`
- `azure_configuration_read`
- `gcp_configuration_read`
- `oci_configuration_read`
- `aws_configuration_edit`
- `azure_configuration_edit`
- `gcp_configuration_edit`
- `oci_configuration_edit`

## LLM Observability

- `llm_observability_read`
- `llm_observability_write`

## Log Management

- `logs_modify_indexes`
- `logs_write_exclusion_filters`
- `logs_write_pipelines`
- `logs_write_processors`
- `logs_write_archives`
- `logs_generate_metrics`
- `logs_read_data`
- `logs_read_archives`
- `logs_write_historical_view`
- `logs_write_facets`
- `logs_delete_data`
- `logs_write_forwarding_rules`
- `flex_logs_config_write`
- `logs_read_workspaces`
- `logs_write_workspaces`
- `logs_read_config`
- `logs_live_tail`
- `logs_read_index_data`

## MCP

- `mcp_write`
- `mcp_read`

## Metrics

- `metric_tags_write`
- `host_tags_write`
- `metrics_metadata_write`

## Monitors

- `monitors_read`
- `monitors_write`
- `monitors_downtime`
- `monitor_config_policy_write`

## Network Device Monitoring

- `ndm_netflow_port_mappings_write`
- `ndm_device_profiles_view`
- `ndm_device_profiles_edit`
- `ndm_devices_read`
- `ndm_device_tags_write`
- `ndm_geomap_locations_write`
- `ndm_device_config_read`

## Notebooks

- `notebooks_read`
- `notebooks_write`

## Observability Pipelines

- `observability_pipelines_read`
- `observability_pipelines_write`
- `observability_pipelines_delete`
- `observability_pipelines_deploy`
- `observability_pipelines_capture_read`
- `observability_pipelines_capture_write`

## On-Call

- `on_call_read`
- `on_call_write`
- `on_call_page`
- `on_call_respond`
- `on_call_admin`

## Orchestration

- `orchestration_custom_resource_definitions_write`
- `orchestration_workload_scaling_write`
- `orchestration_autoscaling_manage`

## Processes

- `processes_generate_metrics`
- `process_tags_read`
- `process_tags_write`

## Product Analytics

- `audience_management_read`
- `audience_management_write`
- `product_analytics_apps_write`
- `product_analytics_saved_widgets_read`
- `product_analytics_saved_widgets_write`
- `product_analytics_settings_read`
- `product_analytics_settings_write`
- `product_analytics_experiments_read`
- `product_analytics_experiments_write`
- `product_analytics_metrics_read`
- `product_analytics_metrics_write`
- `product_analytics_certified_metrics_write`
- `product_analytics_warehouse_model_write`

## Real User Monitoring

- `rum_apps_write`
- `rum_apps_read`
- `rum_session_replay_read`
- `rum_generate_metrics`
- `rum_delete_data`
- `rum_playlist_write`
- `rum_extend_retention`
- `rum_retention_filters_read`
- `rum_retention_filters_write`
- `rum_settings_write`

## Reference Tables

- `reference_tables_write`
- `reference_tables_read`

## Serverless

- `serverless_aws_instrumentation_read`
- `serverless_aws_instrumentation_write`

## Service Level Objectives

- `slos_read`
- `slos_write`
- `slos_corrections`

## Sheets

- `sheets_read`
- `sheets_write`

## Software Delivery

- `ci_visibility_read`
- `ci_visibility_write`
- `ci_provider_settings_write`
- `ci_visibility_settings_write`
- `ci_ingestion_control_write`
- `ci_visibility_pipelines_write`
- `quality_gate_rules_read`
- `quality_gate_rules_write`
- `static_analysis_settings_write`
- `cd_visibility_read`
- `dora_settings_write`
- `code_analysis_read`
- `quality_gates_evaluations_read`
- `test_optimization_read`
- `test_optimization_write`
- `test_optimization_settings_write`
- `dora_metrics_read`
- `code_coverage_read`
- `dora_metrics_write`

## Status Pages

- `status_pages_settings_read`
- `status_pages_settings_write`
- `status_pages_incident_write`

## Synthetic Monitoring

- `synthetics_private_location_read`
- `synthetics_private_location_write`
- `synthetics_global_variable_read`
- `synthetics_global_variable_write`
- `synthetics_read`
- `synthetics_write`
- `synthetics_default_settings_read`
- `synthetics_default_settings_write`

## Teams

- `teams_manage`

## Watchdog

- `watchdog_alerts_write`
- `external_provider_status_notifications_read`
- `external_provider_status_notifications_write`
