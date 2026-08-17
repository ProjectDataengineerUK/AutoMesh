# BRAINSTORM: Fase 3 — Motor de Insights (B3+Lost Sales) e Agente FinOps

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | FASE3_INSIGHTS_FINOPS |
| **Date** | 2026-08-05 |
| **Author** | brainstorm-agent |
| **Status** | ✅ Complete (Defined) |

---

## Initial Idea

**Raw Input:** Explorar a Fase 3 (Camada de Inteligência e FinOps) da arquitetura Zero-Touch Data Mesh — motor de insights cruzando cotações B3 com vendas perdidas (Lost Sales), e o Agente FinOps de governança de custo.

**Context Gathered:**
- Fases 1 (Ingestão) e 2 (Processamento + Self-Healing), ambas shipped, entregam o hand-off natural: `silver.b3_quotes`, `silver.crm_lost_sales` (Fase 2), e o pipeline de guardrails + PR do self-healing (Fase 2), reaproveitável para qualquer ação que exija revisão humana.
- Pesquisa web confirmou que o **Databricks Free Edition só tem compute serverless** — não existe cluster para "redimensionar" como o `context.md` original descrevia para o Agente FinOps. O agente precisou ser reformulado para governança de workload em vez de infraestrutura.
- KB `operations/cost/cost-patterns.md` aponta `system.billing.usage` como a fonte padrão de monitoramento de custo no Databricks — acesso a essa tabela no Free Edition não está confirmado (mesma classe de assunção de risco que a Fase 2 teve com a API do Databricks).

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|--------|-------------|--------------|
| Likely Location | `pipelines/insights/` (treino, inferência, drift) + extensão de `pipelines/self_healing/` (novos tipos de diagnóstico: `cost_anomaly`, `model_promotion`) | Reaproveita o pacote de self-healing em vez de duplicar guardrails/PR |
| Relevant KB Domains | `operations/cost`, `databricks/patterns/compute-patterns`, `ai-data-engineering`, `genai`, `data-quality` | Design deve consultar `cost-patterns.md` e validar acesso a `system.billing.usage` |
| IaC Impact | MLflow tracking/registry deve vir com o workspace Databricks; acesso a `system.billing.usage` — TBD | Design deve validar as duas coisas antes de fechar a arquitetura |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Como reformular o Agente FinOps dado que o Free Edition só tem compute serverless? | Governança de workload, não de infraestrutura | Redefine a natureza inteira do agente — de "redimensionar cluster" para "monitorar e corrigir consumo por job" |
| 2 | Foco deste brainstorm — insights, FinOps, ou os dois? | Os dois juntos, escopo completo | Mesmo padrão das Fases 1 e 2 |
| 3 | Método de detecção de outlier (B3 + Lost Sales) | Isolation Forest (ML leve) | Introduz MLOps real (MLflow, treino, drift) no projeto — ver Approaches Explored |
| 4 | Cadência de retreino do modelo | Continuous Training completo (CT) | Exige monitoramento de drift + shadow deployment + promoção controlada |
| 5 | Como o Agente FinOps age ao detectar anomalia de custo? | Reaproveitar o fluxo de guardrails + PR da Fase 2 | Generaliza o self-healing para "qualquer ação arriscada passa por aqui", não só correção de erro |
| 6 | Critério de sucesso deste brainstorm | Visão completa: insights + FinOps + CT | Documento cobre as três frentes |
| 7 | Amostras/dados de treino disponíveis? | Nenhuma externa — usar os dados sintéticos já gerados nas Fases 1-2 (Silver); Isolation Forest é não-supervisionado, não exige rótulo | Grounding vem do próprio projeto |
| 8 | Cadência de inferência de outliers | De hora em hora, acompanhando o `dag_process_bronze_to_silver` da Fase 2 | Evita inventar um terceiro ritmo de execução no projeto |

**Minimum Questions:** 3 ✅ (8 realizadas)

---

## Sample Data Inventory

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Input files | N/A | 0 | Nenhum dataset externo |
| Output examples | N/A | 0 | N/A |
| Ground truth | N/A | 0 | Isolation Forest é não-supervisionado — não precisa de rótulo de "isso é outlier" |
| Related code | `silver.b3_quotes`, `silver.crm_lost_sales` (Fase 2); `self_healing_events`/`self_healing_rejections` (Fase 2, padrão a reaproveitar) | 2 tabelas Silver + 2 tabelas de padrão | Features de treino vêm direto da Silver; o padrão de guardrails/rejeição é reaproveitado, não recriado |

**How samples will be used:**

- Features do Isolation Forest: variação de preço em janela móvel (`b3_quotes`), valor/frequência de venda perdida (`crm_lost_sales`).
- Nenhum dado externo necessário — o próprio histórico acumulado pelas Fases 1-2 já serve de base de treino inicial.

---

## Approaches Explored

### Approach A: Motor estatístico simples ⭐ Recomendado (evidência KB)

