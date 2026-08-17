# DESIGN: Fase 4 — Motor RAG e Geração de Conteúdo

> Technical design for implementing the Fase 4 RAG engine (SharePoint ingestion + Databricks Vector Search + Advanced RAG) and the content factory that crosses Fase 3 outliers with retrieved documents, gated by RAGAS before any PR.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | FASE4_RAG_CONTEUDO |
| **Date** | 2026-08-10 |
| **Author** | design-agent |
| **DEFINE** | [DEFINE_FASE4_RAG_CONTEUDO.md](./DEFINE_FASE4_RAG_CONTEUDO.md) |
| **Status** | ✅ Shipped |

---

## Architecture Overview

```text
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                    FASE 4 — RAG CORPORATIVO + FÁBRICA DE CONTEÚDO                          │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│ [SharePoint / Microsoft Graph]                                                             │
│         │ delta query (MSAL client-credentials, polling 30min)                             │
│         ▼                                                                                   │
│ [dag_ingest_sharepoint_documents]                                                           │
│   graph_client.list_changed_files → chunking.chunk_document                                │
│         │                                                                                   │
│         ▼                                                                                   │
│ [contract_validator.validate_batch] (Fase 1, reaproveitado — +contracts_dir param)          │
│   valid ──► [bronze_writer.write_bronze] (Fase 1, reaproveitado, zero mudança)              │
│   invalid ──► [bronze_writer.write_dlq] (Fase 1, reaproveitado — cai na mesma DLQ do        │
│               self-healing, sem nenhuma integração nova)                                    │
│         │                                                                                    │
│         ▼                                                                                   │
│ [bronze.sharepoint_documents] (Delta) ──Delta Sync Index──► [Databricks Vector Search]      │
│                                          (vector_index.ensure_index_exists, idempotente)     │
│                                                                       │                       │
│ [gold.market_insights] (Fase 3) ──┐                                  │                       │
│                                     ├──► [dag_generate_content, hourly]                      │
│                                     │      retrieval.search_and_rerank (HYBRID + Claude       │
│                                     │      rerank) → content_factory._draft_report (Claude)   │
│                                     │      → nemo_rails.check_output → RAGAS gate             │
│                                     │                    │                                    │
│                                     │       ┌────────────┴─────────────┐                     │
│                                     │  abaixo do limiar          acima do limiar              │
│                                     │       │                          │                      │
│                                     │  [rejection_writer.write_rejection]  [failure_capture.  │
│                                     │  (Fase 2, direto — sem passar        write_event         │
│                                     │   pelo LLM diagnostician)            source_failure_type │
│                                     │       │                          =content_generation]    │
│                                     │       ▼                          │                       │
│                                     │  [self_healing_rejections]        ▼                      │
│                                     │                        [self_healing_events]             │
│                                     │                                  │                        │
│                                     │                    [dag_self_healing_diagnose]            │
│                                     │                    (Fase 2, reaproveitado — só            │
│                                     │                     resolve_diagnosis() pula o LLM         │
│                                     │                     quando o diagnóstico já vem pronto)    │
│                                     │                                  │                        │
│                                     │                    guardrails.evaluate (allowlist          │
│                                     │                    +pipelines/rag/) → github_pr            │
│                                     │                    (Fase 2, zero mudança)                  │
│                                     │                                  │                        │
│                                     │                    (revisão humana — merge nunca           │
│                                     │                     automático)                            │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| SharePoint Ingestion | Autenticação OAuth2 app-only, delta query, download, chunking | `msal`, Microsoft Graph REST API, `pypdf` |
| Bronze + DLQ (reaproveitado) | Validação de contrato + escrita Delta particionada | `pipelines/ingestion/common/*` (Fase 1, inalterado exceto 1 parâmetro opcional) |
| Vector Index | Delta Sync Index sincronizando `bronze.sharepoint_documents`; busca híbrida | Databricks Vector Search SDK |
| Retrieval | Busca híbrida (semântica+lexical nativa) + rerank por relevância | `databricks-vectorsearch`, Anthropic tool call |
| Content Factory | Cruza outliers (Fase 3) com contexto recuperado, gera rascunho, avalia RAGAS | Anthropic Claude, `ragas`, `langchain-anthropic` |
| RAG Guardrails | Input/output rails isolados do guardrail determinístico da Fase 2 | NeMo Guardrails |
| Self-Healing (reaproveitado) | Diagnóstico (bypass para conteúdo pronto), guardrail de path/conteúdo, PR | `pipelines/self_healing/common/*` (Fase 2/3, 2 diffs pequenos) |

---

## Key Decisions

### Decision 1: `resolve_diagnosis()` — bypass determinístico do LLM diagnostician para eventos com diagnóstico pronto

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-10 |

**Context:** A Fase 3 estabeleceu o precedente de "zero mudança de lógica" em `dag_self_healing_diagnose` — todo evento em `self_healing_events`, não importa o `source_failure_type`, passa por `llm_diagnostician.diagnose()`, que faz uma nova chamada à Anthropic para produzir `root_cause/fix_type/target_file/diff/explanation` a partir do campo `detail`. Isso funcionava bem para `model_promotion`/`cost_anomaly`, onde o "diff" é curto e não tem gate de qualidade anterior. Para `content_generation`, porém, o rascunho **já foi gerado e aprovado pelo gate RAGAS** antes de chegar em `self_healing_events` — se `diagnose()` chamar a LLM de novo para "reformatar" esse rascunho como um diff, o texto que vira PR pode divergir do texto que foi de fato avaliado pelo RAGAS, quebrando a garantia de fidelidade exigida pelo Success Criteria ("100% dos relatórios aprovados incluem as métricas RAGAS no corpo do PR" e "0% dos relatórios abaixo do limiar chegam a virar PR" — que só faz sentido se o PR contém *exatamente* o texto avaliado).

**Choice:** `llm_diagnostician.py` ganha uma função `resolve_diagnosis(event)`: se `event["source_failure_type"] == "content_generation"`, o `detail` (JSON) já contém `root_cause/target_file/diff/explanation` prontos — `resolve_diagnosis` só faz `json.loads` e monta o `Diagnosis` diretamente, sem chamar a API da Anthropic. Para todos os outros tipos (`contract`, `execution`, `model_promotion`, `cost_anomaly`), o comportamento é idêntico ao de hoje — chama `diagnose(event)`. `dag_self_healing_diagnose.py` troca uma linha: `diagnose(event)` → `resolve_diagnosis(event)`.

**Rationale:** Preserva o espírito da Decision 2 da Fase 3 (diff pequeno, sem duplicar guardrail+PR) e ainda garante que o conteúdo do PR seja idêntico ao conteúdo avaliado pelo RAGAS — o requisito mais importante desta fase. É uma mudança aditiva (2 linhas em `dag_self_healing_diagnose.py`, uma função nova em `llm_diagnostician.py`), não um pipeline paralelo.

**Alternatives Rejected:**
1. Manter reuso 100% "zero-change" (deixar `diagnose()` reformatar o rascunho via LLM) — rejeitado: risco real de o texto do PR divergir do texto avaliado pelo RAGAS, invalidando o gate.
2. Criar uma tabela `content_generation_events` e um DAG de aprovação próprio — rejeitado: duplicaria guardrail+PR já testados nas Fases 2-3, mesmo argumento da Decision 2 da Fase 3.

**Consequences:**
- `resolve_diagnosis()` é o único ponto de entrada testável para essa decisão (mockável sem Airflow), coberto por `test_llm_diagnostician.py`.
- Futuros tipos de evento com diagnóstico pré-computado (ex.: uma Fase 5 que já sabe o `target_file`/`diff` de antemão) reaproveitam o mesmo mecanismo sem precisar de um novo `if`.

---

### Decision 2: Gate RAGAS roda dentro do `content_factory`, antes de qualquer escrita em `self_healing_events`

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-10 |

**Context:** O DEFINE (AT-003) exige que relatórios abaixo do limiar caiam direto em `self_healing_rejections`, sem nunca chegar a virar PR. O ponto onde essa decisão pode ser tomada com menor custo e maior clareza é logo após o RAGAS avaliar o rascunho — antes de qualquer chamada adicional à Anthropic (via `resolve_diagnosis`) ou ao GitHub.

**Choice:** `content_factory.process_outlier()` chama `rejection_writer.write_rejection(source_failure_type="content_generation", rejection_reason="low_ragas_score", ...)` diretamente quando o gate reprova — sem passar por `dag_self_healing_diagnose`. Só rascunhos aprovados viram evento em `self_healing_events`.

**Rationale:** Evita custo e latência de diagnosticar/guardrail um rascunho que já sabemos que será descartado; mantém `self_healing_rejections` como o único lugar de "não virou PR", consistente com o padrão já usado pelo guardrail determinístico da Fase 2.

**Alternatives Rejected:**
1. Sempre escrever em `self_healing_events` e deixar o guardrail da Fase 2 decidir com base no score RAGAS — rejeitado: o guardrail da Fase 2 (`guardrails.py`) avalia `target_file`/`diff` (segurança de path/conteúdo), não é o lugar certo para uma decisão de qualidade de conteúdo.

**Consequences:**
- `content_factory.py` importa tanto `rejection_writer` quanto `failure_capture.write_event` (Fase 2/3) — nenhuma tabela nova.
- O corpo do PR (quando aprovado) inclui as métricas RAGAS embutidas em `explanation` — nenhuma mudança em `github_pr.py`.

---

### Decision 3: Databricks Vector Search (Delta Sync Index) com busca híbrida nativa (`query_type="HYBRID"`), sem lexical search custom

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-10 |

**Context:** O DEFINE exige retrieval combinando busca semântica e lexical (AT-002), reaproveitando o workspace Databricks já usado nas Fases 2-3. A Assumption A-001 do DEFINE identifica que o Vector Search depende de Unity Catalog, ainda não validado no Free Edition — mesma classe de risco do MLflow na Fase 3 (que foi validado com sucesso via `docker-compose.local.yml` + SQLite local, mas o workspace real nunca foi provisionado).

**Choice:** `vector_index.py` usa `databricks.vector_search.client.VectorSearchClient.create_delta_sync_index` (Delta Sync Index sobre `bronze.sharepoint_documents`, elimina job de embedding manual) e `index.similarity_search(..., query_type="HYBRID")` para combinar ANN semântico + BM25 lexical nativamente, sem implementar busca lexical própria.

**Rationale:** Consistente com a Decision 3 do brainstorm (reaproveitar o workspace, eliminar job de embedding manual) e com o padrão `databricks/patterns/ai-ml-patterns.md`. Reduz superfície de código: sem essa escolha, seria necessário manter um índice lexical (ex.: BM25 local) e um passo de fusão de ranking à parte.

**Alternatives Rejected:**
1. Qdrant local via Docker — considerado e descartado já no brainstorm (serviço novo, sem precedente no projeto).
2. Lexical search custom (BM25 local) + fusão manual de ranking com o resultado semântico — rejeitado: reimplementa o que o Vector Search já oferece nativamente via `query_type="HYBRID"`.

**Consequences:**
- **Risco não resolvido nesta fase:** a disponibilidade real de Vector Search/Unity Catalog no Free Edition segue como assunção a validar no Build/validação real (mesma classe de risco que MLflow na Fase 3) — se indisponível, o fallback documentado é reavaliar Qdrant local só então, não antecipar a complexidade agora.
- `ensure_index_exists()` precisa ser idempotente (checa existência antes de criar) porque roda a cada execução do DAG de ingestão.

---

### Decision 4: Rerank via Claude (tool call), não um reranker dedicado

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-10 |

**Context:** Advanced RAG (escolhido no brainstorm) exige um passo de rerank entre a busca híbrida e a síntese. O projeto já depende da API da Anthropic (self-healing, Fase 2) e evita introduzir infraestrutura nova sem necessidade (mesmo princípio da Decision 3).

**Choice:** `retrieval.rerank()` pede à Claude, via tool call estruturado (mesmo padrão de `llm_diagnostician.DIAGNOSIS_TOOL`), um score de relevância 0-1 por chunk candidato; os candidatos são reordenados por esse score e truncados em `RAG_RERANK_TOP_N`.

**Rationale:** Zero infraestrutura nova (nenhum modelo de cross-encoder para hospedar, nenhuma chave de API adicional como Cohere Rerank) — reaproveita a mesma dependência (`ANTHROPIC_API_KEY`) e o mesmo padrão de tool call já testado na Fase 2.

**Alternatives Rejected:**
1. Cohere Rerank API — rejeitado: novo vendor, novo segredo, sem precedente no projeto.
2. Cross-encoder open-source (ex.: `sentence-transformers` CrossEncoder) hospedado localmente — rejeitado: adiciona superfície de operação (carregar/servir um modelo) desproporcional ao volume baixo de documentos do projeto (mesmo raciocínio de custo/complexidade da FinOps da Fase 3).

**Consequences:**
- Latência e custo de rerank são uma chamada extra à Anthropic por query — aceitável dado o volume baixo (mesmo perfil de portfólio das fases anteriores).
- `RERANK_TOOL`/prompt precisam ser validados/ajustados durante o Build contra respostas reais (mesma prática de `DIAGNOSIS_TOOL` na Fase 2).

---

### Decision 5: Cursor do Graph delta query em tabela dedicada (`delta_cursor.py`), não reaproveitando `checkpoint.py` da Fase 2

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-10 |

**Context:** `pipelines/self_healing/common/checkpoint.py` já implementa um cursor genérico (`get_checkpoint(source) -> datetime` / `set_checkpoint(source, ts)`), reaproveitável em princípio. Mas o Microsoft Graph delta query retorna um `@odata.deltaLink` (string opaca), não um timestamp — o schema do `checkpoint.py` (`last_processed_at: datetime`) não comporta esse tipo sem alterá-lo.

**Choice:** Criar `pipelines/rag/common/delta_cursor.py`, mesmo padrão estrutural de `checkpoint.py` (tabela Delta de 1 linha por `source`, leitura/escrita via `deltalake`), mas guardando `delta_link: string` em vez de timestamp. Cursores baseados em timestamp (ex.: consumo de `gold.market_insights` pelo content factory) continuam reaproveitando `checkpoint.py` sem modificação.

**Rationale:** Alterar `checkpoint.py` para aceitar tanto `datetime` quanto `string` misturaria dois conceitos num só módulo testado e em produção (Fase 2/3) por um ganho de reuso marginal. Duplicar a *estrutura* (não a lógica de negócio) é mais barato e mais seguro do que generalizar um módulo já estável.

**Alternatives Rejected:**
1. Guardar o `delta_link` serializado dentro do campo `last_processed_at` como string — rejeitado: quebra o contrato de tipo do `checkpoint.py`, frágil.
2. Ignorar delta query e usar filtro `lastModifiedDateTime gt {checkpoint}` (reaproveitando `checkpoint.py` como está) — rejeitado: o DEFINE nomeia explicitamente "Graph delta query" como MUST; um filtro por timestamp é semanticamente mais frágil (não garante consistência transacional de mudanças) e a Graph API já resolve isso de graça via `@odata.deltaLink`.

**Consequences:**
- Mais um arquivo pequeno (~30 linhas), mas nenhuma mudança de risco em `checkpoint.py`, que já protege 2 fluxos testados (Fase 2/3).

---

### Decision 6: NeMo Guardrails isolado em `pipelines/rag/`, sem tocar no guardrail determinístico da Fase 2

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-10 |

**Context:** O `context.md` original prevê NeMo Guardrails para o motor RAG. A Fase 2 tomou a decisão deliberada de guardrails 100% custom (allowlist de path + padrões de conteúdo perigoso) para o mecanismo de PR — decisão reafirmada e mantida aqui. O usuário confirmou no brainstorm (decisão 6) que quer os dois: NeMo Guardrails para o RAG, guardrail custom para o PR.

**Choice:** `pipelines/rag/common/nemo_rails.py` encapsula `RailsConfig`/`LLMRails` do NeMo Guardrails, com rails de entrada (query antes do retrieval) e saída (rascunho antes do gate RAGAS). `pipelines/self_healing/common/guardrails.py` não é tocado em lógica — só ganha o prefixo `pipelines/rag/` na allowlist de paths (mesmo padrão aditivo da Decision 4 da Fase 3).

**Rationale:** Mantém as duas filosofias de guardrail que o projeto já decidiu adotar em momentos diferentes, cada uma no escopo certo — o guardrail determinístico da Fase 2 continua sendo a última linha de defesa antes de qualquer PR (para *qualquer* tipo de evento), e o NeMo Guardrails cobre um problema diferente (conteúdo de entrada/saída do RAG, não segurança de diff/path).

**Alternatives Rejected:**
1. Estender o guardrail custom da Fase 2 para cobrir também segurança de conteúdo RAG — rejeitado: decisão explícita do usuário de usar o framework original do `context.md` especificamente para esta peça.

**Consequences:**
- Nova dependência (`nemoguardrails`) isolada no `requirements.txt` do pacote `rag`, sem afetar `pipelines/self_healing/requirements.txt`.
- A configuração exata do NeMo Guardrails (Colang rails) é um MVP mínimo nesta fase — expansão de regras fica para trabalho futuro (não é MUST do DEFINE).

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `pipelines/rag/__init__.py` | Create | Scaffolding do pacote | (general) | None |
| 2 | `pipelines/rag/requirements.txt` | Create | `msal`, `pypdf`, `databricks-vectorsearch`, `ragas`, `langchain-anthropic`, `datasets`, `nemoguardrails`, `deltalake`, `pyarrow`, `pyyaml` | (general) | None |
| 3 | `pipelines/rag/config/rag_config.yaml` | Create | Tunáveis: thresholds RAGAS, chunking, retrieval, schedules | @data-contracts-engineer | None |
| 4 | `pipelines/rag/contracts/sharepoint_documents.contract.yaml` | Create | Contrato ODCS-lite de `bronze.sharepoint_documents` | @data-contracts-engineer | None |
| 5 | `pipelines/rag/common/__init__.py` | Create | Scaffolding | (general) | None |
| 6 | `pipelines/rag/common/graph_client.py` | Create | MSAL client-credentials + Graph delta query + download | @security-reviewer | None |
| 7 | `pipelines/rag/common/delta_cursor.py` | Create | Cursor `delta_link` (ver Decision 5) | @lakehouse-architect | None |
| 8 | `pipelines/rag/common/chunking.py` | Create | Extração de texto (PDF/texto) + chunking | @ai-data-engineer | None |
| 9 | `pipelines/rag/common/vector_index.py` | Create | Delta Sync Index (create/ensure) + busca híbrida | @ai-data-engineer | None |
| 10 | `pipelines/rag/common/nemo_rails.py` | Create | Input/output rails (NeMo Guardrails), ver Decision 6 | @genai-architect | None |
| 11 | `pipelines/rag/config/guardrails/config.yml` | Create | Config Colang mínima do NeMo Guardrails | @genai-architect | 10 |
| 12 | `pipelines/rag/jobs/__init__.py` | Create | Scaffolding | (general) | None |
| 13 | `pipelines/rag/jobs/ingest_sharepoint.py` | Create | Orquestra delta query → chunk → contrato → bronze/DLQ → índice | @ai-data-engineer | 4, 6, 7, 8, 9 |
| 14 | `pipelines/rag/jobs/retrieval.py` | Create | Busca híbrida + rerank via Claude (Decision 4) | @genai-architect | 9 |
| 15 | `pipelines/rag/jobs/content_factory.py` | Create | Cruza outliers + retrieval → rascunho → NeMo output rail → gate RAGAS → evento/rejeição | @genai-architect | 10, 14 |
| 16 | `pipelines/rag/dags/__init__.py` | Create | Scaffolding | (general) | None |
| 17 | `pipelines/rag/dags/dag_ingest_sharepoint_documents.py` | Create | DAG de polling (30min) | @airflow-specialist | 13 |
| 18 | `pipelines/rag/dags/dag_generate_content.py` | Create | DAG hourly da fábrica de conteúdo | @airflow-specialist | 15 |
| 19 | `pipelines/rag/tests/__init__.py` | Create | Scaffolding | (general) | None |
| 20 | `pipelines/rag/tests/test_graph_client.py` | Create | MSAL/Graph mockados | @test-generator | 6 |
| 21 | `pipelines/rag/tests/test_chunking.py` | Create | Extração/chunking | @test-generator | 8 |
| 22 | `pipelines/rag/tests/test_retrieval.py` | Create | Rerank (LLM mockado) + hybrid search (client mockado) — cobre AT-002 | @test-generator | 14 |
| 23 | `pipelines/rag/tests/test_content_factory.py` | Create | Ramos aprovado/reprovado do gate RAGAS (mockado) — cobre AT-003, AT-004 | @test-generator | 15 |
| 24 | `pipelines/rag/tests/test_dags_integrity.py` | Create | Import + IDs dos 2 DAGs novos | @test-generator | 17, 18 |
| 25 | `pipelines/ingestion/common/contract_validator.py` | Modify | +parâmetro opcional `contracts_dir` (permite `pipelines/rag/contracts/`) | @data-contracts-engineer | None |
| 26 | `pipelines/ingestion/tests/test_contract_validator.py` | Modify | +teste do parâmetro `contracts_dir` | @test-generator | 25 |
| 27 | `pipelines/self_healing/common/guardrails.py` | Modify | +prefixo `pipelines/rag/` na allowlist | @security-reviewer | None |
| 28 | `pipelines/self_healing/common/llm_diagnostician.py` | Modify | +`resolve_diagnosis()` (Decision 1) | @genai-architect | None |
| 29 | `pipelines/self_healing/dags/dag_self_healing_diagnose.py` | Modify | `diagnose(event)` → `resolve_diagnosis(event)` | @airflow-specialist | 28 |
| 30 | `pipelines/self_healing/tests/test_guardrails.py` | Modify | +teste do prefixo `rag/` | @test-generator | 27 |
| 31 | `pipelines/self_healing/tests/test_llm_diagnostician.py` | Modify | +testes de `resolve_diagnosis` (bypass vs. LLM) | @test-generator | 28 |

**Total Files:** 31 (24 novos + 7 modificados) — mais os `__init__.py` de scaffolding já listados individualmente (padrão diferente das Fases 1-3 porque o pacote `rag/` é criado do zero nesta fase).

---

## Agent Assignment Rationale

> Agentes descobertos em `.claude/agents/**/*.md` — mapeamento mantém a mesma correspondência já usada nas Fases 2-3 para os módulos de self-healing reaproveitados/estendidos (`checkpoint.py`→`@lakehouse-architect`, `guardrails.py`→`@security-reviewer`, `llm_diagnostician.py`→`@genai-architect`, DAGs→`@airflow-specialist`), estendida aos módulos novos do pacote `rag/`.

| Agent | Files Assigned | Why This Agent |
|-------|----------------|-----------------|
| @security-reviewer | 6, 27 | OAuth2/Microsoft Graph é citado explicitamente no CLAUDE.md como escopo deste agente; allowlist de guardrail é segurança de path/conteúdo |
| @ai-data-engineer | 8, 9, 13 | RAG pipelines, vector databases — escopo central do agente |
| @genai-architect | 10, 11, 14, 15, 28 | Guardrails (NeMo), roteamento/orquestração LLM, rerank e geração de conteúdo — mesmo agente que fez `llm_diagnostician.py` na Fase 2 |
| @lakehouse-architect | 7 | Cursor sobre tabela Delta — mesmo agente do `checkpoint.py` da Fase 2 |
| @airflow-specialist | 17, 18, 29 | DAGs Airflow 3.0 — mesmo agente das Fases 1-3 |
| @data-contracts-engineer | 3, 4, 25 | Contratos ODCS-lite + configuração de tunáveis |
| @test-generator | 20, 21, 22, 23, 24, 26, 30, 31 | Todos os testes pytest do projeto |
| (general) | 1, 2, 5, 12, 16, 19 | Scaffolding de pacote (`__init__.py`, `requirements.txt`) — mesmo padrão das Fases 1-3 |

**Agent Discovery:**
- Escaneado: `.claude/agents/**/*.md`
- Casado por: tipo de arquivo, palavras-chave de propósito, domínio KB, e precedente direto das Fases 2-3 para os módulos reaproveitados

---

## Code Patterns

### Pattern 1: OAuth2 app-only + Graph delta query (`graph_client.py`)

```python
from __future__ import annotations

