# BRAINSTORM: Fase 2 — Processamento (Bronze→Silver) e Self-Healing

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | FASE2_PROCESSAMENTO_SELFHEALING |
| **Date** | 2026-08-03 |
| **Author** | brainstorm-agent |
| **Status** | ✅ Complete (Defined) |

---

## Initial Idea

**Raw Input:** Explorar a Fase 2 (Processamento distribuído e Self-Healing) da arquitetura Zero-Touch Data Mesh — PySpark/Databricks para Bronze→Silver, e o agente que audita falhas e abre PR de correção no GitHub.

**Context Gathered:**
- A Fase 1 (Ingestão), já shipped, entrega o hand-off natural: tabelas Delta no Bronze e uma `bronze_dlq` unificada (registros inválidos com `_failure_reason` anexado).
- `context.md` descreve o self-healing como um agente que identifica a causa raiz (ex: mudança de schema), reescreve o script/contrato e abre PR no GitHub via API, notificando via Microsoft Graph — a notificação/aprovação HITL completa é escopo da Fase 5.
- Pesquisa web confirmou que o **Databricks Community Edition foi descontinuado em 2026-01-01**, substituído pelo **Databricks Free Edition** (serverless, suporta ETL workflows) — corrigido em tempo real durante o brainstorm, evitando desenhar em cima de um produto que não existe mais.

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|--------|-------------|--------------|
| Likely Location | `pipelines/processing/` (Bronze→Silver) e `pipelines/self_healing/` (novo, ao lado de `pipelines/ingestion/` da Fase 1) | Mantém o padrão de pacote por fase já estabelecido |
| Relevant KB Domains | `databricks`, `spark`, `lakeflow`, `medallion`, `data-quality`, `airflow` (padrão `error-handling.md` para `on_failure_callback`) | Design deve consultar `medallion/quick-reference.md` (regras de Silver) e `lakeflow/quick-reference.md` |
| IaC Patterns | N/A — conta Databricks Free Edition ainda não provisionada | Acesso via API/service principal do Free Edition para chamadas externas do Airflow é uma assunção a validar no Design |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Qual o foco principal deste brainstorm — processamento, self-healing, ou os dois? | Os dois juntos, escopo completo | Amplia o brainstorm, mas mantém coerência com o `context.md` |
| 2 | Qual ambiente Databricks está disponível? | Community Edition → corrigido para **Free Edition** (Community foi descontinuada em 2026-01-01) | Ambiente serverless moderno, não o cluster único limitado da Community antiga |
| 3 | Como o self-healing decide a correção a propor? | LLM (Claude/GPT via API) | Generaliza melhor que regras fixas; exige guardrails |
| 4 | O que a correção deve alvejar quando a causa é identificada? | Depende do tipo de falha — contrato YAML (evolução de schema) ou código Python (lógica) | Agente precisa classificar a causa antes de gerar o diff |
| 5 | Critério de sucesso deste brainstorm | Visão completa: pipeline Bronze→Silver + fluxo inteiro do self-healing | Documento cobre as duas metades da Fase 2 |
| 6 | Amostras disponíveis (PRs de exemplo, prompts, schema Silver real)? | Nenhuma — usar os 3 motivos de falha reais da `bronze_dlq` da Fase 1 como base | Grounding vem do próprio projeto, não de exemplos externos |
| 7 | Que tipo de guardrail antes do PR existir? | Os dois: allowlist estrutural de arquivos/ações **e** guardrail de conteúdo revisando o diff | Duas camadas de defesa antes de qualquer PR ser aberto |
| 8 | Até onde o self-healing deve diagnosticar (só os 3 motivos da DLQ, ou mais)? | Qualquer exceção do pipeline — não só falhas de contrato | Self-healing precisa de uma segunda fonte de evento: falhas de execução do Airflow, não só a DLQ |

**Minimum Questions:** 3 ✅ (8 realizadas)

---

