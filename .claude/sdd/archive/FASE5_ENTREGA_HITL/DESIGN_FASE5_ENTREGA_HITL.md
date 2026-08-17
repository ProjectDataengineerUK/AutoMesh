# DESIGN: Fase 5 — Entrega Segura e Human-in-the-Loop

> Arquitetura de outbox, Teams bot, ledger de decisões e aplicação controlada para fechar o ciclo das Fases 2-4.

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | FASE5_ENTREGA_HITL |
| **Date** | 2026-08-14 |
| **Status** | Built (Infrastructure Validation Pending) |
| **Source** | `DEFINE_FASE5_ENTREGA_HITL.md` |
| **Target Runtime** | Python 3.11, Airflow 3.0, Teams app/bot, Microsoft Graph |

---

## Architecture Overview

```text
Fases 2-4                         pipelines/delivery

self_healing_events ─┐       ┌─> notification_outbox ─> dispatcher DAG
model promotion ─────┼─>     │                              |
FinOps anomaly ──────┼─> request builder                    +─> Teams bot proactive card
RAG report ──────────┘       │                              |       |
                             └─> decision_ledger <──────────┘       v
                                                              Action.Execute
                                                                    |
                                                                    v
                                                         Teams bot invoke handler
                                                                    |
                                                                    v
                                                   authorize + compare-and-set decision
                                                                    |
                                                        approved? ──┴── rejected/expired
                                                            |
                                                            v
                                                     action_applications
                                                            |
                                                   application worker DAG
                                                  /                       \
                                      model alias promotion       PR link only/no merge

Teams delivery exhausted ─> Outlook fallback via Microsoft Graph Mail.Send
```

O Graph não será usado como receptor de cliques. Cartões com `Action.Execute` são enviados por um app/bot do Teams e a ação retorna ao bot como atividade `adaptiveCard/action`. O Graph será usado para instalar o app proativamente quando autorizado e para enviar o fallback por Outlook.

---

## Components

| Component | Responsibility |
|---|---|
| `models.py` | Enums e modelos validados de notificação, decisão, transição e aplicação |
| `storage.py` | Protocolos de outbox/ledger/application store e implementação Delta local |
| `idempotency.py` | Chaves determinísticas e compare-and-set de transições |
| `request_builder.py` | Converte eventos existentes em solicitações sem executar I/O externo |
| `cards.py` | Renderiza Adaptive Cards versionados e sem segredos |
| `teams_client.py` | Envia mensagens proativas usando referência de conversa previamente registrada |
| `graph_mail.py` | Envia fallback por Outlook via Graph com mailbox limitada por política |
| `dispatcher.py` | Reserva item da outbox, entrega, faz retry e agenda fallback |
| `bot/handler.py` | Valida atividade do Teams, autoriza ator e registra decisão idempotente |
| `authorization.py` | Política ator/grupo × tipo de ação; deny by default |
| `applications.py` | Aplica ações permitidas após revalidar precondições |
| `reconciler.py` | Expira decisões e recupera leases abandonados |
| DAGs | Seleção de eventos, dispatch, aplicação e reconciliação |

---

## Key Decisions

### Decision 1: Teams app/bot para cartões interativos

| Attribute | Value |
|---|---|
| **Status** | Accepted |
| **Reason** | `Action.Execute` retorna uma invoke activity ao bot, preservando identidade e protocolo do Teams |

O dispatcher envia mensagens proativas pelo bot. O app precisa estar instalado para o usuário ou equipe; o Graph pode instalar o app previamente quando o administrador conceder as permissões necessárias. A referência de conversa é persistida após eventos de instalação/conversa e reutilizada.

Alternativas rejeitadas:

1. Postar cartão via Graph e receber clique num webhook genérico — não corresponde ao protocolo de Universal Actions.
2. Power Automate como núcleo — reduz controle de idempotência, testes e versionamento do projeto.
3. Link público com token na URL — maior risco de encaminhamento e replay.

### Decision 2: Outbox antes de qualquer efeito externo

