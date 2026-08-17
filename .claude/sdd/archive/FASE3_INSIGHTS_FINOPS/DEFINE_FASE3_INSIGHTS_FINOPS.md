# DEFINE: Fase 3 — Motor de Insights (B3+Lost Sales) e Agente FinOps

> Isolation Forest com Continuous Training para detectar outliers cruzando cotações B3 e vendas perdidas, mais um Agente FinOps de governança de workload — ambos reaproveitando o pipeline de guardrails+PR da Fase 2 para qualquer ação que exija revisão humana.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | FASE3_INSIGHTS_FINOPS |
| **Date** | 2026-08-05 |
| **Author** | define-agent |
| **Status** | ✅ Shipped |
| **Clarity Score** | 14/15 |

---

## Problem Statement

A Fase 3 precisa cruzar os dados de mercado (B3) e vendas perdidas (CRM) já disponíveis na Silver para detectar outliers/oportunidades via um modelo de ML com ciclo de Continuous Training completo, e precisa de um Agente FinOps que monitore o consumo de workload da plataforma e proponha correções — ambos reaproveitando o mecanismo de guardrails+PR já construído na Fase 2 para qualquer ação que exija revisão humana (promoção de modelo, mudança de schedule).

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| Autor do projeto (Jonatas) | Operador do pipeline | Precisa que outliers/oportunidades cheguem prontos numa tabela, sem análise manual; precisa que custo anômalo seja sinalizado antes de virar surpresa na fatura |
| Recrutador/entrevistador técnico | Avaliador do portfólio | Precisa ver um ciclo de MLOps real (treino, drift, shadow deployment, promoção via PR) funcionando, não só descrito em slide |
| Revisor humano do PR (mesma persona da Fase 2) | Aprovador da correção/promoção | Precisa decidir promoção de modelo e mudanças de custo com contexto suficiente direto no PR |

---

## Goals

| Priority | Goal |
|----------|------|
| **MUST** | Modelo Isolation Forest treinado e registrado no MLflow (stage `Staging`) a partir de `silver.b3_quotes` + `silver.crm_lost_sales` |
| **MUST** | Inferência roda de hora em hora com o modelo `Production`, gravando outliers em `gold.market_insights` |
| **MUST** | Drift check compara distribuição nova vs. baseline e dispara retreino quando o limiar é excedido |
| **MUST** | Promoção de modelo (`Staging` → `Production`) só acontece via PR aprovado e mergeado — nunca automática |
| **MUST** | Agente FinOps monitora consumo por job de hora em hora e propõe correção (PR) quando detecta anomalia |
| **MUST** | 100% das decisões de FinOps e de promoção de modelo passam pelos mesmos guardrails (allowlist + conteúdo) da Fase 2 |
| **SHOULD** | Fallback via `dag_run.duration` do Airflow quando `system.billing.usage` não estiver acessível |
| **SHOULD** | Shadow check compara `Staging` vs. `Production` nos mesmos dados antes de gerar o diagnóstico de promoção |
| **COULD** | Dados ficam estruturados de forma reutilizável para o Painel Sentinela da Fase 5 (dashboard consolidado) |

**Priority Guide:**
- **MUST** = MVP fails without this
- **SHOULD** = Important, but workaround exists
- **COULD** = Nice-to-have, cut first if needed

---

## Success Criteria

- [ ] Modelo Isolation Forest treinado e registrado no MLflow (`Staging`) a partir das 2 tabelas Silver
- [ ] Inferência de hora em hora grava outliers em `gold.market_insights`
- [ ] Drift check dispara retreino automaticamente quando a distribuição diverge do baseline
- [ ] 100% das promoções de modelo passam por PR — 0% automáticas
- [ ] Agente FinOps monitora 100% dos jobs da plataforma de hora em hora
- [ ] 100% das decisões de FinOps/promoção passam pelos guardrails (allowlist + conteúdo) já existentes

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Happy path — outlier detectado e gravado | Dados novos chegam na Silver | `dag_generate_insights` roda com o modelo `Production` | Outliers são gravados em `gold.market_insights` dentro de 1h |
| AT-002 | Drift dispara retreino | A distribuição das features novas diverge do baseline de treino além do limiar | O drift check roda | `dag_train_outlier_model` é disparado e um novo modelo aparece em `Staging` no MLflow |
| AT-003 | Promoção de modelo exige PR | Um modelo em `Staging` supera o `Production` no shadow check | O diagnóstico é gerado | Um PR é aberto propondo a promoção — o modelo **não** é promovido automaticamente |
| AT-004 | FinOps detecta anomalia de custo | Um job consome significativamente mais que sua média histórica | `dag_finops_monitor` roda | Um diagnóstico é gerado e, se aprovado nos guardrails, um PR é aberto propondo correção (schedule/`OPTIMIZE`) |

---

## Out of Scope

