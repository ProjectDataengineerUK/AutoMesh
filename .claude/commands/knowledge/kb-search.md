---
description: Busca rápida nos 42+ domínios de KB do agentcode — conceitos, padrões, incidentes conhecidos
---

# /kb-search — Busca no Knowledge Base

Busca um termo ou tema em TODOS os domínios de KB do plugin e responde com as
fontes encontradas, respeitando o protocolo KB-First do DOMA.

## Usage

```
/kb-search <termo ou pergunta>
/kb-search databricks_grants
/kb-search "como fazer DLQ em stream avro"
/kb-search scd2
```

## Execution

1. **Extraia 2-4 termos de busca** do input (termo literal + sinônimos técnicos).
   Ex.: "DLQ avro" → `DLQ|dead.letter|quarantine|from_avro|malformed`.

2. **Busque no KB do plugin** (case-insensitive, com contexto):

```bash
KB="${CLAUDE_PLUGIN_ROOT:-.claude}/kb"
grep -rniE "TERMO1|TERMO2" "$KB" --include="*.md" -l | head -12
```

3. **Priorize por tipo de arquivo** (mais específico primeiro):
   `patterns/known-incidents.md` e `*lessons*.md` (experiência real) >
   `patterns/*.md` (código validado) > `concepts/*.md` (teoria) > `index.md`.

4. **Leia os 2-4 arquivos mais relevantes** e responda:
   - A resposta sintetizada, com trechos de código quando houver
   - **Fonte**: caminho do(s) arquivo(s) KB usados (protocolo de proveniência DOMA)
   - **Confiança**: alta se veio de incidente/padrão validado; média se conceitual
   - Se NADA relevante existir no KB: diga explicitamente "KB não cobre este tema"
     e sugira `/create-kb` ou responda com conhecimento geral SINALIZANDO que não
     é KB-validado.

## Domínios disponíveis

Databricks, Fabric, Snowflake, Spark, Kafka/streaming, Airflow, dbt, lakehouse,
medallion, data-modeling, data-quality, governance, migration, semantic-modeling,
AWS/GCP/cloud, Terraform, Python, testing, Pydantic, GenAI, prompt-engineering,
Supabase, guardrails (constituição + anti-alucinação), legal (14 sub-domínios),
DOMA protocol, agentcodex (controls/operations/patterns/platforms) e mais.