| Attribute | Value |
|---|---|
| **Status** | Accepted |

O request builder apenas grava outbox e ledger. O dispatcher é o único componente que chama Teams/Graph. `idempotency_key` é derivada de `notification_type + resource_ref + resource_version + recipient_ref + channel`.

### Decision 3: Bot registra decisão; worker aplica ação

| Attribute | Value |
|---|---|
| **Status** | Accepted |

O handler nunca promove modelo, altera arquivo ou chama merge. Ele valida, autoriza e realiza compare-and-set `pending -> approved|rejected`. Uma aplicação separada só consome decisões `approved`.

### Decision 4: GitHub continua sendo autoridade para código

| Attribute | Value |
|---|---|
| **Status** | Accepted |

Uma aprovação no Teams registra ciência/intenção e oferece `Action.OpenUrl` para o PR. A Fase 5 não chama endpoints de review ou merge. Branch protection e aprovação do GitHub permanecem obrigatórias.

### Decision 5: Promoção MLflow usa precondição otimista

| Attribute | Value |
|---|---|
| **Status** | Accepted |

O ledger guarda modelo, versão candidata, alias e versão observada no momento da solicitação. Antes de aplicar, o worker relê o registry. Divergência resulta em `stale_precondition`; nunca sobrescreve uma decisão posterior.

### Decision 6: Delta é backend local, não contrato de produção

| Attribute | Value |
|---|---|
| **Status** | Accepted with constraint |

Interfaces de storage isolam o domínio. Delta atende testes e execução sequencial local. Antes de múltiplas instâncias do bot em produção, o ledger deve usar backend com unique constraints e compare-and-set transacional, como PostgreSQL/Azure SQL ou Cosmos DB com ETag.

### Decision 7: Outlook é fallback informativo

| Attribute | Value |
|---|---|
| **Status** | Accepted |

Após três falhas transitórias no Teams, o dispatcher envia um e-mail com contexto e link seguro. O MVP não aceita decisão por resposta de e-mail; isso evita spoofing e interpretação ambígua. `Mail.Send` de aplicação deve ser limitado a mailbox dedicada por política administrativa.

### Decision 8: Política deny-by-default e payload mínimo

| Attribute | Value |
|---|---|
| **Status** | Accepted |

Cada `action_type` declara grupos/atores permitidos. O cartão carrega somente `decision_id`, `verb` e uma versão do schema; dados autoritativos são relidos do ledger. Valores de recurso enviados pelo cliente nunca são confiáveis.

---

## File Manifest

### Production

| # | File | Purpose |
|---|---|---|
| 1 | `pipelines/delivery/__init__.py` | Pacote da Fase 5 |
| 2 | `pipelines/delivery/requirements.txt` | Dependências do domínio |
| 3 | `pipelines/delivery/config/delivery_config.yaml` | Defaults não secretos e versões de schema |
| 4 | `pipelines/delivery/common/models.py` | Modelos e enums |
| 5 | `pipelines/delivery/common/storage.py` | Protocolos + Delta MVP |
| 6 | `pipelines/delivery/common/idempotency.py` | Geração/validação de chaves |
| 7 | `pipelines/delivery/common/authorization.py` | Política de aprovadores |
| 8 | `pipelines/delivery/common/cards.py` | Templates Adaptive Card |
| 9 | `pipelines/delivery/common/teams_client.py` | Mensagem proativa pelo bot |
| 10 | `pipelines/delivery/common/graph_mail.py` | Outlook fallback |
| 11 | `pipelines/delivery/jobs/request_builder.py` | Eventos → outbox/ledger |
| 12 | `pipelines/delivery/jobs/dispatcher.py` | Entrega, retry e fallback |
| 13 | `pipelines/delivery/jobs/applications.py` | Aplicação controlada |
| 14 | `pipelines/delivery/jobs/reconciler.py` | Expiração e leases |
| 15 | `pipelines/delivery/bot/handler.py` | Handler `adaptiveCard/action` |
| 16 | `pipelines/delivery/bot/app.py` | Entry point HTTP do app/bot |
| 17 | `pipelines/delivery/dags/dag_delivery_collect.py` | Seleção incremental de eventos |
| 18 | `pipelines/delivery/dags/dag_delivery_dispatch.py` | Dispatch periódico |
| 19 | `pipelines/delivery/dags/dag_delivery_apply.py` | Aplicador periódico |
| 20 | `pipelines/delivery/dags/dag_delivery_reconcile.py` | Expiração/recuperação |

