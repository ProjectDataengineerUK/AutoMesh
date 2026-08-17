# BRAINSTORM: Fase 6 — Platform Engineering, Observabilidade e Validação Integrada

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | FASE6_PLATFORM_OBSERVABILITY_VALIDATION |
| **Date** | 2026-08-17 |
| **Status** | Complete (Defined) |
| **Source** | Auditoria e artefatos SHIPPED das Fases 1-5 |

---

## Initial Idea

Transformar as cinco fases implementadas do AutoMesh em uma plataforma reproduzível e comprovável. A Fase 6 não adiciona uma nova cadeia de negócio: ela fecha lacunas de CI/CD, ambientes, observabilidade, segurança, recuperação e validação ponta a ponta que impedem o projeto de avançar de `Implemented/Locally Validated` para `Infrastructure Validated/Operationally Complete`.

---

## Discovery Questions & Answers

| # | Question | Answer | Consequence |
|---|---|---|---|
| 1 | Qual é o maior risco atual? | O código existe, mas várias integrações centrais só foram testadas localmente ou com mocks | Validação externa e evidência reproduzível são prioridade |
| 2 | Devemos adicionar Fabric/Power BI agora? | Não | Camada analítica nova esconderia dívida operacional existente |
| 3 | O que significa sucesso? | Conseguir executar, observar, quebrar, recuperar e auditar um fluxo integrado | Métricas e runbooks entram no escopo obrigatório |
| 4 | Como lidar com serviços ainda não provisionados? | Gates progressivos e adaptadores testáveis | Nenhum ambiente ausente pode ser tratado como “passou” |
| 5 | Qual deve ser a fonte da verdade de entrega? | Git + CI + relatório de validação gerado automaticamente | O primeiro commit e checks obrigatórios são pré-requisitos |
| 6 | A Fase 6 deve escolher uma nuvem definitiva? | Não para o núcleo; Azure/Microsoft e Databricks continuam os alvos de integração | Observabilidade usa padrões portáveis, com exportação posterior ao Sentinel |
| 7 | O stack Docker completo precisa ser o único gate? | Não | DagBag isolado e testes por domínio reduzem custo e flakiness |

---

## Current Validation Inventory

| Capability | Current evidence | Missing evidence |
|---|---|---|
| Kafka/B3 → Bronze/DLQ | Redpanda, brapi.dev e Delta reais | Run completa e repetível pelo scheduler |
| Bronze → Silver | Código e estrutura | Cluster Databricks/Spark real |
| Self-healing | Unit tests, guardrails e DagBag | LLM + GitHub PR ponta a ponta em repositório de teste |
| Insights/MLflow | MLflow SQLite e inferência local | Unity Catalog/registry real |
| FinOps | Detecção unitária | `system.billing.usage` e fallback com metastore real |
| RAG | Mocks, Delta e contratos | SharePoint, Graph e Vector Search reais |
| Delivery/HITL | Domínio, SQLite, testes e DagBag | Teams app/bot, Outlook e callback autenticado reais |
| CI/CD | Workflow criado | Primeiro commit e execução real do workflow |
| Observability | Logs locais dispersos | Métricas, traces, alertas, painel e SLOs unificados |

---

## Approaches Explored

### Approach A: Validation-first Platformization — Selected

Organizar a fase em ondas: baseline Git/CI, telemetria comum, ambientes/adaptadores, testes integrados, chaos/recovery e somente então validação externa. Cada capacidade avança individualmente pela taxonomia:

```text
Implemented → Locally Validated → Infrastructure Validated → Operationally Complete
```

**Advantages**

- Fecha diretamente as lacunas encontradas na auditoria.
- Produz evidência incremental mesmo quando um serviço externo não está disponível.
- Evita um teste ponta a ponta monolítico e frágil.
- Melhora a apresentação do portfólio: estado e evidência ficam objetivos.

**Trade-offs**

- Entrega menos funcionalidade visível que Fabric/Power BI.
- Exige disciplina de infraestrutura, segurança e documentação operacional.
- Alguns gates continuarão bloqueados até o provisionamento externo.

### Approach B: Expand Features First

Implementar dbt/Snowflake/Fabric/Power BI antes da plataforma operacional.

