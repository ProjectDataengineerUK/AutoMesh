# Snowflake Governance

## RBAC Hierarchy

```
ACCOUNTADMIN
  └── SYSADMIN
        ├── DATA_ENGINEER_ROLE    → CREATE, DDL em DEV/STAGING
        └── DATA_ANALYST_ROLE     → SELECT em GOLD apenas
  └── SECURITYADMIN
        ├── MASKING_ADMIN_ROLE    → CREATE MASKING POLICY
        └── COMPLIANCE_AUDITOR    → leitura em Account Usage
```

**Regra:** Nunca conceder acesso direto a usuários — sempre via roles hierárquicas.

## Masking Policies

```sql
-- CPF masking
CREATE OR REPLACE MASKING POLICY mask_cpf AS (val STRING)
  RETURNS STRING ->
    CASE
      WHEN CURRENT_ROLE() IN ('DATA_ENGINEER_ROLE', 'COMPLIANCE_AUDITOR') THEN val
      ELSE REGEXP_REPLACE(val, '\\d{3}\\.\\d{3}\\.\\d{3}-', '***.***.***-')
    END;

ALTER TABLE analytics.silver.customers
  MODIFY COLUMN cpf SET MASKING POLICY mask_cpf;

-- Email masking
CREATE OR REPLACE MASKING POLICY mask_email AS (val STRING)
  RETURNS STRING ->
    CASE
      WHEN CURRENT_ROLE() IN ('DATA_ENGINEER_ROLE', 'COMPLIANCE_AUDITOR') THEN val
      ELSE CONCAT(LEFT(SPLIT_PART(val, '@', 1), 2), '****@', SPLIT_PART(val, '@', 2))
    END;
```

## Row Access Policies (RLS)

```sql
-- Usuários veem apenas dados da própria região
CREATE OR REPLACE ROW ACCESS POLICY region_policy AS (region_code STRING)
  RETURNS BOOLEAN ->
    CURRENT_ROLE() IN ('DATA_ENGINEER_ROLE', 'COMPLIANCE_AUDITOR')
    OR EXISTS (
      SELECT 1 FROM analytics.security.user_region_mapping
      WHERE username = CURRENT_USER()
        AND authorized_region = region_code
    );

ALTER TABLE analytics.gold.fact_sales
  ADD ROW ACCESS POLICY region_policy ON (region_code);
```

## Object Tagging

```sql
CREATE OR REPLACE TAG pii_tag ALLOWED_VALUES 'CPF', 'EMAIL', 'PHONE', 'ADDRESS', 'NAME';
CREATE OR REPLACE TAG data_sensitivity ALLOWED_VALUES 'PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED';

-- Taggear coluna PII
ALTER TABLE analytics.silver.customers MODIFY COLUMN cpf SET TAG pii_tag = 'CPF';
ALTER TABLE analytics.silver.customers SET TAG data_sensitivity = 'CONFIDENTIAL';

-- Descobrir todas as colunas PII
SELECT table_name, column_name, tag_value
FROM TABLE(INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS('analytics.silver.customers', 'table'));
```

## Auditoria

```sql
-- Acessos a tabelas sensíveis (últimos 7 dias)
SELECT query_start_time, user_name, role_name, query_text, rows_produced
FROM snowflake.account_usage.query_history
WHERE query_start_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP)
  AND CONTAINS(LOWER(query_text), 'silver.customers')
  AND query_type = 'SELECT'
ORDER BY query_start_time DESC;

-- Logins falhados
SELECT user_name, event_type, error_message, event_timestamp
FROM snowflake.account_usage.login_history
WHERE is_success = 'NO'
  AND event_timestamp >= DATEADD(HOUR, -24, CURRENT_TIMESTAMP)
ORDER BY event_timestamp DESC;
```

## Trust Center

```sql
SELECT * FROM SNOWFLAKE.TRUST_CENTER.SECURITY_POSTURE_OVERVIEW;

SELECT finding_type, severity, description, recommendation
FROM SNOWFLAKE.TRUST_CENTER.SECURITY_FINDINGS
WHERE severity IN ('CRITICAL', 'HIGH');
```

## Guardrails

- Sempre incluir rollback DDL ao lado do apply DDL
- Testar masking com usuário de teste antes de aplicar em produção
- Row Access Policies com subquery → verificar impacto em tabelas grandes
- Ao remover uma policy: verificar quais tabelas a referenciam primeiro
