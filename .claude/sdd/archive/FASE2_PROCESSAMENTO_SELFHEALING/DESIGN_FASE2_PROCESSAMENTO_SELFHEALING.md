# DESIGN: Fase 2 — Processamento (Bronze→Silver) e Self-Healing

> Technical design for implementing FASE2_PROCESSAMENTO_SELFHEALING

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | FASE2_PROCESSAMENTO_SELFHEALING |
| **Date** | 2026-08-03 |
| **Author** | design-agent |
| **DEFINE** | [DEFINE_FASE2_PROCESSAMENTO_SELFHEALING.md](./DEFINE_FASE2_PROCESSAMENTO_SELFHEALING.md) |
| **Status** | ✅ Shipped |

---

## Pre-Design Research

Antes de desenhar, validei a Assumption A-001 do DEFINE (acesso via API externa ao Databricks Free Edition) com pesquisa web nas páginas oficiais de limitações:

> "No access to the account console or account-level APIs" — restrição é a **nível de conta**, não de workspace. A documentação de PAT/Jobs API (`/api/2.0/token/create`, `databricks.sdk.WorkspaceClient().jobs.run_now()`) não é mencionada como bloqueada.
>
> "Outbound internet access is restricted to a limited set of trusted domains" (a menos que o usuário complete verificação de identidade via LinkedIn) — **esta é a restrição que mais importa para este design**: código rodando *dentro* de um notebook/job do Databricks pode não conseguir chamar a API da Anthropic/OpenAI nem a API do GitHub livremente.

