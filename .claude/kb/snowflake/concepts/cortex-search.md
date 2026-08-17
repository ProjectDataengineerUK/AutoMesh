# Cortex Search — Busca Semântica sobre Dados Não Estruturados

> **Propósito:** Criar e consultar índices de busca semântica (vetorial + keyword hybrid)
> sobre tabelas Snowflake com texto não estruturado. Base para RAG nativo no Snowflake.

---

## O que é

**Cortex Search** cria um serviço de busca gerenciado sobre uma coluna TEXT em uma tabela Snowflake.
O serviço indexa os dados, gera embeddings (`AI_EMBED` internamente), e expõe uma API de busca
híbrida (semântica + BM25 keyword).

```sql
-- Criar o serviço de busca
CREATE OR REPLACE CORTEX SEARCH SERVICE kb_search_service
  ON COLUMN content                    -- coluna de texto a indexar
  ATTRIBUTES category, source, created_at  -- filtros disponíveis
  WAREHOUSE = cortex_wh
  TARGET_LAG = '1 hour'
AS
  SELECT
    content,
    category,
    source,
    created_at,
    doc_id
  FROM analytics.gold.knowledge_base_docs
  WHERE is_active = TRUE;
```

---

## Consultando via SQL

```sql
-- Busca semântica simples
SELECT *
FROM TABLE(
  CORTEX_SEARCH_RESULTS(
    'kb_search_service',
    '{"query": "Como configurar RBAC no Snowflake?", "limit": 5}'
  )
) AS results;

-- Busca com filtro por atributo
SELECT *
FROM TABLE(
  CORTEX_SEARCH_RESULTS(
    'kb_search_service',
    '{
      "query": "dynamic tables performance",
      "limit": 5,
      "filter": {"@eq": {"category": "data-engineering"}}
    }'
  )
) AS results;
```

---

## Padrão RAG com Cortex Search + Cortex AI

```python
import snowflake.connector
import json

def snowflake_rag(question: str, service: str, conn, model: str = "claude-sonnet-4-6") -> str:
    """
    RAG nativo Snowflake: busca contexto via Cortex Search + gera resposta via AI_COMPLETE.
    Todo o processamento permanece dentro do perímetro Snowflake.
    """
    # 1. Buscar contexto relevante
    search_results = conn.cursor().execute(
        """
        SELECT value:text::STRING AS chunk, value:score::FLOAT AS score
        FROM TABLE(
            CORTEX_SEARCH_RESULTS(?, ?)
        ), LATERAL FLATTEN(input => results)
        ORDER BY score DESC
        LIMIT 5
        """,
        [service, json.dumps({"query": question, "limit": 5})]
    ).fetchall()
    
    # 2. Montar contexto
    context = "\n\n".join([f"[Score: {r[1]:.2f}]\n{r[0]}" for r in search_results])
    
    # 3. Gerar resposta via AI_COMPLETE (dentro do Snowflake)
    prompt = f"""Contexto:
{context}

Pergunta: {question}

Responda com base no contexto acima. Se não houver informação suficiente, diga claramente."""
    
    response = conn.cursor().execute(
        "SELECT AI_COMPLETE(?, ?)",
        [model, prompt]
    ).fetchone()[0]
    
    return response
```

---

## Chunking Strategy

Para documentos longos, chunkar antes de ingerir:

```python
def chunk_document(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """Chunking por tokens com overlap para preservar contexto entre chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

# Inserir chunks na tabela que o Cortex Search indexa
for doc_id, doc_text in documents.items():
    for idx, chunk in enumerate(chunk_document(doc_text)):
        conn.cursor().execute(
            "INSERT INTO knowledge_base_docs VALUES (?, ?, ?, ?, ?)",
            [f"{doc_id}_{idx}", chunk, "data-engineering", "internal", "2026-05-08"]
        )
```

---

## Manutenção do Índice

```sql
-- Monitorar status do serviço
SHOW CORTEX SEARCH SERVICES;

-- Ver detalhes e quando foi atualizado pela última vez
DESCRIBE CORTEX SEARCH SERVICE kb_search_service;

-- Suspender (economiza créditos quando não em uso)
ALTER CORTEX SEARCH SERVICE kb_search_service SUSPEND;

-- Retomar
ALTER CORTEX SEARCH SERVICE kb_search_service RESUME;
```

---

## Comparação: Cortex Search vs pgvector vs Qdrant

| Dimensão | Cortex Search | pgvector (Supabase) | Qdrant |
|----------|--------------|---------------------|--------|
| Hospedagem | Snowflake managed | Self/cloud | Self/cloud |
| Governança | Unity (Snowflake RBAC) | PostgreSQL RLS | API key |
| Filtros | Atributos declarados | `WHERE` SQL | Payload filter |
| Latência | 200–500ms | 10–50ms | 5–30ms |
| Custo | Créditos Snowflake | Compute + storage | Compute + storage |
| Melhor para | Dados já no Snowflake | PostgreSQL workloads | Alta performance |
