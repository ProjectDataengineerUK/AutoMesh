# DEFINE: Fase 5 — Entrega Segura e Human-in-the-Loop

> Entregar decisões e relatórios pelo ecossistema Microsoft e registrar aprovações humanas auditáveis, idempotentes e separadas da aplicação de ações críticas.

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | FASE5_ENTREGA_HITL |
| **Date** | 2026-08-14 |
| **Author** | Codex + usuário |
| **Status** | Built (Infrastructure Validation Pending) |
| **Clarity Score** | 14/15 |

---

## Problem Statement

As Fases 2-4 geram propostas de correção, promoção de modelo, alertas FinOps e relatórios, mas o decisor precisa procurar essas informações no GitHub ou Airflow e não existe um registro uniforme da decisão. A Fase 5 precisa entregar o contexto pelo Microsoft Teams, usar Outlook como fallback e transformar a resposta humana em um evento auditável, sem permitir merge automático de código ou execução não autorizada.

---

## Target Users

| User | Role | Pain Point |
|---|---|---|
| Responsável técnico | Revisor de PR/contrato | Precisa receber causa, impacto, evidência e link do PR sem acompanhar continuamente o Airflow |
| Responsável de MLOps | Aprovador de modelo | Precisa aprovar ou rejeitar uma promoção e comprovar quem decidiu, quando e sobre qual versão |
| Gestor/FinOps | Dono do custo | Precisa receber anomalias priorizadas e registrar uma decisão sem conceder acesso ao ambiente de dados |
| Auditor/segurança | Controle e conformidade | Precisa reconstruir a cadeia evento → notificação → decisão → aplicação, incluindo falhas e retries |
| Operador da plataforma | Sustentação | Precisa reprocessar entregas com falha sem duplicar mensagens ou ações |

---

## Goals

| Priority | Goal |
|---|---|
| **MUST** | Persistir toda solicitação de decisão em uma outbox antes de tentar entregá-la externamente |
| **MUST** | Enviar Adaptive Card no Teams com contexto mínimo, risco, evidências, ação proposta e correlação com evento/PR |
| **MUST** | Registrar aprovação, rejeição ou expiração em um ledger imutável de decisões |
| **MUST** | Garantir idempotência: uma mesma solicitação ou callback não pode gerar entrega ou aplicação duplicada |
| **MUST** | Autenticar e autorizar o ator da decisão e rejeitar callbacks expirados, adulterados ou repetidos |
| **MUST** | Separar decisão de aplicação: callback registra intenção; um worker aplica apenas ações permitidas e revalida o estado esperado |
| **MUST** | Manter merge de código/contrato exclusivamente no GitHub, sem merge automático pela Fase 5 |
| **SHOULD** | Usar Outlook como fallback após esgotar retries do Teams |
| **SHOULD** | Aplicar promoção de alias MLflow após aprovação válida e registrar o resultado |
| **SHOULD** | Expor métricas de entrega, latência de decisão, expiração, retry e falha de aplicação |
| **COULD** | Entregar relatórios informativos sem botões quando nenhuma decisão for necessária |

---

## Success Criteria

- [ ] 100% das solicitações são persistidas na outbox antes da primeira chamada ao Graph.
- [ ] 100% das notificações e decisões possuem `notification_id`, `decision_id` quando aplicável e `correlation_id`.
- [ ] Reprocessar a mesma solicitação 10 vezes produz no máximo uma notificação ativa por canal.
- [ ] Repetir o mesmo callback 10 vezes produz uma única transição de decisão e no máximo uma aplicação.
- [ ] 100% dos callbacks sem identidade autorizada, expirados ou com payload incompatível são rejeitados sem alterar o estado.
- [ ] 0 merges de PR são executados pelo código da Fase 5.
- [ ] 100% das rejeições e expirações impedem a execução do aplicador.
- [ ] Falhas transitórias do Graph são tentadas no máximo 3 vezes com backoff; após isso, notificações decisórias tentam Outlook uma vez.
- [ ] Promoção MLflow aprovada só ocorre se modelo, versão e alias atual ainda coincidirem com o estado apresentado ao humano.
- [ ] Testes automatizados cobrem todas as transições permitidas e proibidas da máquina de estados.
- [ ] O nível `Infrastructure Validated` exige ao menos uma entrega e uma decisão reais no tenant Microsoft 365 de teste.

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|---|---|---|---|---|
| AT-001 | Entrega Teams | Uma solicitação `pending` persistida | O dispatcher recebe sucesso do Graph | Grava `teams_message_id`, incrementa tentativas e muda para `delivered` |
| AT-002 | Retry idempotente | A mesma solicitação já está `delivered` | O dispatcher é executado novamente | Não chama o Graph e retorna o registro existente |
| AT-003 | Aprovação válida | Decisão `pending`, não expirada, ator autorizado | Callback `approve` é recebido | Registra evento `approved` uma vez e agenda aplicação separada |
| AT-004 | Rejeição válida | Decisão `pending`, ator autorizado | Callback `reject` contém motivo | Registra `rejected`; nenhuma aplicação é criada |
| AT-005 | Callback repetido | A decisão já está `approved` | O mesmo callback chega novamente | Responde idempotentemente e não reaplica a ação |
| AT-006 | Callback adulterado | Recurso/versão não corresponde ao payload persistido | Callback é recebido | Rejeita com `payload_mismatch` e não altera a decisão |
| AT-007 | Decisão expirada | `expires_at` está no passado | Aprovação chega | Registra tentativa recusada; estado permanece `expired` |
| AT-008 | Falha do Teams | Graph falha nas três tentativas | Dispatcher esgota retry | Agenda Outlook uma vez e mantém evidência das falhas |
| AT-009 | Promoção de modelo | Aprovação válida e precondições do registry conferem | Aplicador executa | Move o alias para a versão aprovada e registra `applied` |
| AT-010 | Estado do modelo mudou | Alias/versão divergiu desde a notificação | Aplicador executa | Não promove; registra `stale_precondition` para nova revisão |
| AT-011 | PR de código | PR automático aguarda revisão | Humano aprova no Adaptive Card | A decisão é registrada e o cartão aponta para o GitHub; nenhum merge é chamado |
| AT-012 | Relatório informativo | Relatório RAG aprovado não requer decisão | Dispatcher envia | Entrega cartão sem ações e registra confirmação de envio |

