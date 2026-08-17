# BRAINSTORM: Fase 4 — Motor RAG e Geração de Conteúdo

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | FASE4_RAG_CONTEUDO |
| **Date** | 2026-08-06 |
| **Author** | brainstorm-agent |
| **Status** | ✅ Complete (Defined) |

---

## Initial Idea

**Raw Input:** Explorar a Fase 4 (Motor RAG e Geração de Conteúdo) da arquitetura Zero-Touch Data Mesh — RAG corporativo sobre SharePoint, cruzamento com dados estruturados (`gold.market_insights` da Fase 3), e a "fábrica de prompts" para relatórios de marketing.

**Context Gathered:**
- Fases 1-3, todas shipped, entregam o hand-off natural: `gold.market_insights` (Fase 3) para cruzar com os documentos do RAG, e o pipeline de guardrails+PR do self-healing (Fase 2), reaproveitável de novo para a fábrica de conteúdo.
- `context.md` reserva "entrega segura via Microsoft Graph (OAuth2)" explicitamente para a Fase 5 — mas o usuário decidiu antecipar o registro do app Entra ID/OAuth2 já nesta fase, já que o RAG precisa de acesso real ao SharePoint de qualquer forma.
- KB `patterns/rag/rag-operating-pattern.md` e `genai/quick-reference.md` fornecem o vocabulário de variantes de RAG e padrões de avaliação (RAGAS) usados nas decisões abaixo.
- KB `databricks/patterns/ai-ml-patterns.md` documenta o padrão de Delta Sync Index do Databricks Vector Search — embedding/indexação automáticos a partir de uma tabela Delta, sem job de embedding manual.

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|--------|-------------|--------------|
| Likely Location | `pipelines/rag/` (ingestão SharePoint, config de indexação, retrieval, fábrica de conteúdo) + extensão de `pipelines/self_healing/` (novo tipo de evento `content_generation`) | Reaproveita o pacote de self-healing, mesmo padrão da Fase 3 |
| Relevant KB Domains | `genai`, `prompt-engineering`, `patterns/rag`, `ai-data-engineering`, `data-quality`, `databricks` (Delta Sync Index) | Design deve consultar esses domínios e validar Databricks Vector Search no Free Edition |
| IaC Impact | App registration Entra ID (OAuth2/Microsoft Graph) + endpoint de Databricks Vector Search — nenhum dos dois provisionado ainda | Design deve validar a disponibilidade do Vector Search no Free Edition (mesma classe de assunção da Fase 3 com MLflow) |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Fonte de documentos do RAG — SharePoint real ou simulado? | SharePoint real já nesta fase | Antecipa OAuth2/Microsoft Graph da Fase 5 |
| 2 | Tenant Microsoft 365/Entra ID disponível? | Preciso criar um tenant novo | Mesmo padrão do Databricks Free Edition — desenha agora, provisiona e valida depois |
| 3 | Divisão de escopo OAuth2 entre Fase 4 e Fase 5 | Registrar o app inteiro agora, com todas as permissões | Um único app registration reutilizado nas duas fases |
| 4 | Vector store para o RAG | Databricks Vector Search | Reaproveita o workspace já usado nas Fases 2-3; dependência de Unity Catalog vira assunção a validar |
| 5 | Variante de RAG | Advanced RAG (hybrid search + rerank) | Padrão de produção, sem a complexidade de um agente decidindo quando/como buscar |
| 6 | Gatilho da fábrica de conteúdo | Reaproveitar `dag_self_healing_diagnose` | Generaliza o self-healing para mais um tipo de evento (`content_generation`) |
| 7 | Usar RAGAS e NeMo Guardrails, como o `context.md` descreve? | Os dois | Diverge da decisão de guardrails 100% custom da Fase 2 — aqui adota os frameworks originais do stack, especificamente para o RAG |
| 8 | Critério de sucesso do brainstorm | Visão completa: RAG + fábrica de conteúdo + avaliação | Documento cobre as três frentes |
| 9 | Amostras/documentos de teste disponíveis? | Nenhuma ainda | Documentos de teste sobem no SharePoint quando o tenant estiver pronto |
| 10 | RAGAS como gate bloqueante ou só métrica observada? | Gate bloqueante | Define um limiar de partida a calibrar no Design (sem histórico ainda) |

**Minimum Questions:** 3 ✅ (10 realizadas)

---

## Sample Data Inventory

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Input files | N/A — SharePoint ainda não provisionado | 0 | Documentos de teste (contratos/atas fictícias) sobem no SharePoint quando o tenant existir |
| Output examples | N/A | 0 | Formato do relatório de marketing definido do zero no Design |
| Ground truth | N/A | 0 | RAGAS mede fidelidade/relevância sem precisar de rótulo humano pré-existente |
| Related code | `gold.market_insights` (Fase 3), `self_healing_events`/`self_healing_rejections` (Fase 2/3, padrão a reaproveitar) | 3 tabelas | A fábrica de conteúdo cruza outliers com documentos recuperados |

