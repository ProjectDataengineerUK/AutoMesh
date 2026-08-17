# DEFINE: Fase 7 — Produtos Gold e BI no Databricks

> Produtos Gold governados em Delta e duas visões Lakeview — executiva e operacional — sobre métricas versionadas.

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | FASE7_GOLD_BI_DATABRICKS |
| **Date** | 2026-08-17 |
| **Author** | define-agent |
| **Status** | Ready for Design |
| **Clarity Score** | 14/15 |

---

## Problem Statement

Executivos e operadores não possuem uma visão consolidada e governada dos dados que já existem nas Fases 1–6. Os resultados estão distribuídos entre Silver, insights, FinOps, delivery e evidências de validação, dificultando decisões executivas e diagnóstico operacional.

---

## Target Users

| User | Role | Pain Point |
|---|---|---|
| Executivo/gestor | Consumidor de indicadores e decisões | Não vê tendências, oportunidades, risco e custo numa visão única |
| Operação de dados | Responsável por pipelines e qualidade | Não correlaciona freshness, contratos, DLQ, falhas, custos e maturidade |

---

## Goals

What success looks like (prioritized):

| Priority | Goal |
|---|---|
| **MUST** | Criar produtos Gold incrementais e reproduzíveis em Delta para os domínios priorizados |
| **MUST** | Versionar métricas com owner, granularidade, fonte, testes e definição semântica |
| **MUST** | Entregar uma visão executiva e uma visão operacional com dados testados |
| **MUST** | Preservar a fronteira local/externa: ausência de credenciais produz skip explícito e não falso sucesso |
| **SHOULD** | Integrar evidências CAP-01–CAP-10, observabilidade e FinOps nos produtos operacionais |
| **SHOULD** | Preparar publicação controlada em Databricks SQL/Lakeview |
| **COULD** | Adicionar uma camada semântica portátil para futura integração Fabric/Power BI |

---

## Success Criteria

Measurable outcomes:

- [ ] Pelo menos 4 produtos Gold são definidos e reproduzíveis para mercado/insights, lost sales/CRM, FinOps e saúde operacional.
- [ ] 100% das métricas publicadas possuem owner, granularidade, fonte, fórmula e teste versionados.
- [ ] Fixtures locais apresentam 0 chaves duplicadas, 0 chaves primárias nulas e 0 falhas de contrato nos produtos aprovados.
- [ ] A visão operacional exibe freshness, volume, qualidade, custo e maturidade de CAP-01–CAP-10 em até 15 minutos após a geração do relatório local.
- [ ] A visão executiva exibe pelo menos 8 indicadores: tendência de mercado, lost sales, anomalias, custo, qualidade, freshness, risco e decisões pendentes.
- [ ] 100% dos testes locais do novo domínio passam sem Databricks configurado.
- [ ] Smokes externos sem pré-requisitos resultam em `SKIP_WITH_REASON:MISSING_CREDENTIAL` ou `EXTERNAL_DISABLED`.
- [ ] Nenhum workflow de Build cria recursos pagos ou executa mutação externa sem flag e recurso allowlisted.

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|---|---|---|---|---|
| AT-001 | Gold market product | Silver/market fixtures válidos | Build incremental é executado duas vezes | Resultado é determinístico e sem duplicidade |
| AT-002 | Lost sales product | CRM/lost-sales fixtures e contrato válido | Gold build executa | Métricas de volume, valor e tendência têm schema e owner |
| AT-003 | FinOps product | Histórico e uso atual disponíveis | Agregação de custo executa | Custo por workload e anomalias aparecem com freshness |
| AT-004 | Operational health product | Evidência de validação e eventos observability existem | View operacional é gerada | CAP-01–CAP-10 e reason codes aparecem sem perda |
| AT-005 | Executive view | Produtos Gold aprovados | Consulta executiva executa | Pelo menos 8 indicadores com período e fonte são retornados |
| AT-006 | Quality failure | Fixture contém chave nula ou duplicada | Gate de qualidade executa | Build falha com razão explícita e não publica view aprovada |
| AT-007 | Incremental replay | Mesmo lote é entregue novamente | Build é repetido | No máximo um efeito lógico por chave permanece |
| AT-008 | Missing Databricks | Workspace/warehouse não configurado | Validador de publicação executa | Resultado é skip explícito, sem chamada de criação ou mutação |
| AT-009 | Lakeview publication | Workspace e recurso de teste allowlisted configurados e flag habilitada | Publicação é solicitada | Dashboard é criado/atualizado com evidência, owner e timestamp |
| AT-010 | Schema evolution | Coluna não compatível é adicionada ao Silver | Contrato Gold é validado | Mudança é bloqueada ou classificada antes de alterar o produto |
| AT-011 | Freshness breach | Fixture excede SLA do produto | Health query executa | Indicador fica `STALE` e gera reason code operacional |
| AT-012 | Access boundary | Coluna classificada como sensível existe | Metadata e view são validados | Classificação e regra de acesso são preservadas; valor não aparece em logs |