### Tests and infrastructure descriptors

| # | File | Purpose |
|---|---|---|
| 21 | `pipelines/delivery/tests/test_models.py` | Schemas e invariantes |
| 22 | `pipelines/delivery/tests/test_storage.py` | Unique key, CAS e estados terminais |
| 23 | `pipelines/delivery/tests/test_cards.py` | Payload mínimo e ações corretas |
| 24 | `pipelines/delivery/tests/test_dispatcher.py` | Retry, idempotência e fallback |
| 25 | `pipelines/delivery/tests/test_handler.py` | Autorização, replay e mismatch |
| 26 | `pipelines/delivery/tests/test_applications.py` | Promoção e stale precondition |
| 27 | `pipelines/delivery/tests/test_reconciler.py` | Expiração e lease recovery |
| 28 | `pipelines/delivery/tests/test_dags_integrity.py` | DagBag e IDs esperados |
| 29 | `pipelines/delivery/contracts/notification_outbox.contract.yaml` | Contrato da outbox |
| 30 | `pipelines/delivery/contracts/decision_ledger.contract.yaml` | Contrato do ledger |
| 31 | `pipelines/delivery/contracts/action_applications.contract.yaml` | Contrato das aplicações |
| 32 | `pipelines/delivery/infra/README.md` | Recursos, permissões e validação externa |
| 33 | `pipelines/delivery/infra/teams-app-manifest.json` | Manifesto parametrizado do app |

### Existing files modified

| File | Change |
|---|---|
| `docker-compose.local.yml` | Paths locais e variáveis não secretas da Fase 5 |
| `requirements-dev.txt` | Incluir `pipelines/delivery/requirements.txt` |
| `CLAUDE.md` | Estado e comandos da Fase 5 após build |
| `pipelines/rag/common/graph_client.py` | Extrair autenticação compartilhada apenas se não quebrar API existente |

---

## Code Patterns

### Pattern 1: estados explícitos e transições fechadas

```python
ALLOWED_DECISION_TRANSITIONS = {
    "pending": {"approved", "rejected", "expired"},
    "approved": set(),
    "rejected": set(),
    "expired": set(),
}

def transition(current: str, target: str) -> None:
    if target not in ALLOWED_DECISION_TRANSITIONS[current]:
        raise InvalidTransition(f"{current}->{target}")
```

O storage implementa compare-and-set com versão/revision. Ler e depois sobrescrever sem condição é proibido no handler.

### Pattern 2: idempotência derivada de fatos estáveis

```python
def notification_key(kind: str, resource: str, version: str, recipient: str, channel: str) -> str:
    canonical = "|".join((kind, resource, version, recipient, channel))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

Timestamp de execução, retry count e conteúdo renderizado não entram na chave.

### Pattern 3: handler não confia no payload do cartão

```python
async def handle_execute(activity: dict) -> dict:
    actor = verified_actor(activity)
    decision_id = activity["value"]["action"]["data"]["decision_id"]
    verb = activity["value"]["action"]["verb"]
    decision = store.get_decision(decision_id)
    authorize(actor, decision.action_type)
    store.compare_and_set_decision(decision_id, expected="pending", target=verb, actor=actor)
    return render_current_state(store.get_decision(decision_id))