## Sample Data Inventory

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Input files | N/A | 0 | Nenhum exemplo externo — grounding vem da própria `bronze_dlq` da Fase 1 |
| Output examples | N/A | 0 | N/A |
| Ground truth | N/A | 0 | N/A |
| Related code | `pipelines/ingestion/common/bronze_writer.py`, contratos YAML da Fase 1 | 6 contratos + 1 tabela DLQ | Schema da `bronze_dlq` (`source`, `_failure_reason`, payload original) é a base do diagnóstico |

**How samples will be used:**

- Os 3 `_failure_reason` reais da Fase 1 (`null_violation`, `type_mismatch`, `constraint_violation`) servem de casos de teste para o diagnóstico do LLM.
- Os contratos YAML existentes definem o formato que o self-healing deve saber editar quando a causa for evolução de schema.

---

## Approaches Explored

### Approach A: Airflow continua o maestro único ⭐ Recomendado

**Description:** Um DAG do Airflow aciona um Job Databricks (PySpark simples, sem Lakeflow/DLT) para Bronze→Silver via API. Um segundo DAG (`dag_self_healing_diagnose`) escaneia a `bronze_dlq` e também recebe falhas de execução via `on_failure_callback` do Airflow; chama um LLM para diagnosticar, aplica dois guardrails, e abre PR no GitHub via API.

**Pros:**
- Mantém a narrativa de portfólio (Airflow como painel único de orquestração)
- Reaproveita padrões de retry/erro já validados na Fase 1 (KB `airflow/patterns/error-handling.md`)
- Self-healing fica desacoplado do Airflow como módulo Python testável, no mesmo espírito de `common/` da Fase 1

**Cons:**
- Acesso via API/service principal do Databricks Free Edition para chamadas externas do Airflow ainda não confirmado — assunção de risco a validar no Design

**Why Recommended:** Consistência arquitetural com a Fase 1 (evidência: `context.md` e o próprio `BRAINSTORM_FASE1_INGESTAO.md`), grounding em KB (`medallion`, `lakeflow`, `airflow`). Confiança: 0.85.

---

### Approach B: Lakeflow Declarative Pipelines nativo no Databricks

**Description:** Bronze→Silver usa `@dlt.expect_or_drop()` (Lakeflow) rodando dentro do próprio Databricks; self-healing vira um Job Databricks separado, sem Airflow, disparado por schedule.

**Pros:**
- Mais idiomático Databricks — decorators oficiais de qualidade "shift-left" (KB `lakeflow/quick-reference.md`)
- Serverless com TCO reduzido

**Cons:**
- Quebra a narrativa de "um único painel de orquestração" estabelecida na Fase 1 — dois orquestradores concorrentes

---

### Approach C: Self-healing reativo (trigger por chegada, não por schedule)

**Description:** Mesma base do Approach A, mas o self-healing reage a cada nova falha via trigger de chegada de dado, em vez de escaneamento periódico.

**Pros:**
- Mais fiel ao nome "self-healing" — reage imediatamente

**Cons:**
- Triggers de chegada de dado no Databricks são mais difíceis de testar/demonstrar num Free Edition
- Volume baixo do projeto não justifica a complexidade extra (mesma lógica de YAGNI usada para rejeitar streaming contínuo na Fase 1)

---

## Data Engineering Context

### Source Systems

| Source | Type | Volume Estimate | Current Freshness |
|--------|------|-----------------|--------------------|
| `bronze.b3_quotes`, `bronze.crm_lost_sales`, `bronze.infra_telemetry`, `bronze.usage_logs` (Fase 1) | Tabelas Delta | Baixo (herdado da Fase 1) | Conforme SLA da Fase 1 (~5 min / diário) |
| `bronze_dlq` (Fase 1) | Tabela Delta unificada | Baixo | Assim que uma falha de contrato ocorre |
| Airflow `on_failure_callback` (novo) | Evento/contexto de exceção | Baixo | No momento da falha de execução |