**How samples will be used:**

- N/A nesta sessão — Design deve especificar o schema de `bronze.sharepoint_documents` e um conjunto mínimo de documentos de teste para validar o pipeline de ponta a ponta.

---

## Approaches Explored

### Approach A: Tudo em lote, via Airflow ⭐ Recomendado

**Description:** Airflow orquestra a ingestão do SharePoint (Graph API delta query) → chunking → grava numa tabela Delta (`bronze.sharepoint_documents`). O Databricks Vector Search sincroniza essa tabela automaticamente via Delta Sync Index. A geração de relatórios de marketing também roda em lote, disparada por um DAG — sem nenhuma API viva de consulta.

**Pros:**
- Consistente com as 3 fases anteriores (tudo Airflow-orquestrado, nada "always-on" novo)
- Delta Sync Index elimina a etapa manual de embedding
- Menos superfície de operação numa conta trial

**Cons:**
- Ninguém pode "perguntar algo ao RAG" interativamente — só relatórios agendados

**Why Recommended:** Mantém a mesma filosofia batch/Airflow já validada 3 vezes contra infraestrutura real; o Delta Sync Index encaixa naturalmente com a escolha de Databricks Vector Search. Confiança: 0.85 (padrão de KB + consistência arquitetural com o projeto).

---

### Approach B: Lote + API de consulta ao vivo

**Description:** Mesma ingestão da Approach A, mas adiciona um serviço pequeno (FastAPI) para perguntas interativas em tempo real, além dos relatórios em lote.

**Pros:**
- Mais próximo de como RAG corporativo é usado na prática (pergunta ao vivo, não só relatório agendado)

**Cons:**
- Primeiro serviço "always-on" do projeto — muda o perfil de operação (precisa ficar no ar) e adiciona superfície nova (hosting, auth de API) sem precedente nas fases já validadas

**Why Not Chosen:** O usuário confirmou a Approach A — manter consistência com o padrão batch já estabelecido pesou mais do que a interatividade nesta fase.

---

## Data Engineering Context

### Source Systems

| Source | Type | Volume Estimate | Current Freshness |
|--------|------|-----------------|--------------------|
| SharePoint (Microsoft Graph, delta query) | API REST real | Baixo (poucos documentos de teste) | Polling agendado (não tempo real) |
| `gold.market_insights` (Fase 3) | Tabela Delta | Baixo (herdado) | Hourly (Fase 3) |

### Data Flow Sketch
```text
[SharePoint (Graph delta query)] → [dag_ingest_sharepoint_documents: download + chunking]
        │
        ▼
[bronze.sharepoint_documents (Delta)] ──Delta Sync Index──► [Databricks Vector Search]
                                                                    │
[gold.market_insights (Fase 3)] ──┐                                │
                                    ├──► [fábrica de conteúdo: retrieval hybrid+rerank] ──► rascunho
                                    │                                                          │
                                    │                                                   [RAGAS: gate]
                                    │                                                          │
                                    │                                        ┌─────────────────┴──────┐
                                    │                                   abaixo do limiar          acima do limiar
                                    │                                        │                          │
                                    │                              [self_healing_rejections]   [self_healing_events:
                                    │                                                            content_generation]
                                    │                                                                     │
                                    │                                                                     ▼
                                    │                                                     [dag_self_healing_diagnose]
                                    │                                                          → guardrails → PR
```

### Key Data Questions Explored

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Qual o volume esperado? | Baixo — mesmo perfil de portfólio das fases anteriores | Delta Sync Index e retrieval não precisam de infraestrutura pesada |
| 2 | Qual a frequência de atualização do índice? | Polling agendado via Airflow (não webhook em tempo real) | Consistente com o padrão batch de todo o projeto |
| 3 | Quem consome a saída? | Revisor humano via PR (relatórios); Fase 5 quando a entrega automática existir | Define o formato do corpo do PR e o contrato de `bronze.sharepoint_documents` |

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach A — Tudo em lote, via Airflow |
| **User Confirmation** | 2026-08-06 (confirmado no chat) |
| **Reasoning** | Mantém a mesma filosofia batch/Airflow das 3 fases anteriores; Delta Sync Index elimina a etapa manual de embedding |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|----------|-----------|------------------------|
| 1 | SharePoint real com OAuth2/Microsoft Graph já na Fase 4, antecipando escopo da Fase 5 | Decisão explícita do usuário — o RAG precisa de documentos reais para ter valor de portfólio | Documentos simulados localmente (mais simples, mas adiaria a integração real) |
| 2 | App registration único com todas as permissões (Fase 4 + Fase 5) registradas de uma vez | Evita reconfigurar o app depois; a Fase 5 só adiciona lógica de uso, não escopo de permissão novo | Registrar só o escopo mínimo de leitura da Fase 4 agora |
| 3 | Databricks Vector Search com Delta Sync Index, não Qdrant/pgvector | Reaproveita o workspace já usado nas Fases 2-3; elimina job de embedding manual | Qdrant local via Docker (mais barato/testável, mas um serviço novo) |
| 4 | Advanced RAG (hybrid search + rerank), não Agentic nem Naive | Padrão de produção sem a complexidade de um agente decidindo quando/como buscar | Agentic RAG (multi-hop); Naive RAG (retrieval simples) |
| 5 | RAGAS como gate bloqueante antes do PR | Decisão explícita do usuário — seguir o `context.md` literalmente | RAGAS só como métrica observada, sem bloquear |
| 6 | NeMo Guardrails adotado para o RAG (diferente da decisão 100% custom da Fase 2) | Decisão explícita do usuário — seguir o stack original do `context.md` para esta peça específica | Manter guardrails custom também aqui, sem framework externo |