---

## Out of Scope

- Merge automático de PR ou bypass de branch protection.
- Execução de código ou SQL fornecido no callback.
- Rebalanceamento de carteira ou qualquer operação financeira real.
- Interface web administrativa própria.
- Implantação completa de Power BI/Fabric ou atualização de modelo semântico.
- Substituição do RBAC do Microsoft 365, GitHub, MLflow ou Unity Catalog.
- Provisionamento de tenant corporativo de produção.
- Aprovação por texto livre interpretado por LLM; apenas ações estruturadas são aceitas.

---

## Constraints

| Type | Constraint | Impact |
|---|---|---|
| Security | OAuth2 client credentials não identifica por si só o humano que clicou | O callback precisa de identidade verificável separada e allowlist/grupo de aprovadores |
| Security | Segredos não podem entrar em DAG, payload, Delta ou log | Credenciais vêm de secret backend/variáveis e devem ser mascaradas |
| Governance | Código só é aprovado/mesclado no GitHub | Adaptive Card informa e registra intenção, mas não chama merge |
| Reliability | Airflow e Graph usam entrega pelo menos uma vez | Outbox, chaves idempotentes e compare-and-set são obrigatórios |
| Data | Delta local não oferece as mesmas garantias de concorrência de um serviço transacional de callback | DESIGN deve isolar interface de storage e documentar a estratégia de concorrência |
| Resource | Tenant Microsoft 365 e endpoint público ainda não foram provisionados | Build pode chegar a `Implemented`; validação externa continua um gate separado |
| Compatibility | Projeto usa Python 3.11 no CI e Airflow 3.0 | Código e dependências precisam permanecer compatíveis com esse baseline |
| Cost | Sem infraestrutura continuamente cara | Polling/reconciliação e serviços serverless são preferidos |

---

## Technical Context

| Aspect | Value | Notes |
|---|---|---|
| **Deployment Location** | `pipelines/delivery/` | Novo domínio; evita misturar integração de entrega com ingestão RAG |
| **Integration Reuse** | `pipelines/rag/common/graph_client.py`, `pipelines/self_healing/`, `pipelines/insights/model_registry_state.yaml` | Extrair autenticação Graph comum sem duplicar segredos |
| **Orchestration** | Airflow 3.0 | Dispatcher, expiração, reconciliação e aplicação |
| **External APIs** | Microsoft Graph, GitHub links, MLflow Registry | GitHub é somente referência; MLflow permite ação controlada |
| **Persistence** | Interfaces de outbox/decision ledger; Delta para MVP local | Implementação deve permitir backend transacional no callback real |
| **IaC Impact** | New resources | App registration/permissões, endpoint HTTPS, secret storage e possivelmente Azure Function/API Management |
| **Observability** | Logs estruturados + métricas por estado | Sem dados pessoais ou tokens nos logs |

---

## Data Contract

### Source Inventory

| Source | Type | Volume | Freshness | Owner |
|---|---|---|---|---|
| `self_healing_events` | Delta | Baixo, por evento | Até 5 min | Plataforma |
| `self_healing_rejections` | Delta | Baixo | Até 5 min | Plataforma |
| `gold.market_insights`/relatórios RAG | Delta/evento | Baixo | Até 15 min | Insights/RAG |
| `model_registry_state.yaml` + MLflow | Git/Registry | Baixo | Sob demanda | MLOps |

### Notification Outbox

