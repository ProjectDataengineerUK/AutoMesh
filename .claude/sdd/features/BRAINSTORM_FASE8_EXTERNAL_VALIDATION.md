# BRAINSTORM: Fase 8 — Validação Externa e Readiness Databricks

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | FASE8_EXTERNAL_VALIDATION |
| **Date** | 2026-08-18 |
| **Author** | brainstorm-agent |
| **Status** | ✅ Complete (Defined) |

## Initial Idea

**Raw Input:** Validar externamente os artefatos entregues nas Fases 1–7 e preparar o AutoMesh para uso controlado em um workspace Databricks.

**Context Gathered:**

- As Fases 1–7 estão implementadas, testadas localmente e protegidas por CI.
- A publicação real em Databricks, Unity Catalog, SQL/Lakeview e integrações cloud continua explicitamente pendente.
- A Fase 7 deixou contratos Gold, manifests de dashboards e preflight de publicação prontos para validação opt-in.

## Discovery Questions & Answers

| # | Question | Assumption for Define | Impact |
|---|---|---|---|
| 1 | Qual o objetivo principal? | **Validar os produtos Gold e os gates críticos em um workspace de teste** | Não haverá expansão funcional antes da validação |
| 2 | Qual ambiente? | **Workspace Databricks de teste, com Unity Catalog habilitado** | Catálogo/schema e permissões serão pré-condições |
| 3 | Quais integrações entram? | **Databricks SQL, Lakeview e jobs; demais SaaS ficam fora** | Escopo controlado e custo previsível |
| 4 | Como autenticar? | **OAuth/service principal via secrets do CI ou variável segura** | Nenhuma credencial será commitada ou impressa nos logs |
| 5 | O que constitui sucesso? | **Deploy dry-run, publicação controlada, execução de amostra e evidência exportável** | Cada gate terá resultado PASS/FAIL/SKIP explícito |
| 6 | O que fazer se não houver workspace? | **Executar somente preflight e manter o gate externo como SKIP justificado** | A ausência de infraestrutura não invalida a suíte local |

## Recommended Approach

### Approach A: External validation harness opt-in ⭐ Recommended

Adicionar um harness idempotente de validação que consuma os contratos e manifests existentes, execute preflight, publique apenas quando autorizado e gere evidências sem expor segredos.

**Confidence:** 0.90 — reutiliza os artefatos da Fase 7 e preserva a separação local/externa já adotada.

### Approaches explicitly deferred

- Provisionamento completo via Terraform.
- Migração para Fabric/Power BI ou Snowflake.
- Novos produtos Gold ou novos modelos de ML.
- Testes destrutivos, cargas de produção e alteração de dados do cliente.

## Scope Boundary

**In scope:** workspace preflight, configuração segura, validação de catálogo/schema, publicação controlada de SQL/Lakeview, execução de amostra, reconciliação de métricas e relatório de evidências.

**Out of scope:** provisionar contas, criar recursos com custo sem aprovação, alterar pipelines de produção, ou validar integrações externas não relacionadas ao Databricks.

## Initial Acceptance Signals

- [ ] Preflight detecta autenticação, workspace, catálogo, schema e permissões.
- [ ] Todas as credenciais são obtidas por secret/env e nunca aparecem nos artefatos.
- [ ] Execução sem workspace termina com `SKIP_EXTERNAL` claro e exit code configurável.
- [ ] Execução autorizada é idempotente e não duplica objetos.
- [ ] Métricas Gold publicadas reconciliam com fixtures locais dentro da tolerância definida.
- [ ] Relatório registra timestamp, commit, objetos e resultado de cada gate.

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_FASE8_EXTERNAL_VALIDATION.md`
