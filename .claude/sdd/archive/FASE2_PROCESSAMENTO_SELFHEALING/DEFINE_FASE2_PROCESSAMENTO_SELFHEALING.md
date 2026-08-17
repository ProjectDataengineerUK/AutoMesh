# DEFINE: Fase 2 — Processamento (Bronze→Silver) e Self-Healing

> Pipeline PySpark Bronze→Silver no Databricks, mais um agente que diagnostica falhas de contrato e de execução via LLM e abre PRs de correção no GitHub, dentro de guardrails de escopo e conteúdo.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | FASE2_PROCESSAMENTO_SELFHEALING |
| **Date** | 2026-08-03 |
| **Author** | define-agent |
| **Status** | ✅ Shipped |
| **Clarity Score** | 14/15 |

---

## Problem Statement

A Fase 2 precisa processar os dados validados do Bronze (Fase 1) até a Silver via PySpark no Databricks Free Edition, e fechar o ciclo de resiliência da plataforma: quando ocorre uma falha de contrato (`bronze_dlq`) ou de execução (exceção no Airflow), um agente deve diagnosticar a causa raiz via LLM, propor uma correção (no contrato de dados ou no código) dentro de guardrails de escopo e conteúdo, e abrir um Pull Request no GitHub para revisão humana.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| Autor do projeto (Jonatas) | Operador do pipeline | Precisa que falhas sejam diagnosticadas e propostas de correção cheguem prontas para revisão, sem investigar cada erro manualmente |
| Recrutador/entrevistador técnico | Avaliador do portfólio | Precisa ver o diferencial de "agente autônomo com guardrails" funcionando de ponta a ponta, não só descrito em slide |
| Revisor humano do PR (o próprio autor, no papel de mantenedor) | Aprovador da correção | Precisa que o PR tenha contexto suficiente (diagnóstico + diff + link do log da falha) para decidir rápido, sem abrir o Databricks/Airflow pra investigar |

---

## Goals

| Priority | Goal |
|----------|------|
| **MUST** | Pipeline PySpark Bronze→Silver roda no Databricks Free Edition, disparado pelo Airflow |
| **MUST** | Silver usa MERGE/dedup por chave de negócio nas fontes que têm entidade (`b3_quotes`, `crm_lost_sales`); telemetria/logs continuam append-only |
| **MUST** | `dag_self_healing_diagnose` consome as duas fontes de falha: `bronze_dlq` (contrato) e `on_failure_callback` do Airflow (execução) |
| **MUST** | LLM produz diagnóstico estruturado (causa raiz + tipo de correção + diff proposto) para cada evento de falha recebido |
| **MUST** | Guardrail de allowlist bloqueia qualquer diff fora do escopo de arquivos permitido, antes de qualquer PR |
| **MUST** | Guardrail de conteúdo bloqueia diffs com padrões perigosos conhecidos, antes de qualquer PR |
| **MUST** | PR só é aberto no GitHub quando o diff passa nos dois guardrails, com diagnóstico + diff + link do log no corpo |
| **SHOULD** | Rejeições de guardrail ficam registradas em `self_healing_rejections` (Delta), rastreáveis para revisão manual |
| **SHOULD** | Corpo do PR segue um template consistente (diagnóstico, diff, link do log, motivo da correção) |
| **COULD** | Métricas básicas de falhas diagnosticadas vs. rejeitadas pelos guardrails (preparação para o Painel Sentinela da Fase 3) |

**Priority Guide:**
- **MUST** = MVP fails without this
- **SHOULD** = Important, but workaround exists
- **COULD** = Nice-to-have, cut first if needed

---

## Success Criteria