```

O handler não aceita `resource_ref`, versão do modelo, URL de PR ou destinatário como autoridade vinda do cliente.

### Pattern 4: lease de outbox

```text
pending/retryable -> delivering (lease_owner, lease_until)
delivering -> delivered
delivering -> retryable (transient error, attempt < 3)
delivering -> failed (permanent error or attempts exhausted)
```

O reconciler devolve para `retryable` leases expirados. O dispatcher confirma o estado antes de enviar.

### Pattern 5: aplicação com precondição

```python
current = registry.get_alias(model_name, alias)
if current.version != expected_alias_version:
    return ApplicationResult.STALE_PRECONDITION
registry.set_alias(model_name, alias, approved_version)
```

### Pattern 6: erros externos tipados

```text
2xx                         -> success
408/429/5xx/network timeout -> retryable
400/401/403/404             -> permanent/configuration error
```

Respeitar `Retry-After` quando presente. Nunca registrar bearer token ou payload OAuth.

---

## Data Flow

1. Collector lê eventos após o watermark efetivamente processado.
2. Request builder normaliza o evento e calcula a chave idempotente.
3. Storage cria outbox e, quando aplicável, decisão `pending` atomicamente ou retorna o registro existente.
4. Dispatcher adquire lease e renderiza o cartão a partir do estado persistido.
5. Teams client envia mensagem proativa usando conversation reference conhecida.
6. Sucesso grava identificador externo; falha transitória agenda retry; falha final agenda Outlook.
7. Usuário executa `approve` ou `reject` no cartão.
8. Teams envia `adaptiveCard/action` ao bot.
9. Handler valida protocolo/identidade, relê o ledger, autoriza e faz compare-and-set.
10. Aprovação cria aplicação pendente apenas para tipos com aplicador; rejeição termina o fluxo.
11. Worker relê decisão e recurso, verifica precondições e aplica.
12. Todas as transições são registradas com correlação e métricas.

---

## Integration Points

| Integration | Interface | Authentication | Failure policy |
|---|---|---|---|
| Teams proactive messaging | Teams app/bot SDK/protocol | Identidade do bot | Retry 3x; Outlook fallback |
| Teams actions | `adaptiveCard/action` invoke | Validação do canal + identidade do ator/SSO | Deny by default; no retry client-side assumed |
| Graph app installation | `/users/{id}/teamwork/installedApps` | Application permission com admin consent | Config error if app not in catalog |
| Outlook | Graph `sendMail` | `Mail.Send` application limitado por policy | Uma tentativa de fallback + registro |
| MLflow Registry | `MlflowClient` | Service identity/secret backend | Precondition + no blind overwrite |
| GitHub | URL já criada pela Fase 2 | Nenhuma chamada mutável | Usuário revisa no GitHub |
| Airflow | DAGs periódicos | Ambiente interno | Retries e callbacks existentes |

Referências oficiais verificadas em 2026-08-14:

- `https://learn.microsoft.com/microsoftteams/platform/bots/how-to/conversations/send-proactive-messages`
- `https://learn.microsoft.com/microsoftteams/platform/graph-api/proactive-bots-and-messages/graph-proactive-bots-and-messages`
- `https://learn.microsoft.com/microsoftteams/platform/task-modules-and-cards/cards/universal-actions-for-adaptive-cards/authentication-flow-in-universal-action-for-adaptive-cards`
- `https://learn.microsoft.com/microsoftteams/platform/task-modules-and-cards/cards/universal-actions-for-adaptive-cards/sso-adaptive-cards-universal-action`
- `https://learn.microsoft.com/graph/permissions-reference#mail-send`

---

## Testing Strategy

| Level | Scope | Technique | Gate |
|---|---|---|---|
| Unit | Models, transitions, keys, authorization, cards | Pure pytest | All state branches |
| Storage contract | Outbox/ledger/application behavior | Shared test suite against Delta MVP | Idempotency and CAS semantics |
| Component | Dispatcher/handler/applicator | Fake clients + deterministic clock | AT-001–AT-012 |
| DAG | Imports and dependencies | Airflow DagBag | Zero import errors |
| Local integration | Delta + mocked HTTP/bot adapter | Docker/Airflow | Retry and watermark verified |
| External smoke | Tenant de teste + Teams app + mailbox | One real notification and decision | Required for Infrastructure Validated |
| MLflow smoke | Registry de teste | Approved/stale cases | Required before enabling promotion |

