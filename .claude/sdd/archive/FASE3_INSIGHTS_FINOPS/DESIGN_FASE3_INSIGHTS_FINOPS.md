# DESIGN: Fase 3 — Motor de Insights (B3+Lost Sales) e Agente FinOps

> Technical design for implementing FASE3_INSIGHTS_FINOPS

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | FASE3_INSIGHTS_FINOPS |
| **Date** | 2026-08-05 |
| **Author** | design-agent |
| **DEFINE** | [DEFINE_FASE3_INSIGHTS_FINOPS.md](./DEFINE_FASE3_INSIGHTS_FINOPS.md) |
| **Status** | ✅ Shipped |

---

## Pre-Design Research

Validei as duas Assumptions de risco do DEFINE (A-001 MLflow, A-002 `system.billing.usage`) com pesquisa web:

> "System tables are only available in environments where Unity Catalog (UC) is enabled" — e o Free Edition provisiona "one workspace and one metastore per account" (achado já registrado no DESIGN da Fase 2), ou seja, **tem um metastore Unity Catalog por padrão**. Isso é sinal forte de que `system.billing.usage` (que vive dentro do catálogo `system`, presente em todo metastore UC) está acessível — mas a permissão exata (`SELECT` no catálogo `system`) só se confirma com o workspace real provisionado.
>
> "MLflow Model Registry, integrated with Unity Catalog, centralizes AI models and artifacts" — e a documentação confirma que dá para "try MLflow on Databricks Free Edition". Como o registry é integrado ao Unity Catalog, e o Free Edition tem UC habilitado, o registry deve funcionar com nomenclatura de 3 níveis (`catalog.schema.model_name`) — **mas usando aliases (`@champion`/`@challenger`), não os stages legados (`Staging`/`Production`)**, que a Databricks está descontinuando para modelos registrados via Unity Catalog.