import os

import msal
import requests

GRAPH_TENANT_ID = os.environ["GRAPH_TENANT_ID"]
GRAPH_CLIENT_ID = os.environ["GRAPH_CLIENT_ID"]
GRAPH_CLIENT_SECRET = os.environ["GRAPH_CLIENT_SECRET"]
GRAPH_SITE_ID = os.environ["GRAPH_SITE_ID"]
GRAPH_DRIVE_ID = os.environ["GRAPH_DRIVE_ID"]
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
REQUEST_TIMEOUT_SECONDS = 30


def _access_token() -> str:
    app = msal.ConfidentialClientApplication(
        GRAPH_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{GRAPH_TENANT_ID}",
        client_credential=GRAPH_CLIENT_SECRET,
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise RuntimeError(f"Graph auth failed: {result.get('error_description')}")
    return result["access_token"]


def list_changed_files(delta_link: str | None = None) -> tuple[list[dict], str]:
    """Segue @odata.nextLink até esgotar a página; retorna (itens, novo @odata.deltaLink)."""
    next_link = delta_link or (
        f"{GRAPH_API_BASE}/sites/{GRAPH_SITE_ID}/drives/{GRAPH_DRIVE_ID}/root/delta"
    )
    headers = {"Authorization": f"Bearer {_access_token()}"}
    items: list[dict] = []
    body: dict = {}
    while next_link:
        resp = requests.get(next_link, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        body = resp.json()
        items.extend(item for item in body.get("value", []) if "file" in item)
        next_link = body.get("@odata.nextLink")
    return items, body.get("@odata.deltaLink", delta_link or "")


def download_file_content(download_url: str) -> bytes:
    resp = requests.get(download_url, timeout=REQUEST_TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.content
```

### Pattern 2: Delta Sync Index — criação idempotente + busca híbrida (`vector_index.py`)

```python
# `databricks.vector_search` é importado lazy dentro das funções — mesmo motivo do
# import lazy de `anthropic`/`mlflow` nas Fases 2-3: evita estourar o timeout de parse
# de DAG do Airflow (ver BUILD_REPORT_FASE2, bug real encontrado).
from __future__ import annotations

import os

VECTOR_SEARCH_ENDPOINT = os.environ.get("VECTOR_SEARCH_ENDPOINT", "automesh-rag-endpoint")
VECTOR_SEARCH_INDEX = os.environ.get("VECTOR_SEARCH_INDEX", "main.rag.sharepoint_documents_index")
SOURCE_TABLE = os.environ.get("SHAREPOINT_DOCUMENTS_TABLE", "main.rag.sharepoint_documents")


def ensure_index_exists() -> None:
    from databricks.vector_search.client import VectorSearchClient

    client = VectorSearchClient()
    existing = {idx["name"] for idx in client.list_indexes(VECTOR_SEARCH_ENDPOINT).get("vector_indexes", [])}
    if VECTOR_SEARCH_INDEX in existing:
        return

    client.create_delta_sync_index(
        endpoint_name=VECTOR_SEARCH_ENDPOINT,
        index_name=VECTOR_SEARCH_INDEX,
        primary_key="document_id",
        delta_sync_index_config={
            "data_objects": [
                {
                    "table_name": SOURCE_TABLE,
                    "text_search_config": {"field_name": "chunk_text", "chunk_template": "{{chunk_text}}"},
                    "embedding_source_columns": ["chunk_text"],
                    "embedding_model": "databricks-bge-large-en",
                }
            ]
        },
    )


def hybrid_search(query_text: str, num_results: int = 10) -> list[dict]:
    from databricks.vector_search.client import VectorSearchClient

    client = VectorSearchClient()
    index = client.get_index(VECTOR_SEARCH_ENDPOINT, VECTOR_SEARCH_INDEX)
    results = index.similarity_search(
        query_text=query_text,
        columns=["document_id", "source_path", "chunk_text"],
        num_results=num_results,
        query_type="HYBRID",  # semântico (ANN) + lexical (BM25) nativos — ver Decision 3
    )
    columns = [c["name"] for c in results["manifest"]["columns"]]
    return [dict(zip(columns, row)) for row in results["result"]["data_array"]]
```

### Pattern 3: Rerank via Claude tool call (`retrieval.py`)

```python
from __future__ import annotations

import os

from pipelines.rag.common.vector_index import hybrid_search

RETRIEVAL_CANDIDATES = int(os.environ.get("RAG_RETRIEVAL_CANDIDATES", "10"))
RERANK_TOP_N = int(os.environ.get("RAG_RERANK_TOP_N", "4"))

RERANK_TOOL = {
    "name": "score_relevance",
    "description": "Atribui um score de relevância 0-1 para cada chunk em relação à query, na mesma ordem recebida",
    "input_schema": {
        "type": "object",
        "properties": {"scores": {"type": "array", "items": {"type": "number"}}},
        "required": ["scores"],
    },
}


def rerank(query: str, candidates: list[dict], client=None) -> list[dict]:
    import anthropic

    if not candidates:
        return []

    client = client or anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    numbered = "\n".join(f"{i}: {c['chunk_text'][:500]}" for i, c in enumerate(candidates))
    response = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
        max_tokens=1024,
        tools=[RERANK_TOOL],
        tool_choice={"type": "tool", "name": "score_relevance"},
        messages=[{"role": "user", "content": f"Query: {query}\n\nChunks:\n{numbered}"}],
    )
    tool_use = next(b for b in response.content if b.type == "tool_use")
    scored = sorted(zip(candidates, tool_use.input["scores"]), key=lambda pair: pair[1], reverse=True)
    return [chunk for chunk, _ in scored]


def search_and_rerank(query: str) -> list[dict]:
    candidates = hybrid_search(query, num_results=RETRIEVAL_CANDIDATES)
    return rerank(query, candidates)[:RERANK_TOP_N]
```

### Pattern 4: Gate RAGAS + decisão evento/rejeição (`content_factory.py`)

```python
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from pipelines.rag.common.nemo_rails import check_output
from pipelines.rag.jobs.retrieval import search_and_rerank
from pipelines.self_healing.common.failure_capture import write_event
from pipelines.self_healing.common.rejection_writer import write_rejection

# `anthropic`/`ragas`/`langchain_anthropic` são importados lazy dentro das funções —
# mesmo motivo documentado em llm_diagnostician.py (Fase 2): evita estourar o timeout
# de parse de DAG do Airflow com imports pesados carregados no nível do módulo.
RAGAS_FAITHFULNESS_THRESHOLD = float(os.environ.get("RAGAS_FAITHFULNESS_THRESHOLD", "0.7"))
RAGAS_RELEVANCY_THRESHOLD = float(os.environ.get("RAGAS_ANSWER_RELEVANCY_THRESHOLD", "0.7"))


def _draft_report(outlier: dict, chunks: list[dict], client=None) -> str:
    import anthropic

    client = client or anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    context = "\n\n".join(f"[{c['source_path']}] {c['chunk_text']}" for c in chunks)
    prompt = (
        "Escreva um rascunho de relatório executivo cruzando o outlier de mercado abaixo "
        "com o contexto documental do SharePoint. Cite a fonte de cada afirmação.\n\n"
        f"Outlier: {json.dumps(outlier, default=str)}\n\nContexto:\n{context}"
    )
    response = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _evaluate_ragas(question: str, answer: str, contexts: list[str]) -> dict:
    from datasets import Dataset
    from langchain_anthropic import ChatAnthropic
    from ragas import evaluate
    from ragas.embeddings import HuggingfaceEmbeddings
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import answer_relevancy, faithfulness

    evaluator_llm = LangchainLLMWrapper(ChatAnthropic(model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")))
    evaluator_embeddings = HuggingfaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    dataset = Dataset.from_dict({"question": [question], "answer": [answer], "contexts": [contexts]})
    scores = evaluate(
        dataset, metrics=[faithfulness, answer_relevancy], llm=evaluator_llm, embeddings=evaluator_embeddings
    )
    return {"faithfulness": float(scores["faithfulness"]), "answer_relevancy": float(scores["answer_relevancy"])}


def process_outlier(outlier: dict) -> str:
    query = f"{outlier.get('source_ticker', '')} anomaly_score={outlier.get('anomaly_score', '')}"
    chunks = search_and_rerank(query)

    draft = _draft_report(outlier, chunks)
    draft = check_output(draft, context={"retrieved_chunks": chunks})  # NeMo output rail — ver Decision 6

    ragas_scores = _evaluate_ragas(question=query, answer=draft, contexts=[c["chunk_text"] for c in chunks])
    passed = (
        ragas_scores["faithfulness"] >= RAGAS_FAITHFULNESS_THRESHOLD
        and ragas_scores["answer_relevancy"] >= RAGAS_RELEVANCY_THRESHOLD
    )

    if not passed:
        # Reprovado: cai direto em self_healing_rejections — nunca passa pelo LLM
        # diagnostician nem pelo guardrail de PR (ver Decision 2).
        write_rejection(source_failure_type="content_generation", rejection_reason="low_ragas_score", proposed_diff=draft)
        return "rejected:low_ragas_score"

    report_id = f"{outlier['insight_id']}-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}"
    payload = {
        "root_cause": "content_generation",
        "target_file": f"pipelines/rag/reports/{report_id}.md",
        "diff": draft,  # texto exato avaliado pelo RAGAS — resolve_diagnosis() não regenera (Decision 1)
        "explanation": (
            f"Relatório gerado cruzando outlier {outlier['insight_id']} com {len(chunks)} documento(s) "
            f"do SharePoint. RAGAS: faithfulness={ragas_scores['faithfulness']:.2f}, "
            f"answer_relevancy={ragas_scores['answer_relevancy']:.2f} "
            f"(limiares: {RAGAS_FAITHFULNESS_THRESHOLD}/{RAGAS_RELEVANCY_THRESHOLD})."
        ),
    }
    event_id = write_event(
        source="dag_generate_content", detail=json.dumps(payload), source_failure_type="content_generation"
    )
    return f"queued:{event_id}"
```

### Pattern 5: `resolve_diagnosis()` — diff em `llm_diagnostician.py` (Decision 1)

```python
# Adição a pipelines/self_healing/common/llm_diagnostician.py — resto do arquivo inalterado.
import json


def resolve_diagnosis(event: dict, client: anthropic.Anthropic | None = None) -> Diagnosis:
    """Eventos com diagnóstico pronto (ex.: content_generation, já aprovado pelo gate RAGAS)
    pulam a chamada à LLM — o PR precisa conter exatamente o texto já avaliado."""
    if event.get("source_failure_type") == "content_generation":
        payload = json.loads(event["detail"])
        return Diagnosis(fix_type="content", **payload)
    return diagnose(event, client)
```

```python
# Diff em pipelines/self_healing/dags/dag_self_healing_diagnose.py — 2 linhas:
- from pipelines.self_healing.common.llm_diagnostician import diagnose
+ from pipelines.self_healing.common.llm_diagnostician import resolve_diagnosis
...
-        diagnosis = diagnose(event)
+        diagnosis = resolve_diagnosis(event)
```

### Pattern 6: Reuso de `contract_validator`/`bronze_writer` (Fase 1, zero/mínima mudança)

```python
# pipelines/rag/jobs/ingest_sharepoint.py (trecho) — a Fase 1 já fez o trabalho pesado.
from pathlib import Path

from pipelines.ingestion.common.bronze_writer import write_bronze, write_dlq
from pipelines.ingestion.common.contract_validator import validate_batch

RAG_CONTRACTS_DIR = Path(__file__).resolve().parent.parent / "contracts"
SOURCE = "sharepoint_documents"

valid, invalid = validate_batch(SOURCE, all_chunks, contracts_dir=RAG_CONTRACTS_DIR)
write_bronze(SOURCE, valid)   # particiona por ingestion_date automaticamente — sem mudança
write_dlq(SOURCE, invalid)    # cai na mesma DLQ que dag_self_healing_diagnose já lê — zero
                               # integração nova, o self-healing já processa contract failures
                               # de qualquer `source`.
```

```python
# Diff mínimo em pipelines/ingestion/common/contract_validator.py:
-def _load_contract(source: str) -> dict:
-    path = CONTRACTS_DIR / f"{source}.contract.yaml"
+def _load_contract(source: str, contracts_dir: Path | None = None) -> dict:
+    path = (contracts_dir or CONTRACTS_DIR) / f"{source}.contract.yaml"
     with path.open(encoding="utf-8") as f:
         return yaml.safe_load(f)

-def validate_batch(source: str, records: list[dict]) -> tuple[list[dict], list[dict]]:
-    contract = _load_contract(source)
+def validate_batch(source: str, records: list[dict], contracts_dir: Path | None = None) -> tuple[list[dict], list[dict]]:
+    contract = _load_contract(source, contracts_dir)
```

### Pattern 7: Configuração (`rag_config.yaml`)

```yaml
retrieval:
  candidates: 10
  rerank_top_n: 4
chunking:
  chunk_size: 1000
  chunk_overlap: 200
ragas:
  faithfulness_threshold: 0.7
  answer_relevancy_threshold: 0.7
vector_search:
  endpoint_name: automesh-rag-endpoint
  index_name: main.rag.sharepoint_documents_index
  embedding_model: databricks-bge-large-en
sharepoint:
  polling_schedule: "*/30 * * * *"
content_factory:
  schedule: "@hourly"
```

---

## Data Flow

```text
1. dag_ingest_sharepoint_documents (polling 30min)
   │
   ▼
2. graph_client.list_changed_files(delta_link) — Graph delta query (MSAL app-only)
   │
   ▼
3. chunking.chunk_document — extrai texto (PDF/texto) + chunking (1000/200)
   │
   ▼
4. contract_validator.validate_batch("sharepoint_documents", contracts_dir=rag/contracts)
   │
   ├── válido ──► bronze_writer.write_bronze ──► bronze.sharepoint_documents (Delta)
   │                                                       │
   │                                          Delta Sync Index (auto-sync, sem job de embedding)
   │                                                       ▼
   │                                          Databricks Vector Search
   │
   └── inválido ──► bronze_writer.write_dlq ──► bronze_dlq (mesma DLQ do self-healing,
                                                  Fase 2 processa automaticamente — zero
                                                  integração nova)
   │
   ▼
5. delta_cursor.set_delta_link — avança o cursor

6. dag_generate_content (hourly)
   │
   ▼
7. Lê outliers recentes de gold.market_insights (cursor via checkpoint.py, Fase 2, reaproveitado)
   │
   ▼
8. retrieval.search_and_rerank — vector_index.hybrid_search (HYBRID) + rerank (Claude)
   │
   ▼
9. content_factory._draft_report — Claude gera rascunho citando fontes
   │
   ▼
10. nemo_rails.check_output — output rail (NeMo Guardrails)
    │
    ▼
11. _evaluate_ragas — faithfulness + answer_relevancy
    │
    ├── abaixo do limiar ──► rejection_writer.write_rejection ──► self_healing_rejections
    │
    └── acima do limiar ──► failure_capture.write_event(content_generation) ──► self_healing_events
                                     │
                                     ▼
12. dag_self_healing_diagnose (Fase 2, reaproveitado)
    │
    ▼
13. resolve_diagnosis(event) — bypass do LLM, diagnóstico já pronto (Decision 1)
    │
    ▼
14. guardrails.evaluate(target_file, diff) — allowlist +pipelines/rag/ (Fase 2, reaproveitado)
    │
    ├── rejeitado ──► self_healing_rejections
    │
    └── aprovado ──► github_pr.propose_fix_as_pr ──► PR no GitHub (revisão humana obrigatória)
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|-------------------|------------------|
| Microsoft Graph (SharePoint) | REST API (delta query) | OAuth2 client-credentials (`msal`), app registration Entra ID |
| Databricks Vector Search | SDK (`databricks-vectorsearch`) | Databricks PAT/service principal — mesma Connection reaproveitada das Fases 2-3 |
| Anthropic Claude | SDK (`anthropic`) | `ANTHROPIC_API_KEY` (reaproveitado das Fases 2-3) |
| RAGAS evaluator LLM | `langchain-anthropic` (wrapper sobre a mesma API Anthropic) | `ANTHROPIC_API_KEY` (mesmo segredo, sem credencial nova) |
| GitHub | REST API | `GITHUB_TOKEN` (reaproveitado, Fase 2) — `github_pr.py` inalterado |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|----------------|
| Unit | `chunking.extract_text`/`chunk_text` | `tests/test_chunking.py` | pytest | 80% |
| Unit | `graph_client` — token/delta query/download (Graph mockado) | `tests/test_graph_client.py` | pytest + mock `requests`/`msal` | 80% — cobre AT-001 |
| Unit | `contract_validator` com `contracts_dir` custom | `pipelines/ingestion/tests/test_contract_validator.py` (estendido) | pytest | 80% |
| Unit | `retrieval.rerank`/`search_and_rerank` (LLM + Vector Search client mockados) | `tests/test_retrieval.py` | pytest + mock | 80% — cobre AT-002 |
| Unit | `content_factory.process_outlier` — ramos aprovado/reprovado (RAGAS mockado) | `tests/test_content_factory.py` | pytest + mock | 80% — cobre AT-003, AT-004 |
| Unit | `resolve_diagnosis` — bypass content_generation vs. `diagnose()` padrão | `pipelines/self_healing/tests/test_llm_diagnostician.py` (estendido) | pytest + mock | 80% — cobre AT-004 |
| Unit | `guardrails.check_allowlist` — prefixo `pipelines/rag/` | `pipelines/self_healing/tests/test_guardrails.py` (estendido) | pytest | 80% |
| Integration | Import + IDs dos 2 DAGs novos | `tests/test_dags_integrity.py` | pytest + `importorskip("airflow")` | Key paths |
| E2E | Documento novo no SharePoint → ingestão → índice → fábrica de conteúdo → PR revisado | Manual (após provisionar o tenant Microsoft 365 Developer) | - | Happy path, AT-001 a AT-004 |

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|----------------------|--------|
| Falha de autenticação/HTTP no Graph API | Propaga exceção — política de retry do Airflow (`RETRY_ARGS`, mesma das Fases 1-3) | Yes |
| Download de um arquivo específico falha | Loga aviso, pula esse item, continua o lote (mesmo espírito do split válido/inválido do `contract_validator`) | No (item pulado, não bloqueia o lote) |
| `ensure_index_exists` — índice já existe | Checagem idempotente antes de criar — não é erro | N/A |
| Falha na avaliação RAGAS (dataset malformado, etc.) | Propaga exceção, falha a task visivelmente — o gate de qualidade nunca pode ser contornado silenciosamente | Yes (retry do Airflow) |
| `write_event`/`write_rejection` falha em `content_factory` | **Diferente da Fase 2** (`on_task_failure`, que loga e não propaga para não mascarar a falha original): aqui a escrita do evento **é** o entregável — falha propaga e o Airflow retenta a task | Yes |
| `bronze_writer.write_dlq` falha ao gravar contract failures | Mesma política já validada na Fase 1/2 — loga e não propaga (evita quebrar o DAG de ingestão por um problema na DLQ) | No |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|----------------|
| `GRAPH_TENANT_ID` / `GRAPH_CLIENT_ID` / `GRAPH_CLIENT_SECRET` | string | (obrigatório) | Credenciais do app registration Entra ID (OAuth2 client-credentials) |
| `GRAPH_SITE_ID` / `GRAPH_DRIVE_ID` | string | (obrigatório) | Site/drive do SharePoint alvo |
| `RAG_DELTA_CURSOR_PATH` | string | `data/rag/sharepoint_delta_cursor` | Tabela Delta do cursor de delta query |
| `VECTOR_SEARCH_ENDPOINT` | string | `automesh-rag-endpoint` | Endpoint do Databricks Vector Search |
| `VECTOR_SEARCH_INDEX` | string | `main.rag.sharepoint_documents_index` | Nome do Delta Sync Index |
| `RAG_RETRIEVAL_CANDIDATES` | int | `10` | Candidatos retornados pela busca híbrida antes do rerank |
| `RAG_RERANK_TOP_N` | int | `4` | Chunks finais após rerank, usados na síntese |
| `RAGAS_FAITHFULNESS_THRESHOLD` | float | `0.7` | Limiar mínimo de faithfulness (gate bloqueante) |
| `RAGAS_ANSWER_RELEVANCY_THRESHOLD` | float | `0.7` | Limiar mínimo de answer relevancy (gate bloqueante) |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` | string | (reaproveitado da Fase 2) | Draft, rerank e RAGAS evaluator LLM |

---

## Security Considerations

- `GRAPH_CLIENT_SECRET` segue a mesma política de segredo do `GITHUB_TOKEN`/`ANTHROPIC_API_KEY` — variável de ambiente/Airflow Connection, nunca logado.
- App registration Entra ID escopado a `Sites.Read.All`/`Files.Read.All` (somente leitura) — sem permissão de escrita no SharePoint, mesmo com o escopo da Fase 5 já reservado no mesmo app (Decision confirmada no brainstorm).
- `guardrails.check_content` (Fase 2, inalterado) já bloqueia padrões de segredo/código perigoso em qualquer diff — se aplica automaticamente aos rascunhos de relatório também, sem código novo.
- NeMo Guardrails output rail roda **antes** do gate RAGAS — defende contra prompt injection vindo de conteúdo malicioso já indexado no SharePoint antes mesmo de gastar a chamada de avaliação RAGAS.
- Nenhum relatório é publicado automaticamente — todo PR passa por revisão humana obrigatória (mesma garantia HITL das Fases 2-3).

---

## Observability

| Aspect | Implementation |
|--------|-------------------|
| Logging | `logging.getLogger(__name__)` estruturado, mesmo padrão de `failure_capture.py`/`generate_insights.py` |
| Métricas RAGAS | Embutidas no `detail` JSON de `self_healing_events` (evento aprovado) — já ficam disponíveis para consulta futura sem infraestrutura nova, forward-compatible com um futuro Painel Sentinela (COULD do DEFINE) |
| Rastreabilidade | `payload["target_file"]` referencia o `report_id` derivado do `insight_id` de origem; `source_path` em cada chunk rastreia o documento SharePoint original (lineage exigido pelo DEFINE) |

---

## Pipeline Architecture

### DAG Diagram

```text
[SharePoint/Graph delta] ──extract+chunk──→ [contract_validator] ──valid──→ [bronze.sharepoint_documents]
                                                      │                              │
                                                      └──invalid──→ [bronze_dlq]      Delta Sync Index
                                                            │                         │
                                            (self-healing já processa, Fase 2)   [Vector Search]
                                                                                       │
[gold.market_insights] ──┐                                                           │
                          ├──► [dag_generate_content] ──retrieval+draft──→ [RAGAS gate]
                          │                                                       │
                          │                                        ┌──────────────┴─────────────┐
                          │                                   reprovado                     aprovado
                          │                                        │                              │
                          │                          [self_healing_rejections]       [self_healing_events]
                          │                                                                        │
                          │                                                        [dag_self_healing_diagnose]
                          │                                                          (Fase 2, reaproveitado)
                          │                                                                        │
                          │                                                              [PR no GitHub]
```

### Partition Strategy

| Table | Partition Key | Granularity | Rationale |
|-------|----------------|-------------|--------------|
| `bronze.sharepoint_documents` | `ingestion_date` | daily | Mesma convenção de `bronze_writer.write_bronze` (Fase 1), reaproveitada sem mudança |

### Incremental Strategy

| Model | Strategy | Key Column | Lookback |
|-------|----------|--------------|----------|
| `bronze.sharepoint_documents` | Graph delta query (`@odata.deltaLink`) | `document_id` | N/A — cursor opaco do Graph, não baseado em janela |
| Consumo de `gold.market_insights` pelo content factory | Cursor por timestamp (`checkpoint.py`, Fase 2, reaproveitado) | `generated_at` | Desde o último ciclo hourly |

### Schema Evolution Plan

| Change Type | Handling | Rollback |
|-------------|----------|-------------|
| Novo `source_failure_type` (`content_generation`) em `self_healing_events` | Aditivo — coluna já é STRING livre (mesmo padrão da Decision 2, Fase 3) | N/A |
| Nova coluna em `bronze.sharepoint_documents` | Contrato ODCS-lite marca `evolution.compatibility: additive-only` (mesmo padrão da Fase 1) | Remover coluna, contrato reflete versão anterior |

### Data Quality Gates

| Gate | Tool | Threshold | Action on Failure |
|------|------|-----------|-----------------------|
| Contrato de `bronze.sharepoint_documents` | `contract_validator.validate_batch` (Fase 1, reaproveitado) | 0 nulos em campos obrigatórios | Registro cai na DLQ, processado pelo self-healing (Fase 2) |
| RAGAS (faithfulness + answer relevancy) | `content_factory._evaluate_ragas` | `>= 0.7` cada (configurável) | Bloqueia — nunca vira PR (AT-003) |
| Guardrail de path/conteúdo do diff | `guardrails.evaluate` (Fase 2, reaproveitado) | Allowlist + padrões perigosos | Registrado em `self_healing_rejections` |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|------------|
| 1.0 | 2026-08-10 | design-agent | Initial version |
| 1.1 | 2026-08-11 | ship-agent | Shipped and archived |

---

## Next Step

**Shipped** — see `SHIPPED_2026-08-11.md` in this archive folder.