**Rejected because:** amplia o número de integrações não validadas, aumenta custo e reduz a credibilidade do termo “Zero-Touch”. Deve ser uma Fase 7 posterior.

### Approach C: One Big End-to-End Test

Provisionar tudo e tentar validar toda a sequência em uma única execução.

**Rejected because:** custo, diagnóstico difícil, dependência de múltiplos trials e alto risco de uma falha externa bloquear toda a evidência. Um E2E final continua necessário, mas como último gate, não como estratégia principal.

### Approach D: Documentation-only Hardening

Criar diagramas, runbooks e checklist sem modificar runtime/CI.

**Rejected because:** melhora apresentação, mas não produz evidência executável nem detecta regressões.

---

## Selected Scope

### Workstream 1 — Repository and CI Baseline

- Primeiro commit e baseline rastreável.
- CI por domínio com cache e matriz Python/Airflow compatível.
- Ruff, pytest, DagBag isolado, secret scanning e dependency audit.
- Artefatos de teste e relatório de validação publicados pelo CI.
- Branch protection e revisão obrigatória documentadas.

### Workstream 2 — Unified Observability

- Contexto estruturado comum: `correlation_id`, `dag_id`, `run_id`, `event_id`, `source`.
- Métricas para ingestão, DLQ, processamento, drift, FinOps, RAG, delivery e HITL.
- OpenTelemetry como interface de traces/métricas quando aplicável.
- Stack local leve para métricas/painel, sem tornar o Prometheus/Grafana local requisito de produção.
- Alertas e SLOs versionados.

### Workstream 3 — Environment and Secrets

- Inventário `local`, `integration` e `production`.
- Configuração validada e fail-fast.
- Secret backend/managed identity no alvo; `.env` apenas local e ignorado.
- Matriz de permissões mínimas para GitHub, Databricks, Microsoft Graph, Teams e MLflow.
- Templates IaC somente para recursos confirmados; nenhum recurso cloud fictício.

### Workstream 4 — Integration Harness

- Testes com containers isolados por domínio.
- Fixtures/seed determinísticos.
- Adapters fake e contract tests para serviços externos.
- Smoke tests marcados por capacidade e executados apenas quando credenciais existirem.
- Relatório automático mostrando `PASS`, `FAIL`, `SKIP_WITH_REASON` por capability.

### Workstream 5 — Reliability and Recovery

- Testes de retry, replay, duplicação, poison message, timeout e rate limit.
- Recuperação de checkpoint/cursor e garantia de não perder eventos.
- Concorrência de outbox/ledger.
- Runbooks para DLQ, scheduler degradado, Graph indisponível e precondition stale.
- Backup/restore documentado para estados locais e managed stores.

### Workstream 6 — External Validation Campaign

- Databricks/Unity Catalog/Vector Search.
- Microsoft 365/SharePoint/Teams/Outlook.
- GitHub de teste + provedor LLM.
- FinOps billing quando disponível.
- E2E final com evidência, custo, tempo e limitações.

---

## Features Removed (YAGNI)

| Feature | Reason | Revisit |
|---|---|---|
| Power BI/Fabric dashboards de negócio | Nova capacidade funcional, não observabilidade operacional | Fase 7 |
| Snowflake/dbt | Não é necessário para validar o fluxo Delta atual | Fase 7 ou decisão arquitetural separada |
| Kubernetes | Complexidade sem demanda de escala comprovada | Quando houver requisito multi-réplica real |
| Multi-cloud deployment | Aumenta matriz de validação sem benefício atual | Futuro |
| Auto-remediation sem aprovação | Contraria guardrails e HITL existentes | Não planejado |
| SIEM completo no MVP local | Sentinel exige ambiente externo; primeiro definir eventos e exportadores | Onda externa da Fase 6 |

---

## Key Decisions Made