- [ ] Pipeline Bronze→Silver processa as 4 fontes da Fase 1, com MERGE nas 2 fontes com chave de negócio e append nas 2 restantes
- [ ] 100% dos eventos de falha (DLQ + execução) passam pelo `dag_self_healing_diagnose`
- [ ] 100% das propostas de diff fora da allowlist são bloqueadas antes de chegar a um PR
- [ ] 100% das propostas de diff com padrão perigoso conhecido são bloqueadas antes de chegar a um PR
- [ ] 100% dos PRs abertos incluem diagnóstico, diff e link do log da falha original
- [ ] 100% das rejeições de guardrail ficam rastreáveis em `self_healing_rejections`

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Happy path — falha de contrato conhecida vira PR | Um registro cai na `bronze_dlq` com `_failure_reason: null_violation:ticker` | O `dag_self_healing_diagnose` processa o evento | O LLM propõe um diff no contrato YAML (relaxando o campo ou explicando a causa), os dois guardrails aprovam, e um PR é aberto no GitHub com diagnóstico + link da falha |
| AT-002 | Falha de execução (exceção não tratada) é diagnosticada | Uma task do Airflow lança uma exceção não tratada (ex: timeout de rede) | O `on_failure_callback` dispara | O mesmo fluxo de diagnóstico é acionado com o traceback como contexto, resultando em PR ou rejeição registrada |
| AT-003 | Guardrail de allowlist bloqueia diff fora de escopo | O LLM propõe um diff que toca um arquivo fora da allowlist (ex: `.github/workflows/*`) | O guardrail de allowlist avalia a proposta | O PR não é aberto; o evento é registrado em `self_healing_rejections` com o motivo `out_of_scope_path` |
| AT-004 | Guardrail de conteúdo bloqueia padrão perigoso | O LLM propõe um diff contendo um padrão perigoso conhecido (ex: `os.system`, credencial hardcoded) | O guardrail de conteúdo avalia o diff | O PR não é aberto; o evento é registrado em `self_healing_rejections` com o motivo do bloqueio |

---

## Out of Scope

- Roteamento multi-modelo por custo (LiteLLM) — Fase 4
- Retomada automática do pipeline após merge do PR (webhook fechando o ciclo do HITL) — Fase 5
- Framework dedicado de guardrails (ex: NeMo Guardrails) — implementação própria (allowlist + checagem de conteúdo) por ora
- SCD2 / histórico completo (`valid_from`/`valid_to`) na camada Silver
- Painel Sentinela / observabilidade consolidada entre fases — Fase 3
- Merge automático do PR pelo próprio agente — o token/app do self-healing não tem permissão de merge

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Technical | Databricks Free Edition (serverless) — acesso via API/service principal para chamadas externas do Airflow ainda não confirmado | Vira assunção de risco a validar no Design; se não for possível, força reconsiderar Approach B (Databricks Workflows nativo) |
| Resource | Custo de chamada ao LLM por evento de falha | Sem roteamento multi-modelo neste MVP; volume baixo esperado (mesmo perfil de portfólio da Fase 1) |
| Security | Token/app do GitHub usado pelo self-healing só pode criar branch/PR, nunca mergear | Preserva o HITL real — merge é sempre decisão humana |

---

## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `pipelines/processing/` (Bronze→Silver) e `pipelines/self_healing/` (novo, ao lado de `pipelines/ingestion/` da Fase 1) | Mantém o padrão de pacote por fase já estabelecido |
| **KB Domains** | `databricks`, `spark`, `lakeflow`, `medallion`, `data-quality`, `airflow` (padrão `error-handling.md`) | Design deve consultar `medallion/quick-reference.md` (regras de Silver) e `lakeflow/quick-reference.md` |
| **IaC Impact** | New resources — TBD | Workspace Databricks Free Edition + service principal/token; GitHub token/app com permissão restrita (branch+PR, sem merge) |

---

## Data Contract (if applicable)

### Source Inventory
| Source | Type | Volume | Freshness | Owner |
|--------|------|--------|-----------|-------|
| `bronze.b3_quotes`, `bronze.crm_lost_sales`, `bronze.infra_telemetry`, `bronze.usage_logs` | Tabelas Delta (Fase 1) | Baixo (herdado) | Conforme SLA da Fase 1 | Projeto AutoMesh |
| `bronze_dlq` | Tabela Delta unificada (Fase 1) | Baixo | No momento da falha de contrato | Projeto AutoMesh |
| `on_failure_callback` (Airflow) | Evento/contexto de exceção (novo) | Baixo | No momento da falha de execução | Projeto AutoMesh |

