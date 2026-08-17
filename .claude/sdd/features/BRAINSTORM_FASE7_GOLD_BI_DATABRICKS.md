# BRAINSTORM: Fase 7 — Produtos Gold e BI no Databricks

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | FASE7_GOLD_BI_DATABRICKS |
| **Date** | 2026-08-17 |
| **Author** | brainstorm-agent |
| **Status** | ✅ Complete (Defined) |

---

## Initial Idea

**Raw Input:** Iniciar a próxima fase do AutoMesh após a plataforma de validação e observabilidade.

**Context Gathered:**

- As Fases 1–6 entregaram ingestão, Silver, self-healing, insights, FinOps, RAG, delivery/HITL, validação e observabilidade.
- A arquitetura reserva a camada de consumo para produtos Gold, Databricks SQL/Lakeview, Fabric/Power BI e governança semântica.
- Já existem dados e fixtures de mercado/B3, infraestrutura, CRM/lost sales, insights, FinOps, delivery e evidências CAP-01–CAP-10.

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|---|---|---|
| Likely Location | `pipelines/gold/`, `pipelines/bi/`, `contracts/`, `tests/` | Gold jobs, contratos métricos, views e testes devem seguir os domínios existentes |
| Relevant KB Domains | `lakeflow`, `medallion`, `data-modeling`, `data-quality`, `cloud-platforms`, `testing` | Consultar padrões Gold, Delta/Lakeflow, star schema, quality gates e CI |
| IaC Patterns | Nenhum workspace Databricks provisionado no repositório; CI/DagBag já existentes | MVP local e portável; publicação externa opt-in, sem criar recursos ou custo |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|---|---|---|
| 1 | Qual é o objetivo principal da Fase 7? | **Produtos de Dados Gold + BI** | A fase prioriza consumo governado e métricas, não novos modelos de ML |
| 2 | Quem são os usuários principais? | **Executivos e equipe operacional** | Serão necessárias visões executiva e operacional sobre a mesma camada Gold |
| 3 | Qual tecnologia deve ser a base? | **Databricks SQL/Lakeview** | Delta/Unity Catalog continuam no centro; Snowflake/Fabric ficam posteriores |
| 4 | Existem amostras disponíveis? | **Sim, dados gerados nas Fases 1–6** | Fixtures e contratos existentes fundamentam os testes e os produtos |
| 5 | A abordagem Gold Delta + Lakeview foi confirmada? | **Sim, Approach A** | O Design deve detalhar Gold incremental, views semânticas e dashboards Lakeview |
| 6 | A separação local/externa foi confirmada? | **Sim, após checkpoint de validação** | Sem credenciais, produzir skip explícito; smokes externos são opt-in |

**Minimum Questions:** 3 (to ensure clarity before proceeding)

---

## Sample Data Inventory

| Type | Location | Count | Notes |
|---|---|---:|---|
| Input files | `pipelines/*/contracts/`, `pipelines/*/tests/` | 7+ domínios | Contratos YAML, fixtures e DataFrames para ingestão, insights, FinOps e delivery |
| Output examples | `pipelines/insights/model_registry_state.yaml`, `platform/validation/` | 2 famílias | Estado de modelo e evidências CAP-01–CAP-10 |
| Ground truth | Testes unitários das Fases 1–6 | 100+ casos históricos | Valores esperados de qualidade, anomalia, custo, idempotência e maturidade |
| Related code | `pipelines/processing/`, `pipelines/insights/`, `pipelines/finops/`, `pipelines/observability/` | 4 domínios | Fontes reutilizáveis e contratos de comportamento |

**How samples will be used:**

- Fixtures locais para validar agregações Gold e métricas sem exigir workspace.
- Contratos e schemas como referência de chaves, granularidade, owner e freshness.
- Testes de unicidade, completude, freshness, volume e consistência entre fatos e dimensões.
- Evidências da Fase 6 como fonte do painel operacional de maturidade e qualidade.

---

## Approaches Explored

### Approach A: Gold Delta + Databricks SQL/Lakeview ⭐ Recommended

**Description:** Criar produtos Gold em Delta, views semânticas no Databricks SQL e dois dashboards Lakeview: executivo e operacional.

**Pros:**

- Reutiliza diretamente Bronze/Silver, insights, FinOps e observabilidade.
- Evita duplicação de armazenamento e mantém a linhagem no Unity Catalog.
- Pode ser testado localmente antes do workspace.

**Cons:**

- Publicação e Direct Query reais dependem de Databricks.
- Algumas capacidades de governança só podem ser comprovadas externamente.

**Why Recommended:** Confiança **0,95**, baseada na arquitetura Delta/Databricks já adotada e nos padrões de medallion/lakeflow existentes na KB e no código.

---

### Approach B: Gold Delta + camada semântica independente

**Description:** Manter Gold em Delta, mas definir métricas numa camada portátil que possa alimentar Lakeview, Power BI ou outro consumidor.

**Pros:**

- Reduz dependência do fornecedor.
- Facilita futura integração com Fabric.

**Cons:**

- Adiciona contratos e abstrações antes de existir um consumidor alternativo.
- Aumenta o custo de validação do MVP.

---

### Approach C: Gold duplicado em Databricks e Snowflake

**Description:** Publicar os mesmos produtos em Databricks e Snowflake, com dbt para transformação no warehouse.

**Pros:**

- Demonstra uma arquitetura multicloud.

**Cons:**

- Duplica transformação, custos, governança e monitoramento.
- Pode produzir divergência entre métricas e exige contas externas.

---

## Data Engineering Context (if applicable)

