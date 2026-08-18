# DEFINE: Fase 8 — Validação Externa e Readiness Databricks

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | FASE8_EXTERNAL_VALIDATION |
| **Date** | 2026-08-18 |
| **Status** | ✅ Complete (Defined) |
| **Source** | `BRAINSTORM_FASE8_EXTERNAL_VALIDATION.md` |

## Objective

Entregar uma validação externa segura, repetível e opt-in para os artefatos Databricks produzidos nas Fases 1–7, sem exigir workspace cloud para os testes locais.

## Users and Outcomes

| User | Outcome |
|---|---|
| Data/Platform Engineer | Preflight claro e execução idempotente em workspace de teste |
| Operations | Evidência de execução, freshness, qualidade e reconciliação |
| Security/Reviewer | Nenhum segredo exposto; ações externas auditáveis |

## Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | Detectar autenticação, host, catálogo, schema e permissões antes de mutações | Must |
| FR-002 | Carregar configuração apenas de env/secrets e validar ausência de valores inseguros | Must |
| FR-003 | Executar em modo `preflight`, `dry-run` ou `publish` explicitamente selecionado | Must |
| FR-004 | Publicar os quatro produtos Gold e os manifests SQL/Lakeview da Fase 7 | Must |
| FR-005 | Ser idempotente e registrar objetos criados/atualizados | Must |
| FR-006 | Executar reconciliação contra fixtures e contratos locais | Must |
| FR-007 | Gerar relatório JSON/Markdown com commit, timestamp, gates e evidências | Must |
| FR-008 | Retornar `SKIP_EXTERNAL` quando pré-condições não forem atendidas, sem falha falsa | Must |
| FR-009 | Permitir tolerância configurável para diferenças de amostra e freshness | Should |

## Non-Functional Requirements

- Nenhum token, senha, connection string ou payload sensível em logs, fixtures ou relatórios.
- Sem criação automática de workspace, catálogo, schema ou recursos com custo.
- Execução local deve funcionar sem Airflow, Databricks SDK autenticado ou rede cloud.
- Falhas de permissão e inconsistências devem ser classificadas por gate, não mascaradas.
- Artefatos devem ser compatíveis com CI e revisão por pull request.

## Acceptance Tests

| ID | Scenario | Expected |
|---|---|---|
| AT-001 | Configuração sem credenciais | Preflight retorna `SKIP_EXTERNAL` sem traceback sensível |
| AT-002 | Host inválido | Gate de conectividade falha com diagnóstico acionável |
| AT-003 | Catálogo/schema ausente | Execução bloqueia publicação antes de mutação |
| AT-004 | Permissão somente leitura | Dry-run passa; publish é bloqueado e reportado |
| AT-005 | Dry-run válido | Todos os objetos esperados aparecem sem alteração externa |
| AT-006 | Publish repetido | Segunda execução não duplica objetos |
| AT-007 | Manifest SQL inválido | Gate de contrato falha antes do publish |
| AT-008 | Métrica divergente | Reconciliação falha com produto, métrica e tolerância identificados |
| AT-009 | Freshness fora do SLA | Produto é marcado `STALE` e gate correspondente falha |
| AT-010 | Segredo em configuração/log | Security gate falha e valor é redigido |
| AT-011 | Execução aprovada | Relatório contém commit, timestamp, gates, objetos e resultado final |
| AT-012 | Execução sem workspace | Suíte local permanece verde e externa fica `SKIP_EXTERNAL` |

## Data and Integration Contracts

- Entradas: `pipelines/gold/contracts/*.yaml`, `pipelines/gold/sql/`, `pipelines/gold/dashboards/` e configuração de ambiente.
- Saídas: relatório versionável de evidências e status por gate; nenhum dado operacional deve ser persistido no repositório.
- Integração externa: Databricks SQL/REST/Lakeview somente após confirmação explícita de modo `publish`.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Ambiente externo indisponível | Preflight local e `SKIP_EXTERNAL` explícito |
| Permissões insuficientes | Verificação antecipada e dry-run obrigatório |
| Divergência entre fixture e workspace | Reconciliação com tolerância documentada |
| Exposição de segredo | Redaction, allowlist de campos e testes de segurança |
| Custo ou mutação inesperada | Sem provisionamento; publish opt-in e idempotente |

## Open Questions (non-blocking for Design)

1. Qual catálogo/schema de teste será fornecido para a execução autorizada?
2. Qual mecanismo de autenticação será aprovado para CI (OIDC, service principal ou PAT temporário)?
3. Quais objetos o primeiro publish poderá criar versus somente atualizar?

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-18 | define-agent | Requirements captured from approved Fase 8 brainstorm |

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_FASE8_EXTERNAL_VALIDATION.md`