Security tests must include:

- Unknown actor and wrong group.
- Missing/invalid activity identity.
- Replayed invoke.
- Decision expired between read and write.
- Client payload attempting to replace resource/version.
- Log assertions proving token/secret absence.
- Concurrent approvals with exactly one winner.

---

## Error Handling

| Failure | Behavior | User-visible result |
|---|---|---|
| Teams app not installed | Mark configuration failure; optionally request approved proactive install | Outlook fallback with setup warning |
| Teams 429/5xx | Retry respecting backoff/`Retry-After` | Pending/retrying |
| Graph Mail.Send forbidden | Permanent failure with correlation ID | Operator alert; no silent drop |
| Unauthorized actor | No state change; audit denied attempt | Card/error response |
| Duplicate callback | Return current state | No duplicate application |
| Expired decision | Transition/retain `expired` | Updated expired card |
| Storage conflict | Reload and return winner | Idempotent response |
| MLflow precondition changed | `stale_precondition` | New review required |
| Application exception | `failed`, bounded retry only if classified transient | Operator alert |

---

## Configuration

Non-secret settings:

```yaml
schema_version: 1
delivery:
  max_attempts: 3
  lease_seconds: 120
  decision_ttl_hours: 24
  teams_primary: true
  outlook_fallback: true
authorization:
  review_pr: ["automesh-code-reviewers"]
  promote_model: ["automesh-ml-approvers"]
  ack_finops: ["automesh-finops"]
```

Secrets/identifiers come from the runtime secret backend or environment:

- `TEAMS_APP_ID`
- `TEAMS_APP_TENANT_ID`
- bot credential/managed identity configuration
- `GRAPH_CLIENT_ID`, `GRAPH_TENANT_ID`, `GRAPH_CLIENT_SECRET` for local MVP only
- `GRAPH_SENDER_MAILBOX`
- storage and MLflow credentials

Production should prefer managed identity/certificate over client secret where supported.

---

## Security Considerations

- Least-privilege application permissions and admin consent documented before deployment.
- Teams app must be in the organizational catalog before proactive installation.
- `Mail.Send` application access restricted to a dedicated sender mailbox.
- Bot activities validated using the supported Teams SDK/authentication middleware; no custom JWT parsing.
- Authorization checks immutable server-side policy, not values in the card.
- PII fields minimized and excluded from logs; retention policy required for actor identifiers and reasons.
- Every mutable action requires an expected-state precondition.
- No secrets, auth codes or bearer tokens in Delta, XCom, card payload or exception messages.
- CI scans dependencies/secrets before deployment; branch protection remains required.

---

## Observability

Structured events:

- `notification.created`
- `notification.delivery_attempted`
- `notification.delivered`
- `notification.fallback_sent`
- `decision.approved|rejected|expired|denied`
- `application.applied|failed|stale_precondition`

Metrics:

| Metric | Type | Alert suggestion |
|---|---|---|
| `delivery_outbox_depth` | Gauge | > 0 older than 10 min |
| `delivery_attempts_total{channel,result}` | Counter | Error ratio > 10%/15 min |
| `decision_latency_seconds` | Histogram | p95 > decision TTL warning threshold |
| `decision_denied_total{reason}` | Counter | Any spike |
| `application_total{type,result}` | Counter | Any permanent failure |
| `lease_recovered_total` | Counter | > 0 repeated |

Logs always include `correlation_id`; they never include the full card, e-mail body, token or free-form rejection reason.

---

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-14 | Codex + usuário | Design inicial; bot/Universal Actions escolhido após validação na documentação Microsoft |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_FASE5_ENTREGA_HITL.md`

Build local deve entregar `Implemented`. O status `Infrastructure Validated` permanece bloqueado até tenant, app/bot e storage transacional de teste serem provisionados.