Fontes: [Databricks Free Edition limitations (AWS docs)](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations), [Databricks Free Edition limitations (Azure docs)](https://learn.microsoft.com/en-us/azure/databricks/getting-started/free-edition-limitations)

**Conclusão de design:** o job Databricks (Bronze→Silver) só lê/escreve Delta — não precisa de internet externa, então não é afetado. O self-healing (LLM + GitHub) **não deve rodar dentro do Databricks** — fica inteiramente em tasks do Airflow, que não tem essa restrição. Isso reforça o Approach A escolhido no brainstorm. O acionamento do Job via `jobs.run_now()` a partir do Airflow segue como assunção plausível, mas ainda não validada com o workspace real provisionado (mesma postura da Fase 1 com a conta cloud trial) — ficará marcado como risco a confirmar no Build.

---

## Architecture Overview

```text
┌────────────────────────────────────────────────────────────────────────────────────┐
│                    FASE 2 — PROCESSAMENTO + SELF-HEALING                            │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│ [Bronze (Fase 1)] ──► [dag_process_bronze_to_silver] ──► [Databricks Job: PySpark]  │
│                              │ (databricks-sdk / DatabricksRunNowOperator)           │
│                              ▼                                                       │
│                     [Silver: MERGE (b3_quotes, crm) | append (telemetry, logs)]     │
│                                                                                       │
│ [bronze_dlq (Fase 1, + detected_at)]───┐                                            │
│                                          ├──► [dag_self_healing_diagnose]            │
│ [on_failure_callback (DAGs Fase 2)] ───►│         │                                  │
│   escreve em [self_healing_events]      │    [checkpoint: self_healing_checkpoint]  │
│                                          │         │                                  │
│                                          ▼         ▼                                  │
│                                  [llm_diagnostician: Claude API]                     │
│                                          │                                            │
│                                  diagnóstico estruturado                             │
│                                  (causa raiz, tipo, diff)                            │
│                                          │                                            │
│                              ┌───────────┴───────────┐                               │
│                       [Guardrail 1: allowlist]  (falha)──► [self_healing_rejections] │
│                              │ (passou)                            (Delta)           │
│                       [Guardrail 2: conteúdo]   (falha)──────────────┘               │
│                              │ (passou)                                              │
│                              ▼                                                        │
│                     [github_pr: branch + commit + PR]                                │
│                              │                                                        │
│                     (revisão humana — merge nunca automático)                        │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| Bronze→Silver Job | Cleanse, dedup (MERGE) ou append, type-cast conforme contrato | PySpark, Delta Lake (`DeltaTable.merge`), rodando num Databricks Job (Free Edition, serverless) |
| DAG de Processamento | Aciona o Job Databricks e aguarda conclusão | Airflow, `apache-airflow-providers-databricks` (`DatabricksRunNowOperator`, deferrable) |
| Failure Capture | Escreve falhas de execução do Airflow numa tabela compartilhada | Python, `on_failure_callback` (KB `airflow/patterns/error-handling.md`) |
| Checkpoint | Rastreia até onde a `bronze_dlq`/`self_healing_events` já foi processada | Python, tabela Delta de 1 linha |
| LLM Diagnostician | Recebe o contexto da falha, retorna diagnóstico estruturado (causa, tipo, diff) | Python, Anthropic API (Claude), saída estruturada via tool use |
| Guardrails | Allowlist de caminhos + checagem de padrões perigosos no diff | Python puro, determinístico (sem framework externo, sem segunda chamada de LLM) |
| GitHub PR Writer | Cria branch, commita o diff, abre PR com o diagnóstico no corpo | Python, GitHub REST API (token com escopo restrito) |
| DAG de Self-Healing | Orquestra a leitura das duas fontes de falha até a decisão final (PR ou rejeição) | Airflow |

---

## Key Decisions

### Decision 1: Self-healing roda inteiramente no Airflow, nunca dentro do Databricks

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-03 |

**Context:** O Databricks Free Edition restringe acesso de internet de saída a um conjunto limitado de domínios confiáveis (ver Pre-Design Research). O self-healing precisa chamar a API da Anthropic e a API do GitHub livremente.

**Choice:** Todo o código de diagnóstico (LLM), guardrails e abertura de PR roda como tasks Python do Airflow — nunca dentro de um notebook/job Databricks.

**Rationale:** Airflow não tem a restrição de domínios confiáveis do Free Edition; e como o self-healing precisa chamar dois serviços externos arbitrários (Anthropic, GitHub), rodá-lo fora do Databricks elimina esse risco por completo, sem precisar depender de verificação de identidade (LinkedIn) nem de uma allowlist de domínio administrada pela Databricks.

**Alternatives Rejected:**
1. Rodar o self-healing como um Job Databricks separado — rejeitado: sujeito à restrição de outbound internet do Free Edition, que bloquearia justamente as chamadas que o self-healing mais precisa fazer.

**Consequences:**
- O Databricks só precisa de acesso de rede para ler/escrever Delta — nenhuma dependência de domínio externo lá.
- Airflow permanece o único orquestrador com acesso a segredos externos (Anthropic, GitHub), simplificando a superfície de gestão de credenciais.

---

### Decision 2: Job Databricks acionado via `apache-airflow-providers-databricks` (não via SDK cru)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-03 |

**Context:** É preciso decidir como o Airflow aciona e aguarda o Job Databricks — via chamada direta ao `databricks-sdk` dentro de uma task Python, ou via o provider oficial do Airflow.

**Choice:** Usar `DatabricksRunNowOperator` (deferrable) do `apache-airflow-providers-databricks`.

**Rationale:** Consistente com a decisão da Fase 1 de usar providers oficiais do Airflow (Kafka) em vez de reimplementar polling manual — ganha retry, logging e modo deferrable de graça. **Nota para o Build:** a Fase 1 revelou que a API exata de operadores/sensors de provider pode divergir do que a KB resume (ex: `AwaitMessageTriggerFunctionSensor` exigia um argumento não documentado no pattern) — o Build deve confirmar os parâmetros exatos do `DatabricksRunNowOperator` via `inspect.signature()` contra a versão instalada, exatamente como foi feito na validação real da Fase 1, antes de assumir que o pattern abaixo está 100% correto.

**Alternatives Rejected:**
1. `databricks-sdk` cru numa task Python com polling manual — rejeitado: reinventa retry/deferred polling que o provider já oferece pronto.

**Consequences:**
- Mais uma dependência (`apache-airflow-providers-databricks`) no `requirements.txt`.
- Ganha suporte a execução assíncrona (libera o worker slot enquanto o Job roda), como o padrão de sensors deferrable já usado na Fase 1.

---

### Decision 3: Unificação das duas fontes de falha via checkpoint + tabela nova, sem reabrir os DAGs da Fase 1

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-03 |

**Context:** O self-healing precisa consumir falhas de contrato (`bronze_dlq`, Fase 1) e falhas de execução (Airflow, novas nesta fase) de forma unificada, sem reprocessar o que já foi diagnosticado.

**Choice:** (a) Adicionar uma coluna aditiva `detected_at` (timestamp) em `bronze_writer.write_dlq()` — mudança pequena, retrocompatível, seguindo a própria política de evolução de schema definida no DESIGN da Fase 1 ("New column: adicionar como opcional"). (b) Criar uma tabela nova `self_healing_events` para falhas de execução, escrita por um `on_failure_callback` compartilhado. (c) Uma tabela `self_healing_checkpoint` (1 linha) guarda o timestamp do último evento processado de cada fonte. (d) O `on_failure_callback` é conectado **só nos DAGs novos desta fase** (`dag_process_bronze_to_silver`, `dag_self_healing_diagnose`) — retrofitá-lo nos DAGs já shipped da Fase 1 é uma mudança de uma linha por DAG (`default_args`), deixada como fast-follow em vez de reabrir código já testado e arquivado sem necessidade imediata.

**Rationale:** Minimiza o retrabalho em cima do que já foi shipped, mantendo a Fase 1 estável, e usa exatamente o mecanismo de evolução de contrato que a própria Fase 1 já previu.

**Alternatives Rejected:**
1. Reescrever `bronze_dlq` com um novo formato — rejeitado: quebraria compatibilidade sem necessidade.
2. Aplicar o `on_failure_callback` retroativamente em todos os DAGs da Fase 1 agora — rejeitado nesta rodada: escopo do DEFINE não exige cobertura retroativa imediata, e mexer em DAGs shipped merece uma decisão explícita do usuário, não uma mudança silenciosa.

**Consequences:**
- Falhas de execução dos DAGs da Fase 1 (ingestão) não acionam o self-healing ainda — só falhas de contrato (via DLQ) e falhas de execução dos DAGs novos da Fase 2.
- Fica documentado como lacuna conhecida para uma iteração futura (`/iterate` ou novo brainstorm).

---

### Decision 4: LLM Diagnostician usa Claude (Anthropic API) com saída estruturada via tool use

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-03 |

**Context:** O DEFINE deixou o provedor de LLM em aberto.

**Choice:** Usar a API da Anthropic (Claude), com a resposta forçada a um schema estruturado (`root_cause`, `fix_type: contract|code`, `target_file`, `diff`, `explanation`) via tool use / structured output.

**Rationale:** Evita parsear texto livre em busca do diff (frágil); tool use garante que a resposta já vem no formato que os guardrails esperam. Reduz a superfície de erro de parsing que poderia, ela mesma, criar uma falha silenciosa.

**Alternatives Rejected:**
1. Prompt de texto livre + regex para extrair o diff — rejeitado: frágil, sujeito a variações de formatação do modelo.

**Consequences:**
- Uma dependência nova (`anthropic` SDK).
- Custo por chamada de diagnóstico — sem roteamento multi-modelo neste MVP (YAGNI já registrado no DEFINE).
- **Achado na validação real (Build):** importar `anthropic` no topo do módulo é pesado o bastante (árvore de tipos Pydantic aninhados) para estourar o `DagBag import timeout` padrão do Airflow (30s) quando o módulo é importado transitivamente no parse do DAG. Corrigido tornando o `import anthropic` preguiçoso, só dentro de `diagnose()` — ver Pattern 2 atualizado.

---

### Decision 5: Guardrail de conteúdo é determinístico (regras), não uma segunda chamada de LLM

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-03 |

**Context:** O brainstorm deixou em aberto se o guardrail de conteúdo seria um checker de regras ou um segundo LLM revisando o diff.

**Choice:** Lista de padrões perigosos (regex) verificada em Python puro — sem chamar um LLM para validar a saída de outro LLM.

**Rationale:** Usar um LLM para checar outro LLM é um padrão fraco de guardrail (o segundo modelo pode ser enganado do mesmo jeito que o primeiro); uma checagem determinística é mais rápida, mais barata, 100% testável com casos fixos, e mais fácil de auditar ("por que isso foi bloqueado?" tem sempre uma resposta exata).

**Alternatives Rejected:**
1. Segunda chamada de LLM como guardrail de conteúdo — rejeitado pelas razões acima.

**Consequences:**
- A lista de padrões perigosos precisa ser mantida manualmente (`os.system`, `eval(`, `subprocess`, credenciais hardcoded via regex, `DROP TABLE`, `DELETE FROM` sem `WHERE`, etc.) — fica documentada e testável, mas não é exaustiva por natureza.

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `pipelines/ingestion/common/bronze_writer.py` | Modify | Adicionar coluna aditiva `detected_at` em `write_dlq()` (Decision 3) | @lakehouse-architect | None |
| 2 | `pipelines/processing/jobs/bronze_to_silver.py` | Create | Script PySpark: cleanse, MERGE/append, type-cast por fonte | @spark-engineer | None |
| 3 | `pipelines/processing/dags/dag_process_bronze_to_silver.py` | Create | DAG: aciona o Job Databricks via `DatabricksRunNowOperator` | @airflow-specialist | 2 |
| 4 | `pipelines/self_healing/common/checkpoint.py` | Create | Lê/escreve `self_healing_checkpoint` (Delta, 1 linha) | @lakehouse-architect | None |
| 5 | `pipelines/self_healing/common/failure_capture.py` | Create | `on_failure_callback` compartilhado — escreve em `self_healing_events` | @airflow-specialist | 4 |
| 6 | `pipelines/self_healing/common/llm_diagnostician.py` | Create | Chama a API da Anthropic, retorna diagnóstico estruturado | @genai-architect | None |
| 7 | `pipelines/self_healing/common/guardrails.py` | Create | Allowlist de caminhos + checagem de padrões perigosos | @security-reviewer | None |
| 8 | `pipelines/self_healing/common/github_pr.py` | Create | Cria branch, commita diff, abre PR no GitHub | @ci-cd-specialist | None |
| 9 | `pipelines/self_healing/common/rejection_writer.py` | Create | Escreve `self_healing_rejections` (Delta) | @lakehouse-architect | None |
| 10 | `pipelines/self_healing/dags/dag_self_healing_diagnose.py` | Create | DAG: lê as 2 fontes de falha, orquestra diagnóstico → guardrails → PR/rejeição | @airflow-specialist | 1, 4, 5, 6, 7, 8, 9 |
| 11 | `pipelines/processing/requirements.txt` | Create | Dependências do pacote de processamento | (general) | None |
| 12 | `pipelines/self_healing/requirements.txt` | Create | Dependências do pacote de self-healing | (general) | None |
| 13 | `pipelines/self_healing/tests/test_guardrails.py` | Create | Testes do allowlist + padrões perigosos (cobre AT-003, AT-004) | @test-generator | 7 |
| 14 | `pipelines/self_healing/tests/test_llm_diagnostician.py` | Create | Testes do diagnóstico (LLM mockado) | @test-generator | 6 |
| 15 | `pipelines/self_healing/tests/test_github_pr.py` | Create | Testes da abertura de PR (GitHub API mockada) | @test-generator | 8 |
| 16 | `pipelines/self_healing/tests/test_checkpoint.py` | Create | Testes do checkpoint incremental | @test-generator | 4 |
| 17 | `pipelines/self_healing/tests/test_dags_integrity.py` | Create | Integridade dos 2 novos DAGs (`pytest.importorskip("airflow")`) | @test-generator | 3, 10 |

**Total Files:** 17 (16 novos + 1 modificado)

---

## Agent Assignment Rationale

| Agent | Files Assigned | Why This Agent |
|-------|----------------|------------------|
| @lakehouse-architect | 1, 4, 9 | Formato de tabela Delta e evolução de schema — mesma especialização usada na Fase 1 para `bronze_writer.py` |
| @spark-engineer | 2 | PySpark/DataFrame transformations — cleanse, MERGE, type-cast |
| @airflow-specialist | 3, 5, 10 | DAGs, `on_failure_callback`, operators de provider — SME de Airflow 3.0 |
| @genai-architect | 6 | Desenho de agente com saída estruturada de LLM — especialização em sistemas GenAI de produção |
| @security-reviewer | 7 | Guardrails são, por definição, controle de segurança — revisão de padrões perigosos e allowlist |
| @ci-cd-specialist | 8 | Automação de GitHub (branch, commit, PR) — self-healing abrindo PR é exatamente o caso de uso descrito no CLAUDE.md do projeto |
| @test-generator | 13-17 | Testes pytest — mocks de LLM e GitHub, fixtures |
| (general) | 11, 12 | `requirements.txt` não exige especialista |

**Agent Discovery:**
- Scanned: `.claude/agents/**/*.md`
- Matched por: KB domains do DEFINE (`databricks`, `spark`, `lakeflow`, `medallion`, `data-quality`, `airflow`), mais palavras-chave de propósito (guardrails→security, PR→ci-cd, LLM→genai)

---

## Code Patterns

### Pattern 1: MERGE condicional por fonte (Bronze→Silver)

```python
# pipelines/processing/jobs/bronze_to_silver.py
# Adapted from KB: spark/patterns/delta-integration.md
from __future__ import annotations

from delta.tables import DeltaTable
from pyspark.sql import SparkSession

MERGE_SOURCES = {
    "b3_quotes": "t.ticker = s.ticker AND t.quote_timestamp = s.quote_timestamp",
    "crm_lost_sales": "t.opportunity_id = s.opportunity_id",
}
APPEND_ONLY_SOURCES = ["infra_telemetry", "usage_logs"]


def promote_to_silver(spark: SparkSession, source: str, bronze_path: str, silver_path: str) -> int:
    bronze_df = spark.read.format("delta").load(bronze_path)

    if source in MERGE_SOURCES:
        if not DeltaTable.isDeltaTable(spark, silver_path):
            bronze_df.write.format("delta").save(silver_path)
            return bronze_df.count()

        target = DeltaTable.forPath(spark, silver_path)
        (target.alias("t")
            .merge(bronze_df.alias("s"), MERGE_SOURCES[source])
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute())
        return bronze_df.count()

    if source in APPEND_ONLY_SOURCES:
        bronze_df.write.format("delta").mode("append").save(silver_path)
        return bronze_df.count()

    raise ValueError(f"Unknown source for Silver promotion: {source}")
```

### Pattern 2: Diagnóstico estruturado via Claude (tool use)

> Verificado contra Airflow 3.0.0 real: `import anthropic` no topo do arquivo estourava o `DagBag import timeout` (30s) — corrigido com import preguiçoso dentro de `diagnose()`.

```python
# pipelines/self_healing/common/llm_diagnostician.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import anthropic

DIAGNOSIS_TOOL = {
    "name": "propose_fix",
    "description": "Propõe uma correção estruturada para a falha do pipeline",
    "input_schema": {
        "type": "object",
        "properties": {
            "root_cause": {"type": "string"},
            "fix_type": {"type": "string", "enum": ["contract", "code"]},
            "target_file": {"type": "string"},
            "diff": {"type": "string"},
            "explanation": {"type": "string"},
        },
        "required": ["root_cause", "fix_type", "target_file", "diff", "explanation"],
    },
}


@dataclass
class Diagnosis:
    root_cause: str
    fix_type: str
    target_file: str
    diff: str
    explanation: str


def diagnose(failure_context: dict) -> Diagnosis:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        tools=[DIAGNOSIS_TOOL],
        tool_choice={"type": "tool", "name": "propose_fix"},
        messages=[{
            "role": "user",
            "content": (
                "Diagnostique a falha do pipeline abaixo e proponha uma correção.\n\n"
                f"Tipo de falha: {failure_context['source_failure_type']}\n"
                f"Fonte: {failure_context['source']}\n"
                f"Detalhes: {failure_context['detail']}\n"
                f"Contexto de código/contrato relevante:\n{failure_context['code_context']}"
            ),
        }],
    )

    tool_use = next(block for block in response.content if block.type == "tool_use")
    return Diagnosis(**tool_use.input)
```

### Pattern 3: Guardrails determinísticos (allowlist + conteúdo)

```python
# pipelines/self_healing/common/guardrails.py
from __future__ import annotations

import re

ALLOWED_PATH_PREFIXES = (
    "pipelines/ingestion/contracts/",
    "pipelines/ingestion/producers/",
    "pipelines/ingestion/dags/",
    "pipelines/ingestion/common/",
    "pipelines/processing/",
)

DANGEROUS_PATTERNS = [
    re.compile(r"os\.system\("),
    re.compile(r"subprocess\."),
    re.compile(r"\beval\("),
    re.compile(r"\bexec\("),
    re.compile(r"DROP\s+TABLE", re.IGNORECASE),
    re.compile(r"DELETE\s+FROM\s+\w+\s*;", re.IGNORECASE),
    re.compile(r"(?i)(api[_-]?key|secret|password)\s*=\s*['\"][^'\"]+['\"]"),
]


def check_allowlist(target_file: str) -> str | None:
    if not any(target_file.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES):
        return f"out_of_scope_path:{target_file}"
    return None


def check_content(diff: str) -> str | None:
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(diff):
            return f"dangerous_pattern:{pattern.pattern}"
    return None


def evaluate(target_file: str, diff: str) -> str | None:
    return check_allowlist(target_file) or check_content(diff)
```

### Pattern 4: Configuração — `self_healing_events` (schema)

```yaml
# Estrutura da tabela self_healing_events (Delta), não um contrato de fonte externa
schema:
  columns:
    - name: event_id
      type: string
    - name: source_failure_type
      type: string   # "contract" | "execution"
    - name: source
      type: string    # ex: "dag_process_bronze_to_silver"
    - name: detail
      type: string     # traceback ou _failure_reason
    - name: detected_at
      type: timestamp
```

---

## Data Flow

```text
1. Bronze (Fase 1) tem novos dados validados
   │
   ▼
2. dag_process_bronze_to_silver aciona o Job Databricks (DatabricksRunNowOperator)
   │
   ▼
3. bronze_to_silver.py faz cleanse + MERGE/append + type-cast, grava na Silver
   │
   ▼ (em paralelo, orientado a evento de falha)
4. Falha de contrato → bronze_dlq (com detected_at) | Falha de execução → on_failure_callback → self_healing_events
   │
   ▼
5. dag_self_healing_diagnose lê ambas as fontes desde o último checkpoint
   │
   ▼
6. Para cada evento: llm_diagnostician.diagnose() retorna causa + tipo + diff
   │
   ▼
7. guardrails.evaluate() — se falhar, grava em self_healing_rejections e para
   │
   ▼ (se passou)
8. github_pr cria branch, commita, abre PR com diagnóstico + link do log
   │
   ▼
9. Checkpoint avança; PR aguarda revisão humana (merge nunca automático)
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|-------------------|------------------|
| Databricks Jobs API | `apache-airflow-providers-databricks` (REST) | PAT via Airflow Connection `databricks_default` |
| Anthropic API | SDK (`anthropic`) | API key via Airflow Connection/Variable, nunca hardcoded |
| GitHub REST API | SDK (`PyGithub`) ou `requests` | Token com escopo restrito (`contents:write`, `pull_requests:write` — **sem** permissão de merge/admin) |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|-----------------|
| Unit | `guardrails.evaluate` — allowlist e padrões perigosos | `tests/test_guardrails.py` | pytest — cobre AT-003, AT-004 | 80% |
| Unit | `llm_diagnostician.diagnose` — parsing da resposta estruturada | `tests/test_llm_diagnostician.py` | pytest + mock do client Anthropic | 80% |
| Unit | `github_pr` — criação de branch/commit/PR | `tests/test_github_pr.py` | pytest + mock da API do GitHub | 80% |
| Unit | `checkpoint` — leitura/escrita incremental | `tests/test_checkpoint.py` | pytest + `deltalake` local (tmp dir) | 80% |
| Integration | DAGs importam sem erro | `tests/test_dags_integrity.py` | pytest + `pytest.importorskip("airflow")`, validar via Docker real (mesmo padrão da Fase 1) | 2 DAGs |
| E2E | Fluxo completo AT-001/AT-002 (happy path + falha de execução) | Manual, contra o workspace Databricks Free Edition real quando provisionado | — | Happy path |

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|----------------------|--------|
| Job Databricks falha | `DatabricksRunNowOperator` propaga a falha; Airflow retenta com backoff exponencial (mesmo padrão da Fase 1) | Yes |
| API da Anthropic indisponível/timeout | Retry com backoff (reaproveita o padrão de `b3_quotes_producer.fetch_quotes`); se esgotar, evento fica sem diagnóstico e é reprocessado no próximo scan (checkpoint não avança para esse evento) | Yes |
| Diagnóstico com `fix_type` desconhecido ou diff vazio | Tratado como rejeição de guardrail (`invalid_diagnosis`), registrado em `self_healing_rejections` | No |
| Falha ao abrir PR (rate limit do GitHub, conflito de branch) | Retry com backoff; se esgotar, evento fica pendente (checkpoint não avança) | Yes |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|----------------|
| `DATABRICKS_JOB_ID` | int | (Variable, definido no Build) | ID do Job Databricks de Bronze→Silver |
| `ANTHROPIC_MODEL` | string | `claude-sonnet-4-5` | Modelo usado pelo diagnóstico |
| `GITHUB_REPO` | string | (Variable) | Repositório alvo dos PRs de self-healing |
| `GITHUB_PR_BASE_BRANCH` | string | `main` | Branch base dos PRs |
| `SELF_HEALING_ALLOWED_PATHS` | list[string] | ver `guardrails.py` | Allowlist de prefixos de caminho |

---

## Security Considerations

- Token do GitHub escopado só para `contents:write` + `pull_requests:write` — sem permissão de merge/admin, preservando o HITL (Decision já registrada no DEFINE)
- Guardrails em duas camadas, determinísticas, antes de qualquer PR existir (Decisions 5)
- Nenhum diff proposto pelo LLM é executado (`eval`/`exec`) — só inspecionado por padrão e, se aprovado, commitado como texto
- Credenciais (Anthropic, GitHub, Databricks) sempre via Airflow Connections/Variables, nunca hardcoded
- `self_healing_rejections` preserva todo diff rejeitado para auditoria — nada é descartado silenciosamente

---

## Observability

| Aspect | Implementation |
|--------|------------------|
| Logging | Logging estruturado nas tasks; cada decisão (PR aberto / rejeitado) loga o motivo |
| Metrics | Contagem de eventos diagnosticados vs. PRs abertos vs. rejeições por execução do DAG (base para o Painel Sentinela da Fase 3, conforme o COULD do DEFINE) |
| Tracing | Fora de escopo — mesma decisão da Fase 1 |

---

## Pipeline Architecture

### DAG Diagram

```text
[Bronze (Fase 1)] ──run_now──► [Databricks Job: bronze_to_silver] ──► [Silver]
[bronze_dlq]──┐
[self_healing_events]──┤──► [dag_self_healing_diagnose] ──► [LLM] ──► [Guardrails] ──┬──► [PR no GitHub]
                                                                                        └──► [self_healing_rejections]
```

### Partition Strategy

| Table | Partition Key | Granularity | Rationale |
|-------|-------------------|-------------|--------------|
| `silver.b3_quotes`, `silver.crm_lost_sales` | Nenhuma (tabela pequena, MERGE por chave) | N/A | Volume baixo não justifica particionamento na Silver |
| `silver.infra_telemetry`, `silver.usage_logs` | `ingestion_date` (herdado do Bronze) | Diária | Mantém o padrão já usado no Bronze |
| `self_healing_events`, `self_healing_rejections` | `detected_at` (data) | Diária | Consistente com o padrão de particionamento por data já usado em `bronze_dlq` |

### Incremental Strategy

| Model | Strategy | Key Column | Lookback |
|-------|----------|--------------|-----------|
| `silver.b3_quotes` | `unique_key` (MERGE) | `ticker` + `quote_timestamp` | N/A |
| `silver.crm_lost_sales` | `unique_key` (MERGE) | `opportunity_id` | N/A |
| `silver.infra_telemetry`, `silver.usage_logs` | `incremental_by_time` (append) | `ingestion_date` | 1 dia |
| Leitura de `bronze_dlq`/`self_healing_events` pelo self-healing | `incremental_by_time` via checkpoint | `detected_at` | Desde o último checkpoint |

### Schema Evolution Plan

| Change Type | Handling | Rollback |
|-------------|----------|--------------|
| Nova coluna em `bronze_dlq` (`detected_at`) | Aditiva, `nullable`, retrocompatível (Decision 3) | Remover a coluna (não quebra leitores antigos) |
| Novo `_failure_reason` não previsto | O diagnóstico via LLM generaliza (escopo ampliado no brainstorm) — não exige mudança de schema | N/A |
| Mudança de tipo numa fonte Silver | Dual-write não se aplica ainda (volume baixo); nova versão do contrato documentada manualmente | Reverter para a versão anterior do contrato |

### Data Quality Gates

| Gate | Tool | Threshold | Action on Failure |
|------|------|-----------|----------------------|
| Guardrail de allowlist | `guardrails.check_allowlist` | 0 diffs fora do escopo permitido chegam a PR | Registra em `self_healing_rejections` (AT-003) |
| Guardrail de conteúdo | `guardrails.check_content` | 0 diffs com padrão perigoso chegam a PR | Registra em `self_healing_rejections` (AT-004) |
| Completude do diagnóstico | `llm_diagnostician.diagnose` | 100% dos eventos recebem diagnóstico ou ficam pendentes (nunca descartados) | Reprocessado no próximo scan |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|------------|
| 1.0 | 2026-08-03 | design-agent | Initial version — a partir de DEFINE_FASE2_PROCESSAMENTO_SELFHEALING.md, com pesquisa web validando Assumption A-001 |
| 1.1 | 2026-08-04 | ship-agent | Shipped and archived |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_FASE2_PROCESSAMENTO_SELFHEALING.md`