Fontes: [System tables reference](https://docs.azure.cn/en-us/databricks/admin/system-tables/), [MLflow on Databricks](https://docs.databricks.com/aws/en/mlflow/)

**Conclusão de design:** ambas as assunções têm sinal favorável, mas nenhuma foi confirmada contra um workspace real — mesma postura da Fase 2 com o Databricks Jobs API (correto na maioria das vezes, mas 1 bug real só apareceu rodando de verdade). O Build deve verificar as duas ao provisionar o workspace. O design abaixo já assume **aliases do MLflow** (`champion`/`challenger`), não stages, por ser a API atual e recomendada para registries integrados a Unity Catalog.

---

## Architecture Overview

```text
┌──────────────────────────────────────────────────────────────────────────────────────┐
│              FASE 3 — INSIGHTS (ML) + FINOPS (reaproveitando o self-healing)          │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│ [silver.b3_quotes + silver.crm_lost_sales] (Fase 2)                                    │
│         │                                                                               │
│         ▼                                                                               │
│ [dag_train_outlier_model] ──► features + Isolation Forest ──► [MLflow: registra versão,│
│         ▲                                                       alias @challenger]      │
│         │ (trigger se drift)                                          │                 │
│         │                                                             ▼                 │
│ [dag_generate_insights] (hourly) ──► modelo @champion ──► [gold.market_insights]        │
│         │                                                                               │
│         ├─► drift check (KS-test vs. baseline) ──drift──► trigger dag_train_outlier_model│
│         │                                                                               │
│         └─► se existe @challenger: shadow stats ──► [write_event: "model_promotion"]    │
│                                                              │                           │
│ [system.billing.usage ou dag_run.duration] (hourly)                                    │
│         │                                                                               │
│ [dag_finops_monitor] ──anomalia──► [write_event: "cost_anomaly"] ──────────────────────┤│
│                                                              │                           │
│                                                              ▼                           │
│                              [self_healing_events] (Fase 2, tabela já existente)        │
│                                                              │                           │
│                              [dag_self_healing_diagnose] (Fase 2, ZERO mudança de lógica)│
│                                        │ LLM diagnostica → guardrails (allowlist         │
│                                        │ estendida) → PR no GitHub                       │
│                                        ▼                                                 │
│                        PR: promove modelo (edita model_registry_state.yaml) OU           │
│                        PR: muda schedule/OPTIMIZE (edita arquivo do DAG)                 │
│                                        │                                                 │
│                              (revisão humana — merge nunca automático)                   │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| Train Outlier Model | Feature engineering + treino do Isolation Forest, registra no MLflow com alias `@challenger` | Python, `scikit-learn`, `mlflow`, rodando num Databricks Job |
| Generate Insights | Inferência hourly com o modelo `@champion`, grava outliers na Gold | Python, `mlflow` (load model), `deltalake` |
| Drift Check | Compara distribuição da janela atual vs. baseline de treino (KS-test) | Python, `scipy.stats` |
| Shadow Stats | Compara `@challenger` vs. `@champion` na mesma janela, gera evento de promoção | Python |
| Cost Monitor | Lê `system.billing.usage` (ou `dag_run.duration` como fallback) e detecta anomalia por job | Python, `databricks-sdk` ou Spark SQL |
| `self_healing_events` (Fase 2, reaproveitada) | Recebe eventos de `model_promotion` e `cost_anomaly`, além dos já existentes | Delta, sem mudança de schema |
| `dag_self_healing_diagnose` (Fase 2, reaproveitado) | Diagnostica, aplica guardrails, abre PR — zero mudança de lógica | Airflow (já existente) |

---

## Key Decisions

### Decision 1: MLflow com aliases (`@champion`/`@challenger`), não stages legados

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-05 |

**Context:** O DEFINE (herdado do brainstorm) usa a terminologia `Staging`/`Production` do MLflow clássico. A pesquisa do Pre-Design Research indica que o Free Edition integra o registry ao Unity Catalog, onde a Databricks recomenda aliases em vez de stages.

**Choice:** Usar `champion` (equivalente a `Production`) e `challenger` (equivalente a `Staging`) como aliases do MLflow Model Registry.

**Rationale:** Aliases são a API atual e recomendada para registries integrados a Unity Catalog; usar stages legados arriscaria escrever código que já nasce descontinuado.

**Alternatives Rejected:**
1. Manter a terminologia `Staging`/`Production` do DEFINE literalmente — rejeitado: é a API legada, meramente terminológica no DEFINE, não uma decisão técnica vinculante.

**Consequences:**
- Terminologia no código (`@champion`/`@challenger`) diverge levemente da terminologia do DEFINE/BRAINSTORM (`Staging`/`Production`) — mapeamento documentado aqui para rastreabilidade.
- Se o Build confirmar que o workspace real não tem Unity Catalog habilitado (contrariando a pesquisa), o fallback é o registry legado com stages — mudança pequena e isolada em `train_outlier_model.py`/`generate_insights.py`.

---

### Decision 2: Extensão do self-healing da Fase 2 sem alterar sua lógica — só a allowlist e um parâmetro opcional

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-05 |

**Context:** Promoção de modelo e correção de custo precisam do mesmo tratamento de guardrails+PR que a Fase 2 já construiu para falhas de contrato/execução.

**Choice:** (a) `failure_capture.write_event()` ganha um parâmetro opcional `source_failure_type: str = "execution"` (hoje hardcoded) — chamada existente em `on_task_failure()` continua funcionando sem mudança. (b) `pipelines/insights/` e `pipelines/finops/` chamam `write_event(source=..., detail=..., source_failure_type="model_promotion" | "cost_anomaly")` diretamente. (c) `dag_self_healing_diagnose.py` **não muda nada** — já lê `source_failure_type` genericamente da tabela e passa adiante para o LLM. (d) `guardrails.ALLOWED_PATH_PREFIXES` ganha 3 entradas novas: `pipelines/insights/`, `pipelines/finops/`, `pipelines/self_healing/`.

**Rationale:** O design da Fase 2 já era genérico o suficiente (o `source_failure_type` sempre foi passado como string livre, nunca validado contra um enum fechado) — a extensão é literalmente 2 diffs pequenos em vez de duplicar toda a lógica de diagnóstico/guardrail/PR numa nova tabela ou pipeline paralelo.

**Alternatives Rejected:**
1. Criar uma tabela `insights_events` e `finops_events` separadas, com um DAG de diagnóstico próprio para cada — rejeitado: duplicaria ~100 linhas de lógica já testada na Fase 2 sem ganho real.

**Consequences:**
- `self_healing_events` passa a ter 4 valores possíveis de `source_failure_type` (`contract`, `execution`, `model_promotion`, `cost_anomaly`) em vez de 2 — sem mudança de schema, só de dado.
- Um bug em `dag_self_healing_diagnose` agora afeta 4 fluxos em vez de 2 — risco aceitável dado que já está testado e validado contra Airflow real (Fase 2).

---

### Decision 3: Promoção de modelo vira PR num arquivo de estado (`model_registry_state.yaml`), não uma chamada direta à API do MLflow

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-05 |

**Context:** O mecanismo de self-healing da Fase 2 sempre produz um diff de arquivo + PR. Promoção de modelo (mudar um alias no MLflow) não é naturalmente um "arquivo" — é uma chamada de API.

**Choice:** Criar `pipelines/insights/model_registry_state.yaml`, um arquivo versionado que documenta qual versão do modelo está em `champion`. A "correção" proposta pelo LLM é um diff nesse YAML. O PR, uma vez mergeado, é a **decisão documentada** — a aplicação de fato do alias no MLflow (`set_registered_model_alias`) fica como um passo manual/futuro (fora de escopo desta fase, coerente com a Fase 5/HITL não ter sido antecipada).

**Rationale:** Mantém 100% de reuso do pipeline de guardrails+PR sem criar um segundo tipo de "ação aprovada" (arquivo vs. chamada de API) — e o DEFINE (AT-003) só exige que a promoção não seja automática, não exige que o merge do PR já dispare a mudança de fato.

**Alternatives Rejected:**
1. `github_pr.py` ganhar um modo especial para ações de API (sem diff de arquivo) — rejeitado: quebraria a uniformidade do pipeline e exigiria tocar em código já shipped/testado da Fase 2 para um caso de uso.

**Consequences:**
- Depois do merge, alguém (humano ou uma automação futura da Fase 5) ainda precisa rodar `mlflow.set_registered_model_alias(...)` de fato — documentado como follow-up, não como lacuna escondida.

---

### Decision 4: Shadow check não tenta decidir "qual modelo é melhor" sozinho

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-05 |

**Context:** Isolation Forest é não-supervisionado — não existe "acurácia" objetiva para comparar `@challenger` vs. `@champion` sem rótulo de verdade.

**Choice:** O shadow check calcula estatísticas descritivas simples (taxa de anomalias sinalizadas, score médio) dos dois modelos na mesma janela recente e inclui essas estatísticas no corpo do PR — a decisão de "promover ou não" fica com o humano, informado pelos números, em vez de um critério automático de "vencedor".

**Rationale:** Fingir uma métrica de "acurácia" para um modelo não-supervisionado seria enganoso; expor os números brutos e deixar o humano decidir é mais honesto e está alinhado ao princípio de HITL que já rege todo o self-healing.

**Alternatives Rejected:**
1. Promover automaticamente se o challenger tiver "menos anomalias" (ou métrica similar arbitrária) — rejeitado: métrica sem fundamento estatístico real, risco de otimizar para o critério errado.

**Consequences:**
- O corpo do PR de promoção de modelo é mais longo/descritivo (inclui as estatísticas comparativas) do que os PRs de correção de contrato/código da Fase 2.

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `pipelines/self_healing/common/guardrails.py` | Modify | +3 prefixos na allowlist (`insights/`, `finops/`, `self_healing/`) | @security-reviewer | None |
| 2 | `pipelines/self_healing/common/failure_capture.py` | Modify | `write_event()` ganha parâmetro opcional `source_failure_type` | @airflow-specialist | None |
| 3 | `pipelines/insights/jobs/train_outlier_model.py` | Create | Features + treino do Isolation Forest, registra no MLflow (`@challenger`) | @ai-data-engineer | None |
| 4 | `pipelines/insights/jobs/generate_insights.py` | Create | Inferência com `@champion`, grava `gold.market_insights` | @ai-data-engineer | 3 |
| 5 | `pipelines/insights/jobs/drift_check.py` | Create | KS-test vs. baseline; shadow stats; emite evento de promoção | @ai-data-engineer | 2, 3, 4 |
| 6 | `pipelines/insights/model_registry_state.yaml` | Create | Estado versionado de qual modelo está em `champion` | @data-contracts-engineer | None |
| 7 | `pipelines/insights/dags/dag_train_outlier_model.py` | Create | DAG de treino (sob demanda / disparado por drift) | @airflow-specialist | 3 |
| 8 | `pipelines/insights/dags/dag_generate_insights.py` | Create | DAG hourly: inferência + drift check + shadow stats | @airflow-specialist | 4, 5 |
| 9 | `pipelines/insights/requirements.txt` | Create | Dependências do pacote de insights | (general) | None |
| 10 | `pipelines/finops/jobs/cost_monitor.py` | Create | Lê `system.billing.usage`/fallback, detecta anomalia | @data-platform-engineer | 2 |
| 11 | `pipelines/finops/dags/dag_finops_monitor.py` | Create | DAG hourly do Agente FinOps | @airflow-specialist | 10 |
| 12 | `pipelines/finops/requirements.txt` | Create | Dependências do pacote FinOps | (general) | None |
| 13 | `pipelines/insights/tests/test_train_outlier_model.py` | Create | Testes de feature engineering + treino (MLflow mockado) | @test-generator | 3 |
| 14 | `pipelines/insights/tests/test_generate_insights.py` | Create | Testes de inferência (modelo mockado) | @test-generator | 4 |
| 15 | `pipelines/insights/tests/test_drift_check.py` | Create | Testes de KS-test e shadow stats | @test-generator | 5 |
| 16 | `pipelines/insights/tests/test_dags_integrity.py` | Create | Integridade dos 2 DAGs de insights | @test-generator | 7, 8 |
| 17 | `pipelines/finops/tests/test_cost_monitor.py` | Create | Testes de detecção de anomalia (dados mockados) | @test-generator | 10 |
| 18 | `pipelines/finops/tests/test_dags_integrity.py` | Create | Integridade do DAG de FinOps | @test-generator | 11 |
| 19 | `pipelines/self_healing/tests/test_guardrails.py` | Modify | +casos de teste para os 3 novos prefixos da allowlist | @test-generator | 1 |
| 20 | `pipelines/self_healing/tests/test_failure_capture.py` | Create | Testes do `write_event()` com `source_failure_type` customizado (não existia teste dedicado na Fase 2) | @test-generator | 2 |

**Total Files:** 20 (18 novos + 2 modificados) — mais os `__init__.py` de scaffolding de pacote (`pipelines/insights/`, `pipelines/insights/jobs/`, `pipelines/insights/dags/`, `pipelines/insights/tests/`, `pipelines/finops/`, `pipelines/finops/jobs/`, `pipelines/finops/dags/`, `pipelines/finops/tests/`), não listados individualmente por serem vazios (mesmo padrão das Fases 1-2)

---

## Agent Assignment Rationale

| Agent | Files Assigned | Why This Agent |
|-------|----------------|------------------|
| @security-reviewer | 1 | Allowlist é controle de segurança — mesma especialização usada na Fase 2 |
| @airflow-specialist | 2, 7, 8, 11 | DAGs e o callback de captura de falha — SME de Airflow 3.0 |
| @ai-data-engineer | 3, 4, 5 | Feature engineering, treino de modelo, MLflow, drift — pipeline de ML de ponta a ponta |
| @data-contracts-engineer | 6 | Arquivo de estado versionado — mesma especialização usada para os contratos YAML da Fase 1 |
| @data-platform-engineer | 10 | Otimização/monitoramento de custo de plataforma de dados |
| @test-generator | 13-20 | Testes pytest — fixtures e mocks de MLflow/dados |

**Agent Discovery:**
- Scanned: `.claude/agents/**/*.md`
- Matched por: KB domains do DEFINE (`operations/cost`, `databricks/patterns/compute-patterns`, `ai-data-engineering`, `genai`, `data-quality`) + continuidade com os agentes já usados na Fase 2 para os arquivos reaproveitados

---

## Code Patterns

### Pattern 1: Treino do Isolation Forest + registro no MLflow com alias

```python
# pipelines/insights/jobs/train_outlier_model.py
from __future__ import annotations

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.ensemble import IsolationForest

MODEL_NAME = "main.insights.market_outlier_detector"
FEATURE_COLUMNS = ["price_change_pct", "volume_zscore", "lost_sales_value_zscore"]


def build_features(b3_df: pd.DataFrame, crm_df: pd.DataFrame) -> pd.DataFrame:
    b3_df = b3_df.assign(
        price_change_pct=b3_df.groupby("ticker")["price"].pct_change().fillna(0),
        volume_zscore=(b3_df["volume"] - b3_df["volume"].mean()) / b3_df["volume"].std(),
    )
    crm_df = crm_df.assign(
        lost_sales_value_zscore=(
            (crm_df["estimated_value"] - crm_df["estimated_value"].mean())
            / crm_df["estimated_value"].std()
        )
    )
    return b3_df.merge(crm_df, how="outer", left_index=True, right_index=True).fillna(0)


def train(features: pd.DataFrame) -> str:
    with mlflow.start_run() as run:
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(features[FEATURE_COLUMNS])

        mlflow.log_param("contamination", 0.05)
        mlflow.log_param("n_features", len(FEATURE_COLUMNS))
        model_info = mlflow.sklearn.log_model(
            model, artifact_path="model", registered_model_name=MODEL_NAME
        )

        client = mlflow.MlflowClient()
        client.set_registered_model_alias(MODEL_NAME, "challenger", model_info.registered_model_version)

        return run.info.run_id
```

### Pattern 2: Drift check (KS-test) + evento de promoção

```python
# pipelines/insights/jobs/drift_check.py
from __future__ import annotations

import pandas as pd
from scipy.stats import ks_2samp

DRIFT_P_VALUE_THRESHOLD = 0.05


def has_drifted(baseline: pd.Series, current: pd.Series) -> bool:
    _, p_value = ks_2samp(baseline, current)
    return p_value < DRIFT_P_VALUE_THRESHOLD


def build_shadow_comparison(champion_scores: pd.Series, challenger_scores: pd.Series) -> dict:
    return {
        "champion_anomaly_rate": float((champion_scores < 0).mean()),
        "challenger_anomaly_rate": float((challenger_scores < 0).mean()),
        "champion_mean_score": float(champion_scores.mean()),
        "challenger_mean_score": float(challenger_scores.mean()),
    }
```

### Pattern 3: Emitir evento de self-healing a partir de um novo tipo (reaproveitando a Fase 2)

```python
# pipelines/insights/dags/dag_generate_insights.py (trecho)
from __future__ import annotations

import json

from pipelines.self_healing.common.failure_capture import write_event


def emit_promotion_candidate(model_name: str, comparison: dict) -> str:
    detail = f"model={model_name} comparison={json.dumps(comparison)}"
    return write_event(source="dag_generate_insights", detail=detail, source_failure_type="model_promotion")
```

### Pattern 4: Extensão da allowlist (Fase 2, diff mínimo)

```python
# pipelines/self_healing/common/guardrails.py (diff)
ALLOWED_PATH_PREFIXES = (
    "pipelines/ingestion/contracts/",
    "pipelines/ingestion/producers/",
    "pipelines/ingestion/dags/",
    "pipelines/ingestion/common/",
    "pipelines/processing/",
    "pipelines/insights/",
    "pipelines/finops/",
    "pipelines/self_healing/",
)
```

---

## Data Flow

```text
1. dag_train_outlier_model lê silver.b3_quotes + silver.crm_lost_sales, monta features
   │
   ▼
2. Treina Isolation Forest, registra no MLflow com alias @challenger
   │
   ▼ (hourly)
3. dag_generate_insights carrega o modelo @champion, roda inferência sobre dados novos
   │
   ▼
4. Grava outliers em gold.market_insights
   │
   ▼
5. drift_check compara distribuição nova vs. baseline
   │
   ├── drift alto ──► dispara dag_train_outlier_model de novo
   │
   └── existe @challenger ──► shadow stats ──► write_event("model_promotion") ──┐
                                                                                  │
6. dag_finops_monitor lê system.billing.usage/fallback, compara consumo vs. histórico
   │
   └── anomalia ──► write_event("cost_anomaly") ────────────────────────────────┤
                                                                                  ▼
7. dag_self_healing_diagnose (Fase 2, sem mudança) processa ambos os tipos de evento
   │
   ▼
8. LLM diagnostica → guardrails (allowlist estendida) → PR no GitHub
   │
   ▼
9. Revisão humana decide o merge
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|-------------------|------------------|
| MLflow Tracking/Registry | SDK (`mlflow`) | Credenciais do workspace Databricks (mesma connection da Fase 2) |
| `system.billing.usage` | Spark SQL / Databricks SQL | Mesma credencial do Job Databricks |
| Airflow `dag_run` (fallback) | Airflow API interna | N/A — leitura local do metastore do Airflow |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|-----------------|
| Unit | `build_features` — engenharia de features | `test_train_outlier_model.py` | pytest + `pandas` | 80% |
| Unit | `train` — MLflow mockado, verifica chamadas de log/registro | `test_train_outlier_model.py` | pytest + mock do `mlflow` | 80% |
| Unit | `has_drifted`, `build_shadow_comparison` | `test_drift_check.py` | pytest + `scipy` real (determinístico) | 80% — cobre AT-002, AT-003 |
| Unit | `cost_monitor` — detecção de anomalia com dados sintéticos | `test_cost_monitor.py` | pytest — cobre AT-004 | 80% |
| Unit | `guardrails` — 3 novos prefixos aceitos | `test_guardrails.py` (Fase 2, estendido) | pytest | 100% dos novos casos |
| Unit | `write_event` com `source_failure_type` customizado | `test_failure_capture.py` (novo) | pytest + Delta real (tmp_path) | 80% |
| Integration | DAGs importam sem erro | `test_dags_integrity.py` (insights, finops) | `pytest.importorskip("airflow")`, validar via Docker real (mesmo padrão das Fases 1-2) | 3 DAGs novos |
| E2E | Fluxo completo AT-001 a AT-004 | Manual, contra workspace Databricks Free Edition real quando provisionado | — | Happy path |

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|----------------------|--------|
| MLflow indisponível/timeout ao registrar modelo | Retry com backoff (mesmo padrão da Fase 1/2); se esgotar, a run de treino falha e o Airflow retenta o DAG inteiro | Yes |
| `system.billing.usage` inacessível | Fallback automático para `dag_run.duration` (SHOULD do DEFINE) | No — troca de fonte, não é erro fatal |
| Drift check com dados insuficientes (poucas linhas na janela) | Pula o check nesse ciclo, loga aviso, tenta de novo no próximo ciclo hourly | No |
| `write_event` falha ao gravar em `self_healing_events` | Mesma política já validada na Fase 2 (`on_task_failure`): loga e não propaga, para não quebrar o DAG chamador | No |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|----------------|
| `MLFLOW_MODEL_NAME` | string | `main.insights.market_outlier_detector` | Nome do modelo registrado (3 níveis, Unity Catalog) |
| `DRIFT_P_VALUE_THRESHOLD` | float | `0.05` | Limiar do KS-test para disparar retreino |
| `ISOLATION_FOREST_CONTAMINATION` | float | `0.05` | Proporção esperada de outliers |
| `FINOPS_ANOMALY_THRESHOLD_STDDEV` | float | `2.0` | Nº de desvios-padrão acima da média histórica para considerar anomalia de custo |
| `GOLD_INSIGHTS_PATH` | string | (Variable, definido no Build) | Caminho da tabela `gold.market_insights` |

---

## Security Considerations

- `model_registry_state.yaml` fica dentro da allowlist do self-healing — mesma proteção de guardrail de conteúdo (Fase 2) contra diffs perigosos
- Nenhuma promoção de modelo ou mudança de custo é aplicada automaticamente — sempre via PR revisado (Decision 3, 4)
- Credenciais do MLflow/Databricks reaproveitam a mesma Connection da Fase 2, sem duplicar segredo

---

## Observability

| Aspect | Implementation |
|--------|------------------|
| Logging | Logging estruturado; cada run de treino loga `run_id` do MLflow para rastreabilidade |
| Metrics | Contagem de eventos de `model_promotion`/`cost_anomaly` por execução (base para o Painel Sentinela, ainda não construído) |
| Tracing | Fora de escopo — mesma decisão das Fases 1-2 |

---

## Pipeline Architecture

### DAG Diagram

```text
[silver.b3_quotes + silver.crm_lost_sales] ──► [dag_train_outlier_model] ──► [MLflow @challenger]
                                                        ▲                              │
                                                        │ (drift)                      │
[dag_generate_insights, hourly] ──► [gold.market_insights]                            │
        │                                                                              │
        └──► [drift_check + shadow_stats] ──► [self_healing_events: model_promotion] ◄┘
[dag_finops_monitor, hourly] ──► [self_healing_events: cost_anomaly]
        │
        ▼
[dag_self_healing_diagnose] (Fase 2, inalterado) ──► [PR no GitHub]
```

### Partition Strategy

| Table | Partition Key | Granularity | Rationale |
|-------|-------------------|-------------|--------------|
| `gold.market_insights` | `generated_at` (data) | Diária | Consistente com o padrão de particionamento por data já usado nas Fases 1-2 |

### Incremental Strategy

| Model | Strategy | Key Column | Lookback |
|-------|----------|--------------|-----------|
| `gold.market_insights` | `incremental_by_time` (append) | `generated_at` | 1h (janela da última inferência) |
| Treino do modelo | `full_refresh` a cada disparo (sem incremental) | N/A | Todo o histórico disponível na Silver |

### Schema Evolution Plan

| Change Type | Handling | Rollback |
|-------------|----------|--------------|
| Novo `source_failure_type` em `self_healing_events` | Aditivo por natureza — coluna já é STRING livre (Decision 2) | N/A, não requer migração |
| Nova feature no modelo | Retreino completo registra nova versão no MLflow; versão anterior continua acessível por alias/version number | Reverter alias `@champion` para a versão anterior |

### Data Quality Gates

| Gate | Tool | Threshold | Action on Failure |
|------|------|-----------|----------------------|
| Drift na distribuição de features | `drift_check.has_drifted` (KS-test) | p-value < 0.05 | Dispara retreino automaticamente (não bloqueia, apenas retreina) |
| Anomalia de custo por job | `cost_monitor` | > 2 desvios-padrão da média histórica | Gera evento de self-healing, não bloqueia a execução do job |
| Promoção de modelo | Guardrails da Fase 2 (allowlist + conteúdo) | 0 promoções fora da allowlist | Registrado em `self_healing_rejections` |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|------------|
| 1.0 | 2026-08-05 | design-agent | Initial version — a partir de DEFINE_FASE3_INSIGHTS_FINOPS.md, com pesquisa web validando MLflow e system.billing.usage no Free Edition |
| 1.1 | 2026-08-06 | ship-agent | Shipped and archived |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_FASE3_INSIGHTS_FINOPS.md`
