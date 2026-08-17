# BRAINSTORM: Fase 5 — Entrega Segura e Human-in-the-Loop

## Metadata

| Campo | Valor |
|---|---|
| Data | 2026-08-14 |
| Status | Complete (Defined) |
| Fonte | `context.md`, Fases 2-4 e auditoria de 2026-08-14 |

## Problema

As Fases 2-4 produzem PRs, propostas de promoção de modelo, alertas FinOps e relatórios aprovados, mas o responsável ainda precisa procurar essas decisões no GitHub/Airflow. A última milha precisa entregar o contexto ao decisor e registrar uma aprovação ou rejeição auditável sem permitir que uma mensagem do Teams execute código diretamente.

## Abordagens exploradas

### A. Teams + Adaptive Card + endpoint de decisão — selecionada

O Airflow envia um cartão com resumo, impacto, evidências e link para o PR. Aprovar/rejeitar cria uma decisão assinada e idempotente. Um worker separado aplica somente ações previamente permitidas.

Vantagens: experiência corporativa forte, decisão estruturada e trilha de auditoria. Riscos: exige endpoint público protegido, app registration e tenant real.

### B. Outlook com links de aprovação

Entrega por e-mail com links de uso único. É mais simples para notificações, mas pior para payloads interativos e proteção contra encaminhamento/replay.

### C. Apenas GitHub como HITL

Usar aprovação/merge do PR como única decisão. É tecnicamente simples e deve continuar sendo a autoridade para mudanças de código, mas não fecha a proposta de entrega no ecossistema Microsoft.

## Decisões

1. Teams/Adaptive Cards será o canal principal; Outlook será fallback de notificação.
2. Merge do GitHub continua sendo a autoridade para código e contratos.
3. A Fase 5 não fará merge automático de PR.
4. Promoção de modelo poderá ser aplicada somente após decisão registrada e validação do estado esperado.
5. Toda decisão terá `decision_id`, ator, timestamp, ação, recurso, resultado e correlação com evento/PR.
6. Callbacks serão idempotentes e protegidos contra replay.
7. Falha de entrega não perde a decisão: notificações usam outbox persistente com retry.

## Escopo proposto

- Cliente Microsoft Graph para envio ao Teams e Outlook.
- Modelo de Adaptive Card para PR, promoção de modelo, FinOps e relatório.
- Outbox Delta para notificações.
- Inbox/ledger Delta para decisões.
- Endpoint autenticado para callbacks.
- DAG de entrega e DAG de reconciliação.
- Aplicador de promoção de alias MLflow após aprovação.
- Rejeição com motivo e expiração automática.
- Métricas de entrega, decisão, retry e expiração.

## Fora do escopo

- Merge automático no GitHub.
- Operações financeiras ou rebalanceamento real.
- Interface web própria.
- Substituição do RBAC do Microsoft 365/GitHub.
- Power BI/Fabric completo; poderá ser uma fase posterior independente.

## Riscos a validar antes de Infrastructure Validated

- Tenant Microsoft 365 e permissões Graph disponíveis.
- Forma suportada de publicar e receber ações de Adaptive Cards no ambiente escolhido.
- Identidade do usuário disponível e verificável no callback.
- Endpoint público com TLS, autenticação e proteção contra replay.
- Permissão MLflow/Unity Catalog para aplicar alias em ambiente real.

## Critérios preliminares

- Nenhuma decisão crítica é aplicada sem registro de aprovação válido.
- Repetir o mesmo callback não repete a ação.
- Falha temporária do Graph gera retry sem duplicar notificações.
- Rejeição nunca aciona o aplicador.
- Aprovação de código apenas encaminha ao PR; não realiza merge.
- Todas as transições são auditáveis por `decision_id` e `correlation_id`.

## Próximo passo

Produzir `DEFINE_FASE5_ENTREGA_HITL.md`, fechando atores, SLAs, tipos de decisão, estados e critérios de aceitação antes do DESIGN.
