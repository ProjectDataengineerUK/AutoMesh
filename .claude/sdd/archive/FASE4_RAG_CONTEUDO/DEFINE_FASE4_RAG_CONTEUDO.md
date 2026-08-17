# DEFINE: Fase 4 — Motor RAG e Geração de Conteúdo

> RAG corporativo real sobre SharePoint (Databricks Vector Search + Advanced RAG), cruzando outliers da Fase 3 com documentos indexados para gerar rascunhos de relatórios avaliados por RAGAS antes de virarem PR pelo pipeline de guardrails da Fase 2.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | FASE4_RAG_CONTEUDO |
| **Date** | 2026-08-07 |
| **Author** | define-agent |
| **Status** | ✅ Shipped |
| **Clarity Score** | 14/15 |

---

## Problem Statement

A Fase 4 precisa indexar documentos reais do SharePoint corporativo (via Microsoft Graph/OAuth2) num motor RAG (Databricks Vector Search + Advanced RAG), cruzar esse conhecimento com os outliers de mercado já detectados na Fase 3, e gerar rascunhos de relatórios de marketing/executivos — cada um avaliado por RAGAS como gate de qualidade antes de virar PR pelo mesmo pipeline de guardrails da Fase 2.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| Autor do projeto (Jonatas) | Operador do pipeline | Precisa que o RAG cite a fonte real (documento do SharePoint) e que relatórios de baixa qualidade nunca cheguem a virar PR |
| Recrutador/entrevistador técnico | Avaliador do portfólio | Precisa ver RAG corporativo real (não simulado) funcionando com métricas de avaliação de verdade (RAGAS) |
| Revisor humano do PR (mesma persona das Fases 2-3) | Aprovador do conteúdo | Precisa decidir publicar ou não o rascunho de relatório, já filtrado por qualidade mínima |

---

## Goals

| Priority | Goal |
|----------|------|
| **MUST** | App registration Entra ID criado com `Sites.Read.All`/`Files.Read.All` (+ escopo reservado da Fase 5) |
| **MUST** | `dag_ingest_sharepoint_documents` ingere documentos via Graph delta query e grava chunks em `bronze.sharepoint_documents` |
| **MUST** | Databricks Vector Search (Delta Sync Index) mantém o índice sincronizado automaticamente a partir dessa tabela |
| **MUST** | Retrieval combina busca semântica + lexical, com rerank antes da síntese (Advanced RAG) |
| **MUST** | Fábrica de conteúdo gera rascunho cruzando outliers (`gold.market_insights`) com documentos recuperados |
| **MUST** | RAGAS bloqueia (gate) relatórios abaixo do limiar de faithfulness/relevancy — nenhum relatório reprovado vira PR |
| **MUST** | Relatórios aprovados viram PR via `dag_self_healing_diagnose` reaproveitado (evento `content_generation`) |
| **SHOULD** | NeMo Guardrails aplicado nas entradas/saídas do RAG (input/output rails), isolado do guardrail determinístico do self-healing |
| **SHOULD** | Limiar do gate RAGAS é configurável, não hardcoded |
| **COULD** | Métricas RAGAS agregadas ficam estruturadas de forma reutilizável para o futuro Painel Sentinela |

**Priority Guide:**
- **MUST** = MVP fails without this
- **SHOULD** = Important, but workaround exists
- **COULD** = Nice-to-have, cut first if needed

---

## Success Criteria

- [ ] App registration Entra ID provisionado com as permissões corretas
- [ ] Documento novo/alterado no SharePoint é detectado e indexado em até 1 ciclo de polling
- [ ] Retrieval sempre combina resultado semântico + lexical, reordenado por reranker
- [ ] 100% dos rascunhos gerados passam pelo gate RAGAS antes de qualquer PR
- [ ] 0% dos relatórios abaixo do limiar chegam a virar PR
- [ ] 100% dos relatórios aprovados incluem as métricas RAGAS no corpo do PR

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Happy path — documento novo indexado | Um documento novo é adicionado ao site SharePoint configurado | `dag_ingest_sharepoint_documents` roda | O documento é baixado, chunked, gravado em `bronze.sharepoint_documents`, e o Delta Sync Index reflete o novo conteúdo |
| AT-002 | Retrieval combina busca semântica e lexical | Uma query de retrieval é executada pela fábrica de conteúdo | O retrieval busca contexto | Os resultados combinam relevância semântica e lexical, reordenados por um reranker antes de irem para o LLM |
| AT-003 | RAGAS bloqueia relatório de baixa qualidade | Um rascunho gerado tem faithfulness/relevancy abaixo do limiar | O gate RAGAS avalia o rascunho | O relatório **não** vira PR — é registrado em `self_healing_rejections` com motivo `low_ragas_score` |
| AT-004 | Relatório aprovado vira PR | Um rascunho passa no gate RAGAS | O evento `content_generation` é processado por `dag_self_healing_diagnose` | Os guardrails são aplicados e, se aprovado, um PR é aberto com o rascunho e as métricas RAGAS anexadas |

---

## Out of Scope