| Column | Type | Constraints | PII? |
|---|---|---|---|
| `notification_id` | string/UUID | PK, immutable | No |
| `correlation_id` | string | Required, indexed | No |
| `decision_id` | string/UUID | Nullable para informativo | No |
| `notification_type` | enum | `pr_review`, `model_promotion`, `finops`, `report` | No |
| `recipient_ref` | string | Required; identificador lógico, não segredo | Yes |
| `channel` | enum | `teams`, `outlook` | No |
| `payload` | JSON/string | Schema versionado; sem token/segredo | Potentially |
| `idempotency_key` | string | Unique | No |
| `status` | enum | `pending`, `delivering`, `delivered`, `retryable`, `failed` | No |
| `attempt_count` | integer | >= 0 | No |
| `external_message_id` | string | Nullable | No |
| `created_at`/`updated_at` | timestamp UTC | Required | No |

### Decision Ledger

| Column | Type | Constraints | PII? |
|---|---|---|---|
| `decision_id` | string/UUID | PK, immutable | No |
| `correlation_id` | string | Required | No |
| `action_type` | enum | `review_pr`, `promote_model`, `ack_finops` | No |
| `resource_ref` | string | Required | No |
| `expected_state` | JSON/string | Required para ação mutável | No |
| `actor_id` | string | Obrigatório após decisão | Yes |
| `decision` | enum | `pending`, `approved`, `rejected`, `expired` | No |
| `reason` | string | Obrigatório para rejeição | Potentially |
| `expires_at` | timestamp UTC | Required | No |
| `decided_at` | timestamp UTC | Nullable até decisão | No |
| `application_status` | enum | `not_applicable`, `pending`, `applied`, `failed`, `stale_precondition` | No |

### State Machines

```text
notification: pending -> delivering -> delivered
                              |-> retryable -> delivering
                              |-> failed -> outlook fallback

decision: pending -> approved -> application pending -> applied
              |          |-> failed/stale_precondition
              |-> rejected
              |-> expired
```

Estados terminais não podem retornar a `pending`. Cada transição precisa registrar timestamp, causa e identificador de execução.

### Freshness SLAs

| Layer | Target | Measurement |
|---|---|---|
| Outbox | Persistida em até 1 min após seleção do evento | `created_at - source_detected_at` |
| Teams | Primeira tentativa em até 5 min | `first_attempt_at - created_at` |
| Outlook fallback | Até 5 min após esgotar Teams | `fallback_at - last_teams_attempt_at` |
| Aplicação aprovada | Até 5 min após decisão, salvo precondição inválida | `applied_at - decided_at` |

### Completeness Metrics

- 100% das chamadas externas possuem registro anterior na outbox.
- 100% das decisões possuem ator e correlação.
- Zero ações aplicadas sem decisão `approved` válida.
- Zero chaves de idempotência duplicadas.

### Lineage Requirements

- Evento de origem → outbox → mensagem externa → decisão → tentativa de aplicação.
- Promoção de modelo registra nome, versão, alias anterior, alias esperado e alias resultante.
- PR registra URL e SHA/base observados, sem armazenar token.

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|---|---|---|---|
| A-001 | O tenant permite a modalidade escolhida de envio de Adaptive Cards | Pode exigir bot/Teams app em vez de Graph direto | [ ] |
| A-002 | O callback fornece identidade verificável do usuário | Sem isso, Teams fica apenas como notificação e a decisão permanece no GitHub/portal autenticado | [ ] |
| A-003 | Existe um grupo/allowlist de aprovadores por tipo de ação | DESIGN precisará introduzir cadastro de política | [ ] |
| A-004 | Azure Function ou serviço equivalente pode expor HTTPS com baixo custo | Callback teria de usar polling de uma fonte de decisão alternativa | [ ] |
| A-005 | MLflow/Unity Catalog permite alterar alias com identidade de serviço limitada | Promoção continuará manual, apenas auditada | [ ] |
| A-006 | Delta é suficiente para outbox local e testes de baixa concorrência | Backend transacional será necessário antes da produção | [x] Para MVP local apenas |
| A-007 | Teams é o canal principal desejado e Outlook é fallback | Alteração inverte templates e política de retry | [x] Decisão do brainstorm |

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---|---|---|
| Problem | 3 | Última milha e risco estão claramente delimitados |
| Users | 3 | Atores técnicos, negócio, auditoria e operação identificados |
| Goals | 3 | MUST/SHOULD/COULD com separação decisão/aplicação |
| Success | 3 | Métricas e acceptance tests mensuráveis |
| Scope | 2 | Forma exata da integração interativa do Teams depende de validação do tenant |
| **Total** | **14/15** | Acima do mínimo 12/15 |

---

## Open Questions

Nenhuma questão bloqueia o DESIGN local. A-001 a A-005 precisam aparecer como riscos explícitos e interfaces substituíveis no DESIGN; elas bloqueiam `Infrastructure Validated`, não `Implemented`.

Antes do build externo, confirmar:

1. O app/bot do Teams será o mecanismo de cartões acionáveis; confirmar instalação e políticas no tenant.
2. Qual grupo Entra ID aprova cada tipo de ação.
3. Onde o endpoint HTTPS e os segredos serão hospedados.

---

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-14 | Codex + usuário | Definição inicial derivada do brainstorm e da auditoria das Fases 1-4 |

---

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_FASE5_ENTREGA_HITL.md`