- Databricks Lakehouse Monitoring nativo — comparação estatística simples (KS-test/PSI) cobre a necessidade
- Ensemble de modelos — só Isolation Forest neste MVP
- Alertas externos (PagerDuty/Slack) para o Agente FinOps — Fase 5
- Inferência de outliers em tempo real/streaming — batch hourly já atende
- Notificação via Microsoft Teams/Outlook (Adaptive Cards) — Fase 5

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Technical | Acesso a `system.billing.usage` no Databricks Free Edition não confirmado | Fallback via `dag_run.duration` do Airflow, a validar no Design |
| Technical | MLflow tracking/registry precisa estar disponível no workspace Free Edition | Assunção de risco a validar no Design (mesma classe da API do Databricks na Fase 2) |
| Resource | Sem orçamento para ferramentas externas de FinOps de terceiros | Toda a lógica de detecção/correção fica no código do projeto |

---

## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `pipelines/insights/` (novo: treino, inferência, drift) + extensão de `pipelines/self_healing/` (novos tipos de diagnóstico) | Reaproveita o pacote de self-healing em vez de duplicar guardrails/PR |
| **KB Domains** | `operations/cost`, `databricks/patterns/compute-patterns`, `ai-data-engineering`, `genai`, `data-quality` | Design deve consultar `cost-patterns.md` e validar `system.billing.usage` |
| **IaC Impact** | MLflow tracking/registry (assumir disponível) + acesso a `system.billing.usage` (TBD) | Design deve validar as duas coisas antes de fechar a arquitetura |

---

## Data Contract (if applicable)

### Source Inventory
| Source | Type | Volume | Freshness | Owner |
|--------|------|--------|-----------|-------|
| `silver.b3_quotes`, `silver.crm_lost_sales` | Tabelas Delta (Fase 2) | Baixo (herdado) | Hourly | Projeto AutoMesh |
| `system.billing.usage` | Tabela de sistema Databricks | TBD | TBD | Databricks (gerenciada) |
| `dag_run` (Airflow) | Metadados de execução | Baixo | Por run | Projeto AutoMesh |

### Schema Contract
Exemplo representativo (`gold.market_insights`, novo):

| Column | Type | Constraints | PII? |
|--------|------|-------------|------|
| insight_id | STRING | NOT NULL | No |
| source_ticker | STRING | Nullable (pode cruzar múltiplas fontes) | No |
| anomaly_score | DECIMAL | NOT NULL | No |
| model_version | STRING | NOT NULL (run_id do MLflow) | No |
| generated_at | TIMESTAMP | NOT NULL | No |

### Freshness SLAs
| Layer | Target | Measurement |
|-------|--------|-------------|
| `gold.market_insights` | Atualizada em até 1h após novos dados na Silver | Timestamp de conclusão do `dag_generate_insights` |
| Diagnóstico de FinOps | Gerado em até 1h após anomalia de consumo | Timestamp da run do job vs. timestamp do diagnóstico |

### Completeness Metrics
- 100% das runs de inferência produzem um registro (mesmo que vazio) em `gold.market_insights` — nenhuma execução silenciosamente pulada
- 100% dos eventos de FinOps e de promoção de modelo passam pelo `dag_self_healing_diagnose`

### Lineage Requirements
- Cada outlier em `gold.market_insights` é rastreável ao `run_id` do MLflow que gerou o modelo usado
- Cada PR de promoção é rastreável ao shadow check (métricas de `Staging` vs. `Production`) que o originou

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|---------------------|--------------|
| A-001 | MLflow tracking/registry está disponível no workspace Databricks Free Edition | Precisaria de uma solução alternativa de model registry (ex: tabela Delta customizada) | [ ] |
| A-002 | `system.billing.usage` é acessível no Free Edition | Fallback via `dag_run.duration` do Airflow (já documentado como SHOULD) | [ ] |
| A-003 | O guardrail de allowlist da Fase 2 pode ser estendido para cobrir "promover modelo" e "mudar schedule de DAG" sem reescrever a lógica core | Precisaria de um guardrail separado, duplicando parte da lógica já existente | [ ] |

**Note:** Validate critical assumptions before DESIGN phase. Unvalidated assumptions become risks.

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Sentença única, específica, cobrindo as duas frentes (insights + FinOps) e o mecanismo compartilhado (guardrails+PR) |
| Users | 2 | Três personas com pain points claros; "recrutador" é persona atípica para sistema técnico (mesma ressalva das Fases 1-2) |
| Goals | 3 | MoSCoW aplicado a todos os goals |
| Success | 3 | Critérios com números/binários claros (1h, 100%, 0% automático) |
| Scope | 3 | Out of scope explícito com 5 itens, cada um mapeado a uma razão concreta ou fase futura |
| **Total** | **14/15** | Acima do gate de 12/15 — pronto para Design |

**Minimum to proceed: 12/15**

---

## Open Questions

None — ready for Design. O Design deverá validar as Assumptions A-001 (MLflow no Free Edition) e A-002 (`system.billing.usage`), e definir o formato exato da extensão da allowlist do self-healing para cobrir as novas ações (A-003).

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|------------|
| 1.0 | 2026-08-05 | define-agent | Initial version — extraído de BRAINSTORM_FASE3_INSIGHTS_FINOPS.md |
| 1.1 | 2026-08-06 | ship-agent | Shipped and archived |

---

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_FASE3_INSIGHTS_FINOPS.md`