**Description:** Z-score/IQR sobre janelas móveis das features (variação de preço, valor de venda perdida), sem modelo de ML.

**Pros:**
- Sem infraestrutura de MLOps (sem MLflow, sem registry, sem monitoramento de drift)
- Rápido de rodar em PySpark puro, fácil de explicar e depurar

**Cons:**
- Menos sofisticado — não generaliza bem para padrões multivariados (cruzar preço + venda perdida ao mesmo tempo)

**Why Recommended:** Alinhado ao padrão que as Fases 1-2 sempre seguiram — a opção mais simples e barata que atende o MVP, sem introduzir uma nova classe de infraestrutura (model registry). Confiança: 0.80 (sem precedente direto no código do projeto, mas consistente com as decisões anteriores).

---

### Approach B: Isolation Forest (ML leve) — Escolhido pelo usuário

**Description:** Modelo de detecção de anomalia não-supervisionado, treinado sobre as features de mercado + vendas, servido via MLflow com ciclo de Continuous Training.

**Pros:**
- Detecta padrões multivariados que um z-score simples não capturaria
- Demonstra o stack de MLOps completo que o `context.md` já promete no discurso do projeto (Databricks Feature Store, MLflow, continuous training)

**Cons:**
- Introduz complexidade real de MLOps (treino, versionamento, monitoramento de drift, shadow deployment) — mais superfície para manter

**Why Chosen:** O usuário priorizou demonstrar a capacidade de MLOps completa do projeto (treino + Continuous Training) em vez de manter o MVP mais enxuto — decisão consciente de ampliar escopo para aumentar o valor de portfólio.

---

### Approach C: LLM interpretando os dados

**Description:** Claude analisa os números diretamente e aponta outliers/correlações em linguagem natural.

**Pros:**
- Mais flexível; reaproveita a integração já existente com o Claude (Fase 2)

**Cons:**
- Menos determinístico para métricas numéricas, mais caro por chamada, difícil de validar objetivamente se o resultado está correto

**Why Not Chosen:** Para detecção de anomalia sobre dados numéricos estruturados, um método estatístico/ML é mais confiável e mais barato do que pedir para o LLM "olhar os números".

---

## Data Engineering Context

### Source Systems

| Source | Type | Volume Estimate | Current Freshness |
|--------|------|-----------------|--------------------|
| `silver.b3_quotes`, `silver.crm_lost_sales` | Tabelas Delta (Fase 2) | Baixo (herdado) | Hourly (Fase 2) |
| `system.billing.usage` | Tabela de sistema Databricks | TBD | TBD — acesso a validar no Design |
| `dag_run` (metadados do Airflow) | Fallback de proxy de custo | Baixo | Por execução de DAG |

### Data Flow Sketch
```text
[silver.b3_quotes + silver.crm_lost_sales]
        │
        ▼
[dag_train_outlier_model: features + Isolation Forest] → [MLflow: novo modelo em Staging]
        │
        │ (hourly, dados novos)
        ▼
[dag_generate_insights: inferência com modelo Production] → [gold.market_insights]
        │
        ▼
[drift check: distribuição nova vs. baseline] ──drift alto──► retreina (novo Staging)
        │
        ▼
[shadow check: Staging vs. Production nos mesmos dados] → diagnóstico
        │
        ▼
[dag_self_healing_diagnose] → guardrails → PR (promove modelo) ──merge──► Production

[system.billing.usage ou dag_run.duration, hourly] → [dag_finops_monitor: detecta anomalia de custo]
        │
        ▼
[dag_self_healing_diagnose] → guardrails → PR (schedule / OPTIMIZE)
```

### Key Data Questions Explored

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Qual o volume esperado? | Baixo — mesmo perfil das Fases 1-2 | Isolation Forest treina rápido, sem necessidade de cluster grande |
| 2 | Onde os insights ficam disponíveis? | `gold.market_insights` (Delta) | Prepara o consumo futuro pela Fase 4 (RAG cita "insights" no `context.md`) |
| 3 | Quem consome a saída? | Fase 4 consome `gold.market_insights`; revisor humano consome os PRs de FinOps/promoção | Define o contrato da tabela Gold e o formato do corpo do PR |

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach B — Isolation Forest com Continuous Training |
| **User Confirmation** | 2026-08-05 (confirmado no chat) |
| **Reasoning** | Prioriza demonstrar o stack de MLOps completo (treino, drift, shadow deployment, promoção controlada) já prometido pelo `context.md`, em vez do MVP estatístico mais enxuto recomendado pela evidência de KB |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|----------|-----------|------------------------|
| 1 | Agente FinOps reformulado para governança de workload, não de infraestrutura | Free Edition só tem compute serverless, sem cluster para redimensionar (confirmado via pesquisa web) | Manter a lógica clássica de "redimensionar cluster" do `context.md` original |
| 2 | Isolation Forest + MLflow + Continuous Training completo | Usuário priorizou demonstrar stack de MLOps real no portfólio | Motor estatístico simples (mais barato, recomendação da KB) |
| 3 | Promoção de modelo passa pelo mesmo `dag_self_healing_diagnose` + guardrails + PR da Fase 2 | Reaproveita o mecanismo já construído e validado; bate com o exemplo de decisão HITL que o próprio `context.md` cita ("aprovar um novo modelo preditivo que afeta relatórios executivos") | Promoção automática sem revisão humana |
| 4 | Agente FinOps também usa o `dag_self_healing_diagnose` para suas ações | Generaliza o self-healing para "qualquer ação arriscada passa por guardrails+PR" em vez de duplicar a lógica de diagnóstico/guardrail | Um pipeline de diagnóstico separado só para custo |
| 5 | Inferência de outliers de hora em hora | Acompanha a cadência já estabelecida pelo `dag_process_bronze_to_silver` da Fase 2 | Inferência a cada 15 min (dados não mudam tão rápido) ou diária (usuário pediu algo mais frequente) |