### Data Flow Sketch
```text
[Bronze (Fase 1)] → [Databricks Job: PySpark cleanse+dedup+cast] → [Silver: MERGE por chave de negócio]
        │                                                                    │
[bronze_dlq]──┐                                                    [infra_telemetry/usage_logs:
               │                                                    Silver append-only]
[Airflow on_failure_callback]──┐
                                 ├→ [dag_self_healing_diagnose] → [LLM: diagnóstico estruturado]
                                 │         │
                                 │   ┌─────┴─────┐
                                 │  válido      inválido
                                 │   │             │
                                 │   ▼             ▼
                                 │ [Guardrail   [self_healing_
                                 │  allowlist +  rejections
                                 │  conteúdo]    (Delta)]
                                 │   │
                                 │  passou
                                 │   ▼
                                 └→ [Branch + commit + PR no GitHub]
                                          │
                                   (revisão humana — retomada automática = Fase 5)
```

### Key Data Questions Explored

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Qual o volume esperado? | Baixo — mesmo perfil de portfólio da Fase 1 | Job Databricks pequeno, sem necessidade de cluster grande |
| 2 | A Silver precisa de deduplicação? | Sim, nas fontes com chave de negócio (`b3_quotes`, `crm_lost_sales`); telemetria/logs continuam append-only | Confirma MERGE vs append por fonte, conforme KB `medallion/quick-reference.md` |
| 3 | Quem consome a saída? | Silver alimenta a Fase 3 (FinOps/insights); PRs de self-healing são consumidos por um revisor humano | Define o contrato de saída da Silver e o formato do corpo do PR |

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach A — Airflow continua o maestro único |
| **User Confirmation** | 2026-08-03 (confirmado no chat) |
| **Reasoning** | Consistência com a arquitetura já estabelecida na Fase 1; self-healing desacoplado como módulo Python testável; grounding em KB (`medallion`, `lakeflow`, `airflow/error-handling`) |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|----------|-----------|------------------------|
| 1 | Databricks **Free Edition** (não Community Edition) | Community Edition foi descontinuada em 2026-01-01; Free Edition é o sucessor direto, serverless, com suporte a ETL workflows — confirmado via pesquisa web durante o brainstorm | Continuar assumindo Community Edition (produto não existe mais) |
| 2 | Bronze→Silver via PySpark simples num Databricks Job (não Lakeflow/DLT) | Mantém Airflow como orquestrador único (Approach A); DLT/Lakeflow ficaria mais idiomático mas quebraria a narrativa de painel único | Lakeflow Declarative Pipelines nativo (Approach B) |
| 3 | Self-healing escuta **duas fontes de falha**: `bronze_dlq` (contrato) e `on_failure_callback` do Airflow (execução) | Escopo do diagnóstico foi explicitamente ampliado pelo usuário para cobrir qualquer exceção do pipeline, não só falhas de contrato | Escutar só a `bronze_dlq` (escopo original, mais restrito) |
| 4 | Guardrails em duas camadas própria (allowlist de arquivos + checagem de conteúdo do diff), sem adotar um framework dedicado (ex: NeMo Guardrails) | Usuário pediu guardrails desde já, mas um framework dedicado é infraestrutura extra desproporcional para uma Fase 2 de portfólio; a checagem própria cobre o risco concreto (diff fora de escopo, padrões perigosos) | Adotar NeMo Guardrails como dependência |
| 5 | Rejeições de guardrail vão para uma tabela `self_healing_rejections` (Delta), sem abrir PR | Preserva rastreabilidade sem expor um PR potencialmente perigoso para revisão | Abrir PR mesmo assim, marcado como "requer atenção" |