| # | Decision | Rationale |
|---|---|---|
| 1 | Fase 6 é validation-first | A principal dívida é evidência operacional, não código de negócio |
| 2 | Taxonomia de maturidade é gate formal | Impede voltar a chamar mocks de validação real |
| 3 | CI e DagBag isolados precedem stack completo | Menor custo e diagnóstico mais determinístico |
| 4 | Observabilidade é portável | Evita acoplar o domínio ao Sentinel/Grafana |
| 5 | External smoke tests usam marcadores e skip com motivo | Ausência de credencial é estado visível, nunca sucesso implícito |
| 6 | E2E completo é último gate | Falhas podem ser isoladas antes da campanha cara |
| 7 | Fase 7 só começa após relatório consolidado | Evita acumular novas integrações não verificadas |

---

## Incremental Validations

1. CI local equivalente roda lint, testes e DagBag sem serviços externos.
2. Cada domínio emite ao menos uma métrica com correlação comum.
3. Falha simulada chega ao alerta e ao runbook correto.
4. Checkpoint/cursor sobrevive a retry e restart sem perda nem duplicação indevida.
5. Um ambiente externo por vez recebe smoke test com evidência arquivada.
6. E2E final só é executado após todos os smokes necessários passarem.

---

## Suggested Requirements for DEFINE

### Problem Statement

O AutoMesh possui cinco fases implementadas, mas não consegue provar de forma automática e repetível que o fluxo completo opera, é observável e se recupera nos serviços externos alvo. A Fase 6 deve criar o sistema de validação e operação que converte afirmações arquiteturais em evidência auditável.

### Target Users

- Autor/operador do projeto.
- Revisor técnico/recrutador avaliando evidência.
- Responsável de plataforma/SRE.
- Segurança/auditoria.
- Desenvolvedor que altera qualquer pipeline.

### Preliminary Success Criteria

- [ ] 100% dos domínios têm job de CI com lint, testes e artefato de resultado.
- [ ] 100% dos DAGs importam no Airflow alvo sem erros.
- [ ] Cada integração externa possui contract test e smoke test separado.
- [ ] Nenhum smoke ausente é reportado como pass; sempre `SKIP_WITH_REASON`.
- [ ] Todos os eventos críticos carregam `correlation_id` ponta a ponta.
- [ ] Pelo menos cinco cenários de falha/recovery são executados automaticamente.
- [ ] Um relatório consolida a maturidade real de cada capability.
- [ ] O E2E completo produz evidência ou um blocker preciso por etapa.

### Constraints

- Contas trial/free e recursos locais limitados.
- Credenciais externas podem não estar disponíveis simultaneamente.
- O repositório ainda não possui baseline de commits.
- Docker Desktop completo já demonstrou saturação; testes isolados são obrigatórios.
- Dados e identidades de teste não podem conter PII real.

### Out of Scope

- Nova camada analítica de negócio.
- Redesenho funcional das Fases 1-5 sem evidência de necessidade.
- Declaração de produção sem segurança, SLOs e recuperação comprovados.

---

## Risks and Open Questions

| ID | Risk/Question | Proposed treatment |
|---|---|---|
| R-001 | Quais contas externas estão realmente disponíveis? | Inventário no DEFINE; gates condicionais por capability |
| R-002 | GitHub Actions pode suportar todas as dependências pesadas? | Matriz por domínio e containers isolados, não um único job gigante |
| R-003 | Qual backend de métricas local cabe nos recursos? | Começar com interface + logs/artefatos; painel leve opcional |
| R-004 | Sentinel estará disponível? | Tratar como exporter externo, não requisito do núcleo |
| R-005 | Como medir custo da campanha? | Budget máximo e registro por smoke/E2E no DEFINE |
| R-006 | Primeiro commit deve incluir `mlruns`/artefatos locais? | Não; manter ignorados e versionar apenas metadados necessários |

---

## Session Summary

A Fase 6 será uma fase de platformization e prova operacional. A abordagem selecionada evita adicionar novas funcionalidades antes de validar as existentes, usa gates progressivos, testes isolados, telemetria portável e uma campanha externa capability-by-capability. Fabric/Power BI/dbt/Snowflake ficam reservados para uma possível Fase 7.

---

## Next Step

Criar `DEFINE_FASE6_PLATFORM_OBSERVABILITY_VALIDATION.md` com inventário de ambientes, métricas/SLOs numéricos, matriz de permissões, orçamento, acceptance tests e critérios formais para cada nível de maturidade.