### Schema Contract
Exemplo representativo (`self_healing_rejections`, novo):

| Column | Type | Constraints | PII? |
|--------|------|-------------|------|
| event_id | STRING | NOT NULL | No |
| source_failure_type | STRING | NOT NULL (`contract` \| `execution`) | No |
| rejection_reason | STRING | NOT NULL | No |
| proposed_diff | STRING | NOT NULL | No |
| rejected_at | TIMESTAMP | NOT NULL | No |

### Freshness SLAs
| Layer | Target | Measurement |
|-------|--------|-------------|
| Silver | Atualizada em até 30 min após o Bronze da Fase 1 receber novos dados | Timestamp de conclusão do Job Databricks vs. timestamp de ingestão no Bronze |
| Diagnóstico de falha | Gerado em até 10 min após a falha ser detectada (DLQ ou callback) | Timestamp do evento de falha vs. timestamp de abertura do PR/rejeição |

### Completeness Metrics
- 100% dos eventos de falha (DLQ + execução) passam pelo `dag_self_healing_diagnose` — nenhum evento ignorado
- 100% das decisões (PR aberto ou rejeitado) ficam rastreáveis, sem "falha silenciosa" no meio do fluxo

### Lineage Requirements
- Cada registro na Silver é rastreável à tabela Bronze de origem e à versão do contrato usada
- Cada PR (ou rejeição) é rastreável ao evento de falha original (registro da DLQ ou log de execução do Airflow)

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|---------------------|--------------|
| A-001 | Databricks Free Edition permite acesso via API/service principal para chamadas externas do Airflow | Seria necessário rodar o processamento de dentro do próprio Databricks (Workflows nativo), forçando reconsiderar o Approach B do brainstorm | [ ] |
| A-002 | O provedor de LLM escolhido no Design tem API estável e custo previsível por chamada de diagnóstico | Seria necessário trocar de provedor ou implementar cache/rate limiting mais agressivo | [ ] |
| A-003 | O token/app do GitHub usado pelo self-healing consegue ter escopo restrito a "criar branch + PR", sem permissão de merge | Se o escopo mínimo não for possível, precisa de uma camada extra de proteção (ex: branch protection rules) para preservar o HITL | [ ] |

**Note:** Validate critical assumptions before DESIGN phase. Unvalidated assumptions become risks.

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Sentença única, específica, cobrindo as duas metades (processamento + self-healing) e o mecanismo (LLM, guardrails, PR) |
| Users | 2 | Três personas com pain points claros; "recrutador" é um persona atípico para um sistema técnico (mesma ressalva da Fase 1) |
| Goals | 3 | MoSCoW aplicado a todos os goals, com justificativa herdada do YAGNI do brainstorm |
| Success | 3 | Todos os critérios têm números/binários claros (100%, 4 fontes, 2 guardrails) |
| Scope | 3 | Out of scope explícito com 6 itens, cada um mapeado a uma fase futura ou razão concreta |
| **Total** | **14/15** | Acima do gate de 12/15 — pronto para Design |

**Minimum to proceed: 12/15**

---

## Open Questions

None — ready for Design. O Design deverá resolver: (1) qual provedor de LLM usar para o diagnóstico, (2) o mecanismo exato de acesso do Airflow ao Databricks Free Edition (API/service principal — validar Assumption A-001), e (3) a lista concreta de padrões perigosos do guardrail de conteúdo.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|------------|
| 1.0 | 2026-08-03 | define-agent | Initial version — extraído de BRAINSTORM_FASE2_PROCESSAMENTO_SELFHEALING.md |
| 1.1 | 2026-08-04 | ship-agent | Shipped and archived |

---

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_FASE2_PROCESSAMENTO_SELFHEALING.md`
