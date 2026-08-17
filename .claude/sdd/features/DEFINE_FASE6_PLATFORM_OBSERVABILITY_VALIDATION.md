# DEFINE: Fase 6 — Platform Engineering, Observabilidade e Validação Integrada

> Criar uma base reproduzível de CI, telemetria, testes de integração e evidência operacional para elevar cada capability das Fases 1-5 por níveis explícitos de maturidade.

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | FASE6_PLATFORM_OBSERVABILITY_VALIDATION |
| **Date** | 2026-08-17 |
| **Author** | Codex + usuário |
| **Status** | ✅ Complete (Built) |
| **Clarity Score** | 14/15 |

---

## Problem Statement

O AutoMesh possui cinco fases implementadas, porém a evidência está distribuída entre testes locais, mocks, smoke tests manuais e relatórios SDD. Sem baseline Git, execução real de CI, telemetria comum e campanha externa por capability, não é possível provar de forma automática que o sistema completo opera, se recupera e mantém as garantias de segurança declaradas.

A Fase 6 deve converter cada afirmação arquitetural em uma evidência versionada, reproduzível e classificável, sem representar credencial ausente ou serviço não provisionado como sucesso.

---

## Target Users

| User | Role | Pain Point |
|---|---|---|
| Autor/operador | Mantém e demonstra o AutoMesh | Não possui um comando/relatório único que prove o estado real da plataforma |
| Desenvolvedor | Modifica pipelines e DAGs | Não recebe feedback isolado e rápido sobre regressões por domínio |
| Platform/SRE | Opera ambientes | Não possui SLOs, métricas, alertas ou runbooks consistentes |
| Segurança/auditoria | Verifica controles | Não consegue reconstruir capability → teste → evidência → decisão de release |
| Revisor técnico/recrutador | Avalia o portfólio | Precisa distinguir implementação, mock, validação local e integração cloud real |

---

## Goals

| Priority | Goal |
|---|---|
| **MUST** | Estabelecer baseline Git rastreável e CI executável por domínio |
| **MUST** | Validar todos os DAGs descobertos no Airflow 3.0 com zero erros de importação |
| **MUST** | Gerar relatório consolidado de capabilities com `PASS`, `FAIL` ou `SKIP_WITH_REASON` e nível de maturidade |
| **MUST** | Propagar um contexto de correlação mínimo pelos eventos críticos das Fases 1-5 |
| **MUST** | Definir métricas, SLOs e alertas para ingestão, processamento, self-healing, insights, FinOps, RAG e delivery |
| **MUST** | Executar testes automatizados de retry, replay, checkpoint/cursor, idempotência e recuperação |
| **MUST** | Separar testes unitários, contract tests, integração local, smoke externo e E2E |
| **MUST** | Impedir que ausência de credencial/infraestrutura seja registrada como sucesso |
| **SHOULD** | Disponibilizar painel operacional local leve, derivado das mesmas métricas exportáveis |
| **SHOULD** | Criar templates de configuração/IaC apenas para recursos externos confirmados |
| **SHOULD** | Publicar artefatos de teste, DagBag e validação em cada execução de CI |
| **COULD** | Exportar eventos de segurança para Microsoft Sentinel quando um workspace estiver disponível |

---

## Maturity Model

| Level | Required evidence |
|---|---|
| `Implemented` | Código, lint e testes automatizados do domínio existem |
| `Locally Validated` | Capability foi exercitada com componentes locais reais e resultado persistido |
| `Infrastructure Validated` | Capability foi exercitada contra o serviço externo alvo em ambiente de teste |
| `Operationally Complete` | SLO, alerta, recovery, segurança e runbook foram exercitados além do happy path |

Rules:

1. O nível é atribuído por capability, nunca à plataforma inteira por inferência.
2. Um nível só pode avançar se todos os requisitos do nível anterior estiverem verdes.
3. `SKIP_WITH_REASON` preserva o nível anterior; nunca promove.
4. Evidência manual precisa registrar data, ambiente, comando/cenário e resultado.
5. Evidência expirada pode reduzir confiança sem apagar o histórico; validade padrão de smoke externo: 30 dias.

---

## Capability Inventory