---

## Out of Scope

Explicitly NOT included in this feature:

- Snowflake ou dbt como engine de transformação do MVP.
- Microsoft Fabric, Power BI, DirectLake e Copilot.
- Novos modelos de ML, previsão ou perguntas em linguagem natural.
- Provisionamento Terraform completo de workspace, SQL warehouse, catálogo ou cluster.
- Atualização automática de recursos externos sem flag, credenciais e allowlist.
- Dashboards adicionais por departamento ou persona.

---

## Constraints

| Type | Constraint | Impact |
|---|---|---|
| Technical | Databricks SQL/Lakeview é o consumidor alvo; Delta/Unity Catalog são a fonte Gold | Design deve separar SQL/views externas de fixtures locais |
| Technical | Deve reutilizar contratos, evidências e observabilidade das Fases 1–6 | Novos produtos não podem duplicar definições de qualidade ou reason codes |
| Resource | Budget recorrente zero | Nenhuma execução cria recursos pagos por padrão |
| Security | Secrets não podem aparecer em inventário, logs, fixtures ou relatórios | Publicação e smokes usam apenas presença/configuração e referências seguras |
| Validation | Workspace e contas externas podem estar indisponíveis | Todo gate externo precisa de precondition e skip explícito |
| Compatibility | Execução local deve funcionar sem Databricks | Fixtures e queries locais devem validar schemas e métricas essenciais |

---

## Technical Context

| Aspect | Value | Notes |
|---|---|---|
| **Deployment Location** | `pipelines/gold/`, `pipelines/bi/`, `contracts/gold/`, `tests/gold/`, `tests/bi/` | Mantém separação por domínio e reutiliza padrões de pipeline existentes |
| **KB Domains** | `medallion`, `lakeflow`, `lakehouse`, `data-modeling`, `data-quality`, `cloud-platforms`, `testing`, `sql-patterns` | Design deve consultar Gold, Delta, incremental, star schema, quality gates e SQL cross-dialect |
| **IaC Impact** | Modify existing / external opt-in | Pode adicionar configuração e manifests; não provisiona recursos automaticamente |

**Why This Matters:**

- **Location** → evita colocar transformações Gold em jobs Silver ou dashboards em pipelines de ingestão.
- **KB Domains** → fornece padrões para incrementalidade, testes, linhagem, views e publicação Databricks.
- **IaC Impact** → mantém custo e permissões sob controle e torna a publicação externa auditável.

---

## Data Contract (if applicable)

### Source Inventory

| Source | Type | Volume | Freshness | Owner |
|---|---|---|---|---|
| Silver market/B3 | Delta/API/Kafka | Fixtures e volume da Fase 1 | Por execução/stream | ingestion |
| Silver CRM/lost sales | Delta/batch | Fixtures de CRM | Batch | ingestion |
| Insights | Delta/MLflow artifacts | Por run de treino/inferência | Por DAG | insights |
| FinOps | Databricks billing/fallback Airflow | Por janela de uso | Horário | finops |
| Validation evidence | JSON artifacts | Por run | Por validação | platform |
| Observability events | JSON/logs/metrics | Por evento | Contínua | platform |