### Source Systems

| Source | Type | Volume Estimate | Current Freshness |
|---|---|---|---|
| B3/market | API/Kafka | Fixture e fluxo de mercado | Batch/streaming conforme fonte |
| Infra telemetry | Kafka | Fixture sintética | Near-real-time local |
| CRM/lost sales | Batch | Fixture de testes | Batch |
| Insights/MLflow | Tabelas/artefatos | Resultado por execução | Por DAG |
| FinOps | Databricks billing ou fallback Airflow | Resultado por janela | Horário/por execução |
| Validation/observability | JSON/metrics | Por run e evento | Contínua/local |

### Data Flow Sketch

```text
[Bronze/Silver + Insights + FinOps + Evidence]
                    → [Gold incremental Delta]
                    → [Databricks SQL semantic views]
                    → [Executive Lakeview + Operational Lakeview]
```

### Key Data Questions Explored

| # | Question | Answer | Impact |
|---|---|---|---|
| 1 | Qual o volume esperado? | Fixtures e workloads existentes; volume externo ainda desconhecido | Começar com agregações incrementais e limites explícitos |
| 2 | Qual freshness é necessária? | Operacional deve exibir freshness; executivo pode ser batch | Definir SLA por produto no DEFINE |
| 3 | Quem consome? | Executivos e operações | Dois modelos de consumo com métricas compartilhadas |

---

## Selected Approach

| Attribute | Value |
|---|---|
| **Chosen** | Approach A — Gold Delta + Databricks SQL/Lakeview |
| **User Confirmation** | 2026-08-17 |
| **Reasoning** | Reutiliza a arquitetura existente, entrega dashboards demonstráveis e mantém o MVP sem Snowflake/Fabric ou novos custos |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|---|---|---|
| 1 | Gold incremental em Delta | Compatível com as camadas já implementadas | Gold duplicado em Snowflake |
| 2 | Databricks SQL/Lakeview como consumidor primário | Foi a tecnologia escolhida pelo usuário e integra com Unity Catalog | Fabric/Power BI no MVP |
| 3 | Dois dashboards, executivo e operacional | Cobre as duas personas sem multiplicar produtos | Painéis por área individual |
| 4 | Validação local + publicação externa opt-in | Contas externas e custos não estão autorizados por padrão | Provisionamento automático |

---

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed | Can Add Later? |
|---|---|---|
| Snowflake + dbt | Duplica transformação antes de validar o primeiro produto Gold | Yes |
| Microsoft Fabric/Power BI/DirectLake | Integração posterior; depende de tenant e licenças | Yes |
| Copilot e linguagem natural | Requer modelo semântico estável primeiro | Yes |
| Novos modelos de ML e previsão | Fase consome insights existentes | Yes |
| Terraform completo de workspace | Nenhum provisionamento externo autorizado nesta fase | Yes |
| Dashboards por persona adicional | Não necessário para o MVP executivo/operacional | Yes |

---

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---|---|---|---|
| Objetivo e personas | ✅ | Confirmou Gold + BI para executivos e operações | No |
| Abordagens | ✅ | Confirmou Approach A | No |
| Escopo YAGNI | ✅ | Confirmou escopo enxuto | No |
| Arquitetura e fronteira local/externa | ✅ | Confirmou separação e publicação opt-in | No |

**Minimum Validations:** 2 (to ensure alignment)

---

## Suggested Requirements for /define

### Problem Statement (Draft)

Os dados operacionais e de validação existem em vários domínios, mas ainda não estão consolidados em produtos Gold governados e visões executiva/operacional no Databricks.

### Target Users (Draft)

| User | Pain Point |
|---|---|
| Executivo/gestor | Não possui uma visão consolidada de tendências, oportunidades, risco e custo |
| Operação de dados | Não possui uma visão única de freshness, qualidade, falhas, DLQ e maturidade |

### Success Criteria (Draft)

- [ ] Produtos Gold incrementais e reproduzíveis em Delta para os domínios priorizados.
- [ ] Métricas versionadas com owner, granularidade, testes e definição semântica.
- [ ] Zero duplicidade de chave e zero falha de contrato nos fixtures aprovados.
- [ ] Freshness, volume, qualidade, custo e maturidade CAP-01–CAP-10 visíveis na visão operacional.
- [ ] Indicadores de tendência, lost sales, anomalias e custo visíveis na visão executiva.
- [ ] Testes locais passam sem Databricks configurado; smokes externos retornam skip explícito quando pré-requisitos faltam.
- [ ] Publicação Lakeview é auditável, opt-in e não cria recursos pagos automaticamente.

### Constraints Identified

- Workspace Databricks, Unity Catalog e SQL warehouse não estão validados/provisionados neste ambiente.
- Budget recorrente zero e ausência de mutações externas sem autorização explícita.
- Contratos e métricas devem permanecer versionados e compatíveis com a Fase 6.
- Full E2E externo depende de credenciais, recursos allowlisted e evidência com expiração.

### Out of Scope (Confirmed)

- Snowflake/dbt como engine de transformação do MVP.
- Microsoft Fabric, Power BI, DirectLake e Copilot.
- Novos modelos de ML, previsão ou perguntas em linguagem natural.
- Provisionamento Terraform completo e criação automática de workspace/warehouse.

---

## Session Summary

| Metric | Value |
|---|---:|
| Questions Asked | 6 |
| Approaches Explored | 3 |
| Features Removed (YAGNI) | 6 |
| Validations Completed | 4 |
| Duration | Uma sessão |

---

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_FASE7_GOLD_BI_DATABRICKS.md`