| ID | Capability | Current level | Target in Fase 6 |
|---|---|---|---|
| CAP-01 | Kafka/B3 → Bronze/DLQ | Locally Validated | Operationally Complete local |
| CAP-02 | Bronze → Silver | Implemented | Infrastructure Validated |
| CAP-03 | Self-healing LLM → GitHub PR | Implemented | Infrastructure Validated em repositório de teste |
| CAP-04 | MLflow treino/inferência/drift | Locally Validated | Infrastructure Validated |
| CAP-05 | FinOps billing/fallback | Implemented | Infrastructure Validated quando billing existir |
| CAP-06 | SharePoint → Bronze | Implemented | Infrastructure Validated |
| CAP-07 | Vector Search/retrieval/RAGAS | Implemented | Infrastructure Validated |
| CAP-08 | Teams/Outlook/HITL | Implemented + Airflow Validated | Infrastructure Validated |
| CAP-09 | CI/DagBag/quality gates | Implemented parcialmente | Operationally Complete |
| CAP-10 | Observabilidade e recovery | Não implementado como sistema | Locally Validated, com exporters externos preparados |

Targets externos são condicionais à disponibilidade das contas. Se uma conta não existir, o resultado correto é `SKIP_WITH_REASON`, e não uma redução silenciosa do critério.

---

## Success Criteria

- [ ] Um baseline Git contém todos os arquivos versionáveis e nenhum segredo/artefato local conhecido.
- [ ] 100% dos pull requests executam lint, testes unitários e contract tests dos domínios afetados.
- [ ] 100% dos DAGs descobertos importam no Airflow 3.0 com zero `import_errors`.
- [ ] O caminho de CI por domínio conclui em até 20 minutos no p95, excluindo smoke externo manual.
- [ ] 100% dos jobs de CI publicam resultado legível mesmo em falha.
- [ ] 100% das capabilities CAP-01–CAP-10 aparecem no relatório consolidado com nível, evidência e blocker.
- [ ] 0 capabilities sem infraestrutura aparecem como `PASS`; devem aparecer como `SKIP_WITH_REASON`.
- [ ] 100% dos eventos críticos novos carregam `correlation_id`, `event_type`, `occurred_at`, `source` e `schema_version`.
- [ ] Pelo menos 12 métricas operacionais cobrem as sete áreas funcionais e a plataforma.
- [ ] Pelo menos 6 cenários de falha/recovery são automatizados: timeout, rate limit, mensagem inválida, replay, cursor/checkpoint e precondition stale.
- [ ] Pelo menos 5 runbooks possuem trigger, diagnóstico, mitigação, recovery e evidência de exercício.
- [ ] Nenhum token, secret, auth code ou PII de teste aparece nos artefatos/logs de CI.
- [ ] Smoke externo expira após 30 dias e volta a `SKIP_WITH_REASON:STALE_EVIDENCE` até reexecução.
- [ ] Nenhum recurso pago ou permissão externa é criado sem aprovação explícita do usuário.

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|---|---|---|---|---|
| AT-001 | PR limpo | Mudança em um domínio | CI é disparado | Lint, testes e contract tests passam; artefatos são publicados |
| AT-002 | DAG quebrado | Um DAG contém erro de importação | Gate DagBag executa | Job falha e informa arquivo/traceback |
| AT-003 | Credencial ausente | Smoke externo não possui secret necessário | Validador executa | Resultado é `SKIP_WITH_REASON:MISSING_CREDENTIAL`, não `PASS` |
| AT-004 | Evidência expirada | Último smoke externo tem mais de 30 dias | Relatório consolida níveis | Capability não usa o smoke como evidência atual |
| AT-005 | Correlação ponta a ponta | Evento sintético com `correlation_id` | Percorre duas ou mais fases | Logs/eventos derivados preservam o identificador |
| AT-006 | Timeout externo | Adapter recebe timeout | Job executa | Retry é limitado, métrica incrementa e estado recuperável é preservado |
| AT-007 | Rate limit | Adapter recebe 429/`Retry-After` | Job executa | Espera/reagenda segundo política sem duplicar efeito |
| AT-008 | Poison message | Registro viola contrato | Ingestão processa lote | Registro vai à DLQ, válidos continuam e alerta é gerado |
| AT-009 | Replay | Mesmo evento é entregue dez vezes | Consumidor idempotente processa | No máximo um efeito lógico é persistido |
| AT-010 | Cursor/checkpoint | Falha ocorre antes do commit de cursor | Task é repetida | Nenhum item é perdido; duplicações seguem política documentada |
| AT-011 | Precondition stale | Estado mudou após aprovação | Aplicador executa | Ação não é aplicada e alerta/runbook correto é associado |
| AT-012 | Recuperação de scheduler | Stack completo degrada por recursos | Gate isolado executa | DagBag continua validável e limitação fica explícita |
| AT-013 | Secret scanning | Fixture contém secret de teste reconhecível | Scanner executa | CI bloqueia e não publica o valor em claro no resumo |
| AT-014 | Relatório consolidado | Alguns gates passam, falham e pulam | Relatório é gerado | Todos os estados e motivos aparecem sem ambiguidade |
| AT-015 | E2E elegível | Smokes requeridos estão atuais | E2E é solicitado | Executa fluxo; caso contrário bloqueia com lista exata de pré-requisitos |