---

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed | Can Add Later? |
|--------------------|------------------|------------------|
| Databricks Lakehouse Monitoring nativo | Feature avançada, possivelmente restrita/premium no Free Edition; uma comparação estatística simples de distribuição (KS-test/PSI) em PySpark cobre a necessidade sem dependência extra | Yes — se confirmado disponível no Design |
| Ensemble de modelos | Um Isolation Forest já cobre o MVP; ensemble é otimização prematura | Yes — iteração futura |
| Alertas externos (PagerDuty/Slack) para o Agente FinOps | Notificação via chat corporativo é escopo da Fase 5 (HITL/Microsoft Graph); nesta fase fica só PR + tabela | Yes — Fase 5 |
| Inferência de outliers em tempo real/streaming | Volume baixo do projeto não justifica; batch de hora em hora já atende | Yes — se o volume crescer |

---

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---------|-----------|-----------------|------------|
| Motor de insights + Continuous Training | ✅ | Confirmado sem ajustes ("sim") | No |
| Agente FinOps (coleta, detecção, ação) | ✅ | Confirmado sem ajustes ("segue") | No |

**Minimum Validations:** 2 ✅

---

## Suggested Requirements for /define

### Problem Statement (Draft)
A Fase 3 precisa cruzar os dados de mercado (B3) e vendas perdidas (CRM) já disponíveis na Silver para detectar outliers/oportunidades via um modelo de ML com ciclo de Continuous Training completo, e precisa de um Agente FinOps que monitore o consumo de workload da plataforma e proponha correções — ambos reaproveitando o mecanismo de guardrails+PR já construído na Fase 2 para qualquer ação que exija revisão humana (promoção de modelo, mudança de schedule).

### Target Users (Draft)
| User | Pain Point |
|------|------------|
| Autor do projeto (operador) | Precisa que outliers/oportunidades cheguem prontos numa tabela, sem análise manual; precisa que custo anômalo seja sinalizado antes de virar surpresa na fatura |
| Recrutador/entrevistador técnico | Precisa ver um ciclo de MLOps real (treino, drift, shadow deployment, promoção via PR) funcionando, não só descrito em slide |
| Revisor humano do PR (mesma persona da Fase 2) | Precisa decidir promoção de modelo e mudanças de custo com contexto suficiente direto no PR |

### Success Criteria (Draft)
- [ ] Modelo Isolation Forest treinado e registrado no MLflow (stage `Staging`) a partir de `silver.b3_quotes` + `silver.crm_lost_sales`
- [ ] Inferência roda de hora em hora, gravando outliers em `gold.market_insights`
- [ ] Drift check compara distribuição nova vs. baseline e dispara retreino quando o limiar é excedido
- [ ] Promoção de modelo (`Staging` → `Production`) só acontece via PR aprovado e mergeado — nunca automática
- [ ] Agente FinOps monitora consumo por job de hora em hora e propõe correção (PR) quando detecta anomalia
- [ ] 100% das decisões de FinOps e de promoção de modelo passam pelos mesmos guardrails (allowlist + conteúdo) da Fase 2

### Constraints Identified
- Acesso a `system.billing.usage` no Databricks Free Edition não confirmado — fallback via `dag_run.duration` do Airflow
- MLflow tracking/registry precisa estar disponível no workspace Free Edition (assunção a validar no Design)
- Sem orçamento para ferramentas externas de FinOps de terceiros

### Out of Scope (Confirmed)
- Databricks Lakehouse Monitoring nativo
- Ensemble de modelos
- Alertas externos (PagerDuty/Slack) — Fase 5
- Inferência em tempo real/streaming
- Notificação via Microsoft Teams/Outlook (Adaptive Cards) — Fase 5

---

## Session Summary

| Metric | Value |
|--------|-------|
| Questions Asked | 8 |
| Approaches Explored | 3 |
| Features Removed (YAGNI) | 4 |
| Validations Completed | 2 |
| Duration | 1 sessão de chat |

---

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_FASE3_INSIGHTS_FINOPS.md`