### Schema Contract

| Column | Type | Constraints | PII? |
|---|---|---|---|
| `event_date` | DATE | NOT NULL | No |
| `domain` | STRING | NOT NULL, accepted domain enum | No |
| `metric_name` | STRING | NOT NULL | No |
| `metric_value` | DECIMAL | NOT NULL, finite | No |
| `source_ref` | STRING | NOT NULL, no secret value | No |
| `status` | STRING | accepted status enum | No |
| `correlation_id` | STRING | optional trace reference | No |
| `owner` | STRING | NOT NULL | No |

Sensitive source columns must be excluded or classified before entering an executive view. No credential value is a Gold field.

### Freshness SLAs

| Layer | Target | Measurement |
|---|---|---|
| Silver → Gold operational | ≤ 15 minutes after validation report generation | `gold_generated_at - evidence_generated_at` |
| Silver → Gold executive | ≤ 60 minutes in a configured workspace | `gold_generated_at - source_watermark` |
| Dashboard metadata | ≤ 15 minutes after Gold refresh | Lakeview refresh timestamp |

### Completeness Metrics

- 100% of approved fixture records represented or explicitly rejected with reason code.
- Zero null primary keys and zero duplicate business keys in approved Gold products.
- 100% of published metrics map to a versioned source and formula.

### Lineage Requirements

- Source-to-Gold lineage must identify domain, contract, transformation version and source watermark.
- Every dashboard metric must reference a Gold product and metric definition.
- Schema changes require contract validation before publication.

---

## Assumptions

Assumptions that if wrong could invalidate the design:

| ID | Assumption | If Wrong, Impact | Validated? |
|---|---|---|---|
| A-001 | Silver fixtures expose stable keys and timestamps | Gold incremental strategy needs a new cursor/key design | [ ] |
| A-002 | Databricks SQL supports the planned view and dashboard objects | External publication needs compatible SQL or a reduced MVP | [ ] |
| A-003 | At least one allowlisted workspace can be made available later | Lakeview remains local/spec-only | [ ] |
| A-004 | Existing CAP evidence and observability schemas remain stable | Operational product needs an adapter/version bridge | [x] Based on Fase 6 contracts |
| A-005 | Executive metrics can exclude sensitive columns | Additional masking/aggregation layer is required | [ ] |
| A-006 | Local fixtures are sufficient to verify metric formulas | Additional anonymized samples are needed | [x] Confirmed in brainstorm |
| A-007 | No recurring cloud budget is authorized | External validation remains opt-in and possibly pending | [x] Confirmed by prior phases |

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---|---:|---|
| Problem | 3 | Problema, impacto e personas são específicos |
| Users | 3 | Executivo e operação com dores distintas |
| Goals | 3 | Priorizados e ligados a produtos e views concretos |
| Success | 3 | Critérios com contagens, percentuais, SLAs e 12 acceptance tests |
| Scope | 2 | MVP está claro; detalhes de objetos Lakeview e recursos externos ficam para Design |
| **Total** | **14/15** | Alta clareza; pronto para Design |

**Minimum to proceed: 12/15**

---

## Open Questions

1. Quais quatro produtos Gold terão prioridade de implementação se o tempo do MVP for reduzido?
2. Qual workspace/schema/catalog de teste será usado quando a validação externa for autorizada?
3. Qual política de acesso deve ser aplicada às colunas classificadas como sensíveis?

Essas perguntas não bloqueiam o Design local; bloqueiam apenas a publicação externa final.

---

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-17 | define-agent | Requirements extracted from approved Fase 7 brainstorm |

---

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_FASE7_GOLD_BI_DATABRICKS.md`