---

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed | Can Add Later? |
|--------------------|------------------|------------------|
| Roteamento multi-modelo por custo (LiteLLM) | Otimização prematura — uma chamada direta a um único LLM já resolve o MVP; roteamento por custo faz mais sentido quando o volume de chamadas crescer (Fase 4/LLMOps) | Yes — no brainstorm da Fase 4 |
| Retomada automática do pipeline após o merge do PR (webhook fechando o ciclo) | É literalmente o que o Human-in-the-Loop da Fase 5 descreve no `context.md` — implementar agora antecipa escopo de outra fase | Yes — no brainstorm da Fase 5 |
| Framework dedicado de guardrails (NeMo Guardrails) | Infraestrutura extra desproporcional; a checagem própria (allowlist + padrões perigosos) cobre o risco concreto do MVP | Yes — se o volume/risco justificar depois |
| SCD2 / histórico completo na camada Silver | Nenhuma fonte atual precisa de rastreamento de histórico (`valid_from`/`valid_to`); MERGE simples por chave de negócio já atende | Yes — quando uma fonte exigir análise histórica |

---

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---------|-----------|-----------------|------------|
| Fontes de falha e guardrails (2 camadas) | ✅ | Confirmado sem ajustes ("sim") | No |
| Bronze→Silver + fluxo completo do PR | ✅ | Confirmado sem ajustes ("sim") | No |

**Minimum Validations:** 2 ✅

---

## Suggested Requirements for /define

### Problem Statement (Draft)
A Fase 2 precisa processar os dados validados do Bronze (Fase 1) até a Silver via PySpark no Databricks Free Edition, e fechar o ciclo de resiliência da plataforma: quando ocorre uma falha de contrato (`bronze_dlq`) ou de execução (exceção no Airflow), um agente deve diagnosticar a causa raiz via LLM, propor uma correção (no contrato de dados ou no código) dentro de guardrails de escopo e conteúdo, e abrir um Pull Request no GitHub para revisão humana.

### Target Users (Draft)
| User | Pain Point |
|------|------------|
| Autor do projeto (operador) | Precisa que falhas sejam diagnosticadas e propostas de correção cheguem prontas para revisão, sem investigar cada erro manualmente |
| Recrutador/entrevistador técnico | Precisa ver o diferencial de "agente autônomo com guardrails" funcionando de ponta a ponta, não só descrito em slide |
| Revisor humano do PR (o próprio autor) | Precisa que o PR tenha contexto suficiente (diagnóstico + diff + link do log da falha) para decidir rápido |

### Success Criteria (Draft)
- [ ] Pipeline PySpark Bronze→Silver roda no Databricks Free Edition, disparado pelo Airflow, com MERGE/dedup nas fontes com chave de negócio
- [ ] Falhas de contrato (`bronze_dlq`) e falhas de execução (`on_failure_callback`) alimentam o mesmo fluxo de diagnóstico
- [ ] LLM produz diagnóstico estruturado (causa raiz + tipo de correção + diff proposto) para 100% dos eventos de falha recebidos
- [ ] Guardrail de allowlist bloqueia 100% das propostas de diff fora do escopo de arquivos permitido
- [ ] Guardrail de conteúdo bloqueia propostas com padrões perigosos conhecidos, registrando em `self_healing_rejections`
- [ ] PR aberto no GitHub inclui diagnóstico + diff + link do log da falha original

### Constraints Identified
- Databricks Free Edition (serverless) — acesso via API/service principal para chamadas externas do Airflow ainda não confirmado, é uma assunção de risco a validar
- Custo de chamadas ao LLM por evento de falha — sem roteamento multi-modelo neste MVP
- Sem retomada automática do pipeline após merge do PR (fica para a Fase 5)

### Out of Scope (Confirmed)
- Roteamento multi-modelo por custo (LiteLLM) — Fase 4
- Retomada automática do pipeline após merge do PR (webhook HITL) — Fase 5
- Framework dedicado de guardrails (NeMo Guardrails) — implementação própria mais simples por ora
- SCD2 / histórico completo na camada Silver
- Painel Sentinela / observabilidade consolidada — Fase 3

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

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_FASE2_PROCESSAMENTO_SELFHEALING.md`