- API de consulta interativa em tempo real (Approach B do brainstorm, rejeitada)
- Notificação via webhook do SharePoint — só polling agendado
- GraphRAG / grafo de conhecimento
- Suporte multi-idioma
- Entrega via Teams/Outlook (Adaptive Cards) — só a leitura do SharePoint é desta fase; envio é Fase 5

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Technical | Databricks Vector Search depende de Unity Catalog no workspace Free Edition | Assunção de risco a validar no Design (mesma classe do MLflow na Fase 3) |
| Resource | Tenant Microsoft 365/Entra ID ainda não existe | Precisa ser provisionado (ex: Microsoft 365 Developer Program, gratuito) antes da validação real |
| Technical | RAGAS precisa de um limiar calibrado sem histórico prévio de relatórios | Design deve propor um valor de partida razoável e documentar como ajustável |

---

## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `pipelines/rag/` (novo: ingestão SharePoint, config de indexação, retrieval, fábrica de conteúdo) + extensão de `pipelines/self_healing/` | Reaproveita o pacote de self-healing, mesmo padrão da Fase 3 |
| **KB Domains** | `genai`, `prompt-engineering`, `patterns/rag`, `ai-data-engineering`, `data-quality`, `databricks` (Delta Sync Index) | Design deve consultar `rag-operating-pattern.md`, `genai/quick-reference.md` e validar Databricks Vector Search |
| **IaC Impact** | App registration Entra ID (OAuth2/Graph) + endpoint de Databricks Vector Search — nenhum provisionado ainda | Design deve validar a disponibilidade do Vector Search no Free Edition |

---

## Data Contract (if applicable)

### Source Inventory
| Source | Type | Volume | Freshness | Owner |
|--------|------|--------|-----------|-------|
| SharePoint (Microsoft Graph, delta query) | API REST real | Baixo (documentos de teste) | Polling agendado | Projeto AutoMesh |
| `gold.market_insights` (Fase 3) | Tabela Delta | Baixo (herdado) | Hourly | Projeto AutoMesh |

### Schema Contract
Exemplo representativo (`bronze.sharepoint_documents`, novo):

| Column | Type | Constraints | PII? |
|--------|------|-------------|------|
| document_id | STRING | NOT NULL | No |
| source_path | STRING | NOT NULL | No |
| chunk_index | LONG | NOT NULL | No |
| chunk_text | STRING | NOT NULL | Possível — depende do conteúdo real do documento |
| updated_at | TIMESTAMP | NOT NULL | No |

### Freshness SLAs
| Layer | Target | Measurement |
|-------|--------|-------------|
| `bronze.sharepoint_documents` | Atualizada a cada ciclo de polling (frequência a definir no Design) | Timestamp de conclusão do `dag_ingest_sharepoint_documents` vs. `updated_at` no Graph |
| Fábrica de conteúdo | Roda na mesma cadência hourly já estabelecida no projeto | Timestamp de geração do rascunho |

### Completeness Metrics
- 100% dos documentos novos/alterados detectados pelo delta query são processados e indexados
- 100% dos rascunhos gerados passam pelo gate RAGAS antes de qualquer PR — nenhum bypass

### Lineage Requirements
- Cada chunk em `bronze.sharepoint_documents` é rastreável ao `document_id`/`source_path` original no SharePoint
- Cada relatório gerado é rastreável aos outliers de `gold.market_insights` e aos documentos usados como contexto de retrieval

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|---------------------|--------------|
| A-001 | Databricks Vector Search está disponível no workspace Free Edition (depende de Unity Catalog) | Precisaria de um vector store alternativo (Qdrant local, considerado e descartado no brainstorm) | [ ] |
| A-002 | É possível provisionar um tenant Microsoft 365 Developer gratuito com um site SharePoint de teste | Precisaria de outra fonte real de documentos ou reconsiderar documentos simulados | [ ] |
| A-003 | NeMo Guardrails funciona de forma compatível com o pipeline de guardrails determinístico já existente na Fase 2, sem conflito | Pode ser necessário escopar o uso do NeMo Guardrails só para o RAG, isolado do self-healing | [ ] |

**Note:** Validate critical assumptions before DESIGN phase. Unvalidated assumptions become risks.

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Sentença única, específica, cobrindo ingestão, retrieval, geração e o gate de qualidade |
| Users | 2 | Três personas com pain points claros; "recrutador" é persona atípica para sistema técnico (mesma ressalva das fases anteriores) |
| Goals | 3 | MoSCoW aplicado a todos os goals |
| Success | 3 | Critérios com números/binários claros (100%, 0%, 1 ciclo de polling) |
| Scope | 3 | Out of scope explícito com 5 itens, cada um mapeado a uma razão concreta ou fase futura |
| **Total** | **14/15** | Acima do gate de 12/15 — pronto para Design |

**Minimum to proceed: 12/15**

---

## Open Questions

None — ready for Design. O Design deverá validar as Assumptions A-001 (Databricks Vector Search no Free Edition), A-002 (provisionamento do tenant Microsoft 365 Developer) e A-003 (compatibilidade do NeMo Guardrails com o pipeline existente), além de propor o limiar inicial de RAGAS.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|------------|
| 1.0 | 2026-08-07 | define-agent | Initial version — extraído de BRAINSTORM_FASE4_RAG_CONTEUDO.md |
| 1.1 | 2026-08-11 | ship-agent | Shipped and archived |

---

## Next Step

**Shipped** — see `SHIPPED_2026-08-11.md` in this archive folder.