---

## Observability Requirements

### Common Event Envelope

| Field | Type | Requirement |
|---|---|---|
| `event_id` | UUID/string | Unique per emitted event |
| `correlation_id` | string | Stable across the business flow |
| `event_type` | versioned string | Required |
| `schema_version` | integer | Required, starts at 1 |
| `source` | string | Domain/component name |
| `occurred_at` | UTC timestamp | Required |
| `severity` | enum | `info`, `warning`, `error`, `critical` |
| `attributes` | object | Allowlisted, no secret/PII by default |

### Minimum Metrics

| Area | Metrics |
|---|---|
| Ingestion | records accepted/rejected, DLQ depth, source freshness |
| Processing | rows processed, duration, failure count |
| Self-healing | events diagnosed, rejected proposals, PRs opened, latency |
| Insights | training/inference duration, outliers, drift decisions |
| FinOps | consumption, anomaly count, data-source fallback count |
| RAG | documents/chunks, retrieval latency, RAGAS pass/fail |
| Delivery/HITL | outbox depth, delivery results, decision latency, application results |
| Platform | CI duration/result, DagBag errors, stale evidence count |

### Initial SLOs

| SLO | Target | Window |
|---|---|---|
| CI quality-gate success on unchanged main | >= 95% | Last 20 runs |
| DagBag import availability | 100% | Every main/PR validation |
| No silent event loss in recovery tests | 100% | Every test run |
| Delivery request persisted before external call | 100% | Every run |
| Critical validation report completeness | 100% CAP-01–CAP-10 | Every generated report |

SLOs de produção como disponibilidade 99.9% ficam fora desta fase até existir ambiente contínuo e histórico suficiente.

---

## Evidence Contract

Cada execução de validação produz um registro com:

| Field | Description |
|---|---|
| `capability_id` | CAP-01–CAP-10 |
| `gate` | `unit`, `contract`, `dagbag`, `local_integration`, `external_smoke`, `e2e`, `recovery` |
| `status` | `PASS`, `FAIL`, `SKIP_WITH_REASON` |
| `reason_code` | Obrigatório para skip/fail |
| `environment` | `local`, `ci`, `integration`, `production` |
| `started_at`/`finished_at` | UTC timestamps |
| `commit_sha` | SHA validado; obrigatório após baseline Git |
| `tool_version` | Versão do validador/runtime |
| `artifact_refs` | Logs, reports e métricas sem segredos |
| `expires_at` | Obrigatório para smoke externo |

Reason codes iniciais:

- `MISSING_CREDENTIAL`
- `INFRA_NOT_PROVISIONED`
- `UNSUPPORTED_FREE_TIER`
- `STALE_EVIDENCE`
- `RESOURCE_LIMIT`
- `DEPENDENCY_UNAVAILABLE`
- `ASSERTION_FAILED`
- `CONFIGURATION_ERROR`

---

## Out of Scope

- Microsoft Fabric, Power BI, dbt e Snowflake como novas capacidades de negócio.
- Kubernetes ou multi-cloud deployment.
- SLA de produção 24×7 sem ambiente contínuo.
- Uso de dados pessoais/corporativos reais nos testes.
- Provisionamento automático de recursos pagos.
- Auto-merge ou remoção dos controles HITL.
- Reescrita total dos pipelines existentes apenas para uniformidade estética.

---

## Constraints

| Type | Constraint | Impact |
|---|---|---|
| Repository | Não existe commit inicial; todos os arquivos aparecem como untracked | CI e evidência por SHA não funcionam até o baseline |
| Runtime | Host usa Python 3.13; CI e Airflow usam Python 3.11 | Matriz deve separar host de runtime suportado |
| Docker | Docker Desktop 28.3/Compose 2.39; stack completo já saturou recursos | DagBag e testes por domínio usam containers isolados |
| Cost | Budget recorrente default é zero | Trials/free tiers; qualquer custo exige aprovação explícita |
| Credentials | Disponibilidade externa ainda desconhecida | Smokes condicionais e inventário sem valores secretos |
| Security | Logs/artefatos não podem carregar secrets ou PII | Redação, allowlist e scanners são gates |
| Compatibility | Airflow alvo 3.0 | DagBag usa imagem/versionamento fixado |
| Evidence | Resultados manuais sem SHA não comprovam versão | Após baseline, toda nova evidência exige commit SHA |