---

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed | Can Add Later? |
|--------------------|------------------|------------------|
| Webhook do SharePoint (change notifications em tempo real) | Polling via Airflow já é o padrão consistente do projeto; webhook seria o primeiro listener "always-on" | Yes — se a latência do polling virar problema real |
| GraphRAG / grafo de conhecimento | Advanced RAG já escolhido; GraphRAG é mais escopo do que o MVP precisa | Yes — se raciocínio relacional entre documentos virar necessidade |
| Suporte multi-idioma | Documentos e relatórios em português por ora | Yes — quando houver necessidade real |

---

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---------|-----------|-----------------|------------|
| Ingestão SharePoint real + indexação (Delta Sync Index) | ✅ | Confirmado sem ajustes ("sim") | No |
| Retrieval, geração e fábrica de conteúdo (RAGAS + self-healing) | ✅ | Confirmado sem ajustes ("sim") | No |

**Minimum Validations:** 2 ✅

---

## Suggested Requirements for /define

### Problem Statement (Draft)
A Fase 4 precisa indexar documentos reais do SharePoint corporativo (via Microsoft Graph/OAuth2) num motor RAG (Databricks Vector Search + Advanced RAG), cruzar esse conhecimento com os outliers de mercado já detectados na Fase 3, e gerar rascunhos de relatórios de marketing/executivos — cada um avaliado por RAGAS como gate de qualidade antes de virar PR pelo mesmo pipeline de guardrails da Fase 2.

### Target Users (Draft)
| User | Pain Point |
|------|------------|
| Autor do projeto (operador) | Precisa que o RAG cite a fonte real (documento do SharePoint) e que relatórios de baixa qualidade nunca cheguem a virar PR |
| Recrutador/entrevistador técnico | Precisa ver RAG corporativo real (não simulado) funcionando com métricas de avaliação de verdade (RAGAS) |
| Revisor humano do PR | Precisa decidir publicar ou não o rascunho de relatório, já filtrado por qualidade mínima |

### Success Criteria (Draft)
- [ ] App registration Entra ID criado com as permissões `Sites.Read.All`/`Files.Read.All` (+ escopo reservado da Fase 5)
- [ ] `dag_ingest_sharepoint_documents` ingere documentos reais via Graph delta query e grava chunks em `bronze.sharepoint_documents`
- [ ] Databricks Vector Search (Delta Sync Index) mantém o índice sincronizado automaticamente
- [ ] Query de retrieval combina busca semântica + lexical com rerank antes da síntese
- [ ] Fábrica de conteúdo gera rascunho cruzando outliers (`gold.market_insights`) com documentos do RAG
- [ ] RAGAS bloqueia (gate) relatórios abaixo do limiar de faithfulness/relevancy definido
- [ ] Relatórios aprovados viram PR via `dag_self_healing_diagnose` reaproveitado

### Constraints Identified
- Tenant Microsoft 365/Entra ID ainda não existe — precisa ser provisionado (ex: Microsoft 365 Developer Program, gratuito)
- Databricks Vector Search depende de Unity Catalog — assunção a validar no Design (mesma classe de risco do MLflow na Fase 3)
- RAGAS precisa de um limiar calibrado sem histórico prévio — valor de partida a propor no Design, ajustável

### Out of Scope (Confirmed)
- API de consulta interativa em tempo real (Approach B rejeitada)
- Notificação via webhook do SharePoint
- GraphRAG / grafo de conhecimento
- Suporte multi-idioma
- Entrega via Teams/Outlook — só a leitura do SharePoint é desta fase; envio é Fase 5

---

## Session Summary

| Metric | Value |
|--------|-------|
| Questions Asked | 10 |
| Approaches Explored | 2 |
| Features Removed (YAGNI) | 3 |
| Validations Completed | 2 |
| Duration | 1 sessão de chat |

---

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_FASE4_RAG_CONTEUDO.md`
