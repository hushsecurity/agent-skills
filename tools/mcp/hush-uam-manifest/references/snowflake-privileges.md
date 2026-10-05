# Snowflake Privileges by Resource Type

Complete privilege map for an `AccessPrivilege` of type `snowflake`. Use one of the privilege names below in `grants[].privileges[]`, paired with the matching `resource_type`. Use `["ALL"]` to grant every privilege valid for the resource type (cannot be mixed with specific privileges).

`resource_names` is **forbidden** when `resource_type` is `database` or `schema`. For schema-scoped object types (e.g. `table`, `view`, `function`), omitting `resource_names` grants on all current and future objects of that type in the schema.

## database

- `APPLYBUDGET`
- `CREATE DATABASE ROLE`
- `CREATE SCHEMA`
- `IMPORTED PRIVILEGES`
- `MODIFY`
- `MONITOR`
- `REFERENCE_USAGE`
- `USAGE`

## schema

- `ADD SEARCH OPTIMIZATION`
- `APPLYBUDGET`
- `CREATE ALERT`
- `CREATE CORTEX SEARCH SERVICE`
- `CREATE DYNAMIC TABLE`
- `CREATE EVENT TABLE`
- `CREATE EXTERNAL TABLE`
- `CREATE FILE FORMAT`
- `CREATE FUNCTION`
- `CREATE GIT REPOSITORY`
- `CREATE ICEBERG TABLE`
- `CREATE IMAGE REPOSITORY`
- `CREATE MASKING POLICY`
- `CREATE MATERIALIZED VIEW`
- `CREATE MODEL`
- `CREATE NETWORK RULE`
- `CREATE NOTEBOOK`
- `CREATE PACKAGES POLICY`
- `CREATE PASSWORD POLICY`
- `CREATE PIPE`
- `CREATE PROCEDURE`
- `CREATE ROW ACCESS POLICY`
- `CREATE SECRET`
- `CREATE SEQUENCE`
- `CREATE SERVICE`
- `CREATE SESSION POLICY`
- `CREATE STAGE`
- `CREATE STREAM`
- `CREATE STREAMLIT`
- `CREATE TABLE`
- `CREATE TAG`
- `CREATE TASK`
- `CREATE VIEW`
- `MODIFY`
- `MONITOR`
- `USAGE`

## table

- `APPLYBUDGET`
- `DELETE`
- `EVOLVE SCHEMA`
- `INSERT`
- `REFERENCES`
- `SELECT`
- `TRUNCATE`
- `UPDATE`

## view

- `REFERENCES`
- `SELECT`

## warehouse

- `APPLYBUDGET`
- `MODIFY`
- `MONITOR`
- `OPERATE`
- `USAGE`

## dynamic_table

- `MONITOR`
- `OPERATE`
- `SELECT`

## external_table

- `REFERENCES`
- `SELECT`

## file_format

- `USAGE`

## function

- `USAGE`

## materialized_view

- `APPLYBUDGET`
- `REFERENCES`
- `SELECT`

## pipe

- `APPLYBUDGET`
- `MONITOR`
- `OPERATE`

## procedure

- `USAGE`

## sequence

- `USAGE`

## stage

- `READ`
- `USAGE`
- `WRITE`

## stream

- `SELECT`

## task

- `APPLYBUDGET`
- `MONITOR`
- `OPERATE`
