# BRAINSTORM: Fase 9 — Databricks Smoke Test Autorizado

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | FASE9_DATABRICKS_SMOKE_TEST |
| **Date** | 2026-08-18 |
| **Author** | brainstorm-agent |
| **Status** | ✅ Complete (Defined) |

## Initial Idea

**Raw Input:** Executar o primeiro smoke test externo do AutoMesh em um workspace Databricks de teste usando o harness entregue na Fase 8.

**Context Gathered:**

- As Fases 1–8 estão implementadas e arquivadas.
- A Fase 8 valida localmente, mas seu adapter Databricks ainda é deliberadamente um boundary sem implementação live.
- A próxima entrega deve provar conectividade, Unity Catalog, permissões, publicação controlada e reconciliação sem tocar em produção.

## Discovery Questions & Answers

| # | Question | Assumption for Define | Impact |
|---|---|---|---|
| 1 | Qual ambiente será usado? | **Workspace de teste dedicado ou schema isolado** | Nenhum objeto de produção será alterado |
| 2 | Qual autenticação? | **OAuth/service principal com segredo injetado no ambiente** | PAT em arquivo e logs ficam proibidos |
| 3 | Qual escopo de publicação? | **Um produto Gold e uma view Lakeview primeiro** | Reduz risco e tempo do primeiro smoke |
| 4 | O teste pode criar objetos? | **Somente dentro do schema explicitamente aprovado** | Catálogo/schema serão verificados antes |
| 5 | Qual resultado mínimo? | **Preflight PASS, dry-run PASS, publish idempotente e reconciliação PASS** | Evidência deve conter cada gate |
| 6 | O que acontece em falha? | **Parar sem rollback destrutivo e registrar diagnóstico** | Remediação será manual e auditável |

## Recommended Approach

### Approach A: Canary publish in isolated schema ⭐ Recommended

Usar o adapter da Fase 8 para publicar um subconjunto canário em schema isolado, executar uma consulta de reconciliação, repetir o publish para provar idempotência e remover apenas objetos temporários se isso for explicitamente autorizado.

**Confidence:** 0.85 — depende de acesso externo ainda não fornecido, mas reutiliza contratos, planner, gates e evidências já implementados.

### Deferred approaches

- Publicação de todos os quatro produtos em uma única execução.
- Alteração de pipelines produtivos ou schedules permanentes.
- Provisionamento de workspace, cluster, catálogo ou permissões.
- Teste de carga, benchmark de custo ou migração de BI.

## Scope Boundary

**In scope:** adapter mínimo autenticado, preflight real, dry-run, canary publish, consulta de reconciliação, repetição idempotente e relatório de evidências.

**Out of scope:** produção, dados sensíveis reais, destruição automática, provisionamento e integrações SaaS.

## Initial Acceptance Signals

- [ ] Workspace e identidade confirmados sem revelar credenciais.
- [ ] Catálogo/schema aprovados e isolados.
- [ ] Dry-run lista exatamente os objetos canários esperados.
- [ ] Publish cria/atualiza somente o escopo autorizado.
- [ ] Segunda execução não duplica objetos.
- [ ] Métricas e freshness reconciliam com tolerância documentada.
- [ ] Relatório exportável contém commit, timestamp, gates e objetos.
- [ ] Qualquer falha encerra o teste antes de mutação adicional.

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_FASE9_DATABRICKS_SMOKE_TEST.md`