---

## Technical Context

| Aspect | Value | Notes |
|---|---|---|
| **Deployment Location** | `platform/`, `scripts/validation/`, `.github/workflows/`, `pipelines/observability/` | Separar plataforma dos domínios funcionais |
| **Existing Assets** | `pyproject.toml`, `requirements-dev.txt`, `quality.yml`, `validate_dagbag.py`, Docker compose | Evoluir, não duplicar |
| **CI Runtime** | Python 3.11 + Airflow 3.0 isolado | Compatível com o alvo, independente do Python 3.13 do host |
| **Telemetry Interface** | Logging estruturado + métricas/exporters desacoplados | Design decide bibliotecas e backend local |
| **IaC Impact** | Local descriptors + templates condicionais | Recursos externos só após inventário/aprovação |
| **Data Impact** | Novo evidence store e schema de eventos | Não altera contratos de negócio existentes sem necessidade |

---

## Environment Inventory Requirements

O DESIGN/BUILD deve gerar um inventário sem valores secretos:

| Environment | Required capabilities | Provisioning status now |
|---|---|---|
| `local` | Python, Docker, Airflow image, Redpanda, PostgreSQL, Delta/SQLite | Parcialmente disponível |
| `ci` | GitHub repo, Actions, cache/artifacts, optional protected environments | Bloqueado pelo baseline Git inexistente |
| `integration-databricks` | Workspace, Unity Catalog, SQL warehouse, Vector Search, MLflow | Unknown/not validated |
| `integration-m365` | Tenant, Entra app, SharePoint, Teams app/bot, mailbox | Unknown/not validated |
| `integration-github-llm` | Test repository, limited token/app, LLM key/budget | Unknown/not validated |

Inventory records only `configured: true/false`, owner and last validation date. Secret values are never read into reports.

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|---|---|---|---|
| A-001 | O usuário pode criar ou selecionar um repositório Git para o baseline | CI externo permanece bloqueado | [ ] |
| A-002 | GitHub Actions está disponível no repositório escolhido | Será necessário runner/local CI alternativo | [ ] |
| A-003 | Pelo menos um ambiente externo poderá ser provisionado durante a fase | Algumas capabilities permanecerão em nível local | [ ] |
| A-004 | Containers isolados permanecem estáveis no Docker local | Será necessário executar DagBag somente no CI |
| A-005 | OpenTelemetry/logging estruturado cabe sem reescrever todos os jobs | Instrumentação pode precisar de rollout incremental maior | [ ] |
| A-006 | O limite de 20 min por job é viável com cache e matriz por domínio | Jobs pesados precisarão de tiers ou execução agendada | [ ] |
| A-007 | Budget recorrente zero é requisito atual | Qualquer campanha paga deve parar e solicitar aprovação | [x] Derivado das fases anteriores |

---

## Clarity Score Breakdown

| Element | Score | Notes |
|---|---:|---|
| Problem | 3 | Lacuna entre implementação e prova operacional está explícita |
| Users | 3 | Operação, desenvolvimento, auditoria e avaliação contemplados |
| Goals | 3 | Prioridades e níveis de maturidade acionáveis |
| Success | 3 | Métricas, SLOs, evidence contract e 15 acceptance tests |
| Scope | 2 | Disponibilidade das contas externas ainda precisa de inventário |
| **Total** | **14/15** | Ready for Design |

---

## Open Questions

Nenhuma pergunta bloqueia o DESIGN local. As seguintes decisões bloqueiam apenas provisionamento/validação externa e devem permanecer configuráveis:

1. Qual repositório remoto receberá o baseline e quais regras de branch protection serão permitidas.
2. Quais contas Databricks e Microsoft 365 estão disponíveis.
3. Qual provedor/back-end receberá métricas localmente e no ambiente externo.
4. Qual teto de gasto, se diferente de zero, será autorizado para uma campanha externa.

O BUILD não está autorizado por este documento a criar repositório remoto, recursos cloud, permissões administrativas ou custos.

---

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-17 | Codex + usuário | Definição inicial baseada no brainstorm e no inventário real do workspace |

---

## Next Step

**Ready for:** `/ship .claude/sdd/features/DEFINE_FASE6_PLATFORM_OBSERVABILITY_VALIDATION.md`
