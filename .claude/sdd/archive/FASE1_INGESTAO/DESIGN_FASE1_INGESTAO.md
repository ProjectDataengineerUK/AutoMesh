# DESIGN: Fase 1 — Ingestão (Kafka/Airflow)

> Technical design for implementing the Fase 1 ingestion layer — Kafka + Airflow, one real source (brapi.dev/B3) plus simulated corporate sources, validated against versioned data contracts before landing in Bronze.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | FASE1_INGESTAO |
| **Date** | 2026-07-31 |
| **Author** | design-agent |
| **DEFINE** | [DEFINE_FASE1_INGESTAO.md](./DEFINE_FASE1_INGESTAO.md) |
| **Status** | ✅ Shipped |

---

## Architecture Overview

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│                         FASE 1 — INGESTÃO (SYSTEM DIAGRAM)                         │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  [brapi.dev API]──poll 5min──►[b3_quotes_producer]──►[Kafka: market.b3_quotes.v1] │
│                                                                          │          │
│  [sim: infra gen]────────────►[simulated_infra_producer]──►[Kafka: infra.*.v1] │   │
│                                                                          │      │   │
│                                                                          ▼      ▼   │
│                                                          ┌───────────────────────┐  │
│                                                          │   AIRFLOW (Astro/     │  │
│  [sim: CRM Lost Sales]──file──►[crm_generator]──────────►   Databricks trial)   │  │
│                                                          │                       │  │
│                                                          │ dag_ingest_kafka_     │  │
│                                                          │   market / infra      │  │
│                                                          │ dag_ingest_batch_crm  │  │
│                                                          │   (embeds shared      │  │
│                                                          │    validate_and_      │  │
│                                                          │    promote TaskGroup) │  │
│                                                          └──────────┬────────────┘  │
│                                                                     │               │
│                                                          ┌──────────▼───────────┐   │
│                                                          │  contract_validator  │   │
│                                                          │  (contracts/*.yaml)  │   │
│                                                          └──────┬─────────┬─────┘   │
│                                                            valid│         │invalid  │
│                                                          ┌──────▼───┐ ┌───▼──────┐  │
│                                                          │  Bronze  │ │   DLQ    │  │
│                                                          │  (Delta, │ │  (Delta, │  │
│                                                          │  via     │ │  bronze_ │  │
│                                                          │ deltalake)│ │  dlq)    │  │
│                                                          └──────────┘ └──────────┘  │
│                                                                     │               │
│                                                          (consumido pela Fase 2)    │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| B3 Quotes Producer | Faz polling da brapi.dev (~5 min) e publica cotações no Kafka | Python, `requests`, `confluent-kafka` |
| Simulated Source Generators | Geram eventos sintéticos (infra telemetry, usage logs) e registros batch (CRM Lost Sales) | Python, `Faker`, `confluent-kafka` |
| Kafka (gerenciado) | Broker de streaming; um tópico por fonte | Confluent Cloud (free/trial tier) |
| Airflow (gerenciado ou self-hosted) | Orquestra todos os DAGs de ingestão | Airflow 3.0 (Astronomer trial ou instância no Databricks trial workspace) |
| Contract Validator | Valida um lote de registros contra o contrato YAML da fonte correspondente | Python, `pyyaml` + `jsonschema` |
| Data Contracts | Schema, SLA, owner, regra de compatibilidade por fonte (ODCS-lite) | YAML versionado no repo (`contracts/`) |
| Bronze Writer | Grava registros válidos como tabela Delta particionada; registros inválidos na DLQ | Python, `deltalake` (delta-rs) — sem cluster Spark provisionado nesta fase |

---

## Key Decisions

### Decision 1: Airflow 3.0 asset/sensor deferrable consumindo Kafka em micro-lote

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-31 |

**Context:** A Fase 1 precisa decidir como Kafka e Airflow se articulam para ingerir tanto a fonte real (B3) quanto as simuladas, operando dentro de uma conta cloud trial (sem orçamento para compute contínuo).

**Choice:** Cada DAG de ingestão usa um sensor deferrable (`deferrable=True`) para escutar o tópico Kafka correspondente e consumir em micro-lote a cada execução, em vez de um consumidor contínuo.

**Rationale:** Já validado no brainstorm (`BRAINSTORM_FASE1_INGESTAO.md`, Approach B) — bate com a narrativa do `context.md` ("Airflow escuta o evento via Kafka"), usa o *asset-aware scheduling* nativo do Airflow 3.0 (KB `airflow/patterns/sensors-triggers.md`) e evita computação contínua numa conta trial.

**Alternatives Rejected:**
1. Kafka Connect Sink direto pro Bronze — rejeitado por adicionar um componente de infra extra numa conta trial e por enfraquecer a narrativa de orquestração unificada no Airflow.
2. Spark Structured Streaming contínuo — rejeitado por exigir cluster/job rodando continuamente, incompatível com o orçamento de conta trial.

**Consequences:**
- Cadência de consumo fica acoplada ao intervalo do DAG (não é streaming "puro" de milissegundos) — aceitável, já que o SLA de freshness da B3 é de 5 minutos.
- Ganha-se um único painel (Airflow UI) mostrando todo o fluxo de ingestão.

---

### Decision 2: Bronze escrito via `deltalake` (delta-rs), sem cluster Spark nesta fase

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-31 |

**Context:** O DEFINE exige que dados válidos cheguem ao Bronze como tabelas Delta, mas não especifica o motor de escrita. Provisionar um cluster Databricks/PySpark só para gravar Delta a partir de tarefas do Airflow seria caro numa conta trial e antecipa o processamento pesado que é escopo da Fase 2.

**Choice:** As tasks do Airflow escrevem diretamente nas tabelas Delta usando a biblioteca `deltalake` (delta-rs), que não requer um cluster Spark ativo.

**Rationale:** Mantém o formato de tabela (Delta) exigido pelo DEFINE e pela Fase 2, sem o custo de manter um cluster provisionado só para ingestão. `databricks-spark-expert` e PySpark entram na Fase 2, quando o processamento pesado (Bronze→Silver, auditoria de schema) de fato precisa de Spark.

**Alternatives Rejected:**
1. Job Databricks/PySpark disparado pelo Airflow a cada micro-lote — rejeitado: cluster de curta duração ainda consome quota de trial repetidamente e adiciona latência de start-up a cada execução (5 em 5 minutos).
2. Gravar apenas Parquet/JSON cru, sem Delta — rejeitado: não atende ao critério de sucesso do DEFINE ("tabelas Delta no Bronze").

**Consequences:**
- Ganha-se custo próximo de zero de computação para a camada de ingestão.
- A Fase 2 precisará abrir essas tabelas Delta via Databricks normalmente (formato é compatível — Delta Lake é um formato aberto, não uma feature exclusiva de cluster).

---

### Decision 3: Contrato de dados em YAML "ODCS-lite" (subconjunto do ODCS v3.1)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-31 |

**Context:** É preciso um formato de contrato de dados simples o bastante para validar em toda execução de DAG, mas expressivo o suficiente para schema, SLA e regra de compatibilidade (exigidos no DEFINE).

**Choice:** Um YAML por fonte, seguindo um subconjunto do ODCS v3.1 (`metadata`, `schema`, `quality.freshness`, `quality.completeness`, `evolution.compatibility`) — omitindo seções não aplicáveis a este estágio (`pricing`, `roles`, `vendors`).

**Rationale:** Alinhado ao padrão já documentado na KB (`data-quality/patterns/data-contract-authoring.md` e `controls/data-contracts/data-contract-baseline.md`), evitando inventar um formato novo. Um schema registry completo (Confluent Schema Registry + Avro) é overkill para o volume desta fase.

**Alternatives Rejected:**
1. Avro + Confluent Schema Registry — rejeitado: exige provisionar mais um serviço gerenciado na conta trial, para um throughput baixo que não justifica o custo operacional.
2. JSON Schema solto por fonte (sem metadata/SLA) — rejeitado: perderia os campos de SLA e ownership exigidos no DEFINE.

**Consequences:**
- Validação é feita em Python puro (`jsonschema`/checagem manual), não em um registry centralizado — aceitável no volume atual.
- Migrar para um schema registry completo fica mais fácil no futuro, pois o contrato já documenta schema e regra de compatibilidade.

---

### Decision 4: DLQ unificada como tabela Delta, não tópicos Kafka por fonte

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-31 |

**Context:** Fontes streaming (Kafka) e batch (CRM) precisam de um destino comum para registros que violam o contrato, sem duplicar a lógica de tratamento de erro.

**Choice:** Uma única tabela Delta `bronze_dlq`, particionada por `source` e `failure_reason`, usada tanto pelas DAGs de Kafka quanto pela DAG batch.

**Rationale:** Um único código de escrita (`bronze_writer.write_dlq()`) atende às duas origens, evitando manter 3+ tópicos Kafka extras só para DLQ — reduz componentes de infra numa conta trial.

**Alternatives Rejected:**
1. Um tópico Kafka `automesh.dlq.<fonte>.v1` por fonte — rejeitado: multiplica tópicos a gerenciar sem necessidade, já que nada consome a DLQ em tempo real nesta fase (a leitura é batch, pela Fase 2/self-healing).

**Consequences:**
- A Fase 2 (agente de self-healing) lê a DLQ como uma tabela Delta comum, com uma query filtrando por `source`, em vez de assinar múltiplos tópicos.

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `pipelines/ingestion/contracts/b3_quotes.contract.yaml` | Create | Contrato de dados da fonte real B3 | @data-contracts-engineer | None |
| 2 | `pipelines/ingestion/contracts/infra_telemetry.contract.yaml` | Create | Contrato da telemetria de infra simulada | @data-contracts-engineer | None |
| 3 | `pipelines/ingestion/contracts/usage_logs.contract.yaml` | Create | Contrato dos logs de uso simulados | @data-contracts-engineer | None |
| 4 | `pipelines/ingestion/contracts/crm_lost_sales.contract.yaml` | Create | Contrato do CRM Lost Sales simulado | @data-contracts-engineer | None |
| 5 | `pipelines/ingestion/contracts/pdf_contracts.contract.yaml` | Create | Contrato (schema apenas) para PDFs/contratos | @data-contracts-engineer | None |
| 6 | `pipelines/ingestion/contracts/video_transcripts.contract.yaml` | Create | Contrato (schema apenas) para transcrições de vídeo | @data-contracts-engineer | None |
| 7 | `pipelines/ingestion/producers/b3_quotes_producer.py` | Create | Producer real: polling brapi.dev → Kafka | @streaming-engineer | 1 |
| 8 | `pipelines/ingestion/producers/simulated_infra_producer.py` | Create | Gera telemetria/logs sintéticos → Kafka | @streaming-engineer | 2, 3 |
| 9 | `pipelines/ingestion/producers/simulated_crm_generator.py` | Create | Gera registros sintéticos de CRM Lost Sales (arquivo/API simulada) | @streaming-engineer | 4 |
| 10 | `pipelines/ingestion/common/kafka_config.py` | Create | Configuração compartilhada de producer/consumer Kafka | @streaming-engineer | None |
| 11 | `pipelines/ingestion/common/contract_validator.py` | Create | Carrega contrato YAML e valida um lote de registros | @data-quality-analyst | 1-6 |
| 12 | `pipelines/ingestion/common/bronze_writer.py` | Create | Escreve registros válidos no Bronze (Delta) e inválidos na DLQ | @lakehouse-architect | 11 |
| 13 | `pipelines/ingestion/dags/dag_ingest_kafka_market.py` | Create | DAG: consome `b3_quotes`, valida e promove ao Bronze | @airflow-specialist | 7, 10, 11, 12 |
| 14 | `pipelines/ingestion/dags/dag_ingest_kafka_infra.py` | Create | DAG: consome `infra_telemetry` + `usage_logs` (dynamic task mapping), valida e promove | @airflow-specialist | 8, 10, 11, 12 |
| 15 | `pipelines/ingestion/dags/dag_ingest_batch_crm.py` | Create | DAG: lê o CRM simulado, valida e promove | @airflow-specialist | 9, 11, 12 |
| 16 | `pipelines/ingestion/tests/test_contract_validator.py` | Create | Testes unitários do validador de contrato | @test-generator | 11 |
| 17 | `pipelines/ingestion/tests/test_bronze_writer.py` | Create | Testes unitários da escrita Bronze/DLQ | @test-generator | 12 |
| 18 | `pipelines/ingestion/tests/test_dags_integrity.py` | Create | Teste de integridade: todos os DAGs importam sem erro de ciclo | @test-generator | 13, 14, 15 |
| 19 | `pipelines/ingestion/requirements.txt` | Create | Dependências Python do pacote de ingestão | (general) | None |

**Total Files:** 19

---

## Agent Assignment Rationale

> Agents discovered from `.claude/agents/` — Build phase invokes matched specialists.

| Agent | Files Assigned | Why This Agent |
|-------|----------------|------------------|
| @data-contracts-engineer | 1-6 | Especialista em autoria de contratos de dados (ODCS), SLA e governança de schema — exatamente o formato definido na Decision 3 |
| @streaming-engineer | 7-10 | Especialista em pipelines Kafka/Flink/CDC — producers, consumer config e padrões de streaming SQL |
| @data-quality-analyst | 11 | Especialista em Great Expectations/dbt tests/data contracts — validação de payload contra schema é o núcleo da sua especialidade |
| @lakehouse-architect | 12 | Especialista em formatos de tabela abertos (Delta/Iceberg) e catálogo — cobre a Decision 2 (escrita Delta sem cluster Spark) |
| @airflow-specialist | 13-15 | SME de Airflow 3.0 (TaskFlow, asset-aware scheduling, dynamic task mapping) — cobre a Decision 1 |
| @test-generator | 16-18 | Especialista em testes pytest — fixtures e casos de borda para os módulos compartilhados e para integridade dos DAGs |
| (general) | 19 | `requirements.txt` não exige especialista — Build lida diretamente |

**Agent Discovery:**
- Scanned: `.claude/agents/**/*.md`
- Matched by: purpose keywords (contratos, streaming, qualidade, Delta/lakehouse, Airflow, testes), KB domains do DEFINE (`airflow`, `streaming`, `controls/data-contracts`, `data-quality`)

---

## Code Patterns

### Pattern 1: B3 Quotes Producer (polling + idempotent produce)

```python
# pipelines/ingestion/producers/b3_quotes_producer.py
# Adapted from KB: streaming/patterns/kafka-producer-consumer.md
from __future__ import annotations

import json
import logging
import time

import requests
from confluent_kafka import Producer

logger = logging.getLogger(__name__)

BRAPI_BASE_URL = "https://brapi.dev/api/quote"
TICKERS = ["PETR4", "VALE3", "ITUB4"]  # subset for MVP
TOPIC = "automesh.market.b3_quotes.v1"

producer_config = {
    "bootstrap.servers": "{{ KAFKA_BOOTSTRAP_SERVERS }}",
    "enable.idempotence": True,
    "acks": "all",
    "retries": 5,
    "compression.type": "zstd",
    "linger.ms": 10,
}
producer = Producer(producer_config)


def fetch_quotes(tickers: list[str]) -> list[dict]:
    """Poll brapi.dev with basic retry/backoff for transient failures (AT-003)."""
    for attempt in range(3):
        try:
            resp = requests.get(
                f"{BRAPI_BASE_URL}/{','.join(tickers)}",
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
        except requests.RequestException as e:
            wait = 2 ** attempt
            logger.warning("brapi.dev fetch failed (attempt %d): %s — retrying in %ds", attempt, e, wait)
            time.sleep(wait)
    logger.error("brapi.dev unreachable after retries — skipping this poll cycle")
    return []


def publish_quotes(quotes: list[dict]) -> None:
    def on_delivery(err, msg):
        if err:
            logger.error("Delivery failed: %s", err)

    for q in quotes:
        payload = {
            "ticker": q["symbol"],
            "price": q["regularMarketPrice"],
            "volume": q.get("regularMarketVolume"),
            "quote_timestamp": q["regularMarketTime"],
        }
        producer.produce(
            topic=TOPIC,
            key=payload["ticker"].encode("utf-8"),
            value=json.dumps(payload).encode("utf-8"),
            on_delivery=on_delivery,
        )
    producer.flush()


if __name__ == "__main__":
    publish_quotes(fetch_quotes(TICKERS))
```

### Pattern 2: Airflow DAG — deferrable Kafka sensor + shared validate_and_promote TaskGroup

> Verificado contra Airflow 3.0.0 + Redpanda reais (ver `docker-compose.local.yml`). O provider `apache-airflow-providers-apache-kafka` expõe `AwaitMessageSensor` (aguarda e opcionalmente consome/commita) e `AwaitMessageTriggerFunctionSensor` (aguarda e dispara um `event_triggered_function` obrigatório) — para o padrão "só detectar chegada, deixar a task seguinte consumir o lote", `AwaitMessageSensor` com `commit_offset=False` é o ajuste correto; a primeira versão deste pattern usava `AwaitMessageTriggerFunctionSensor` sem o argumento obrigatório `event_triggered_function` e falhava no parse do DAG.

```python
# pipelines/ingestion/dags/dag_ingest_kafka_market.py
# Adapted from KB: airflow/patterns/sensors-triggers.md + airflow/patterns/error-handling.md
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task
from airflow.providers.apache.kafka.sensors.kafka import AwaitMessageSensor

from pipelines.ingestion.common.kafka_config import consume_batch
from pipelines.ingestion.common.contract_validator import validate_batch
from pipelines.ingestion.common.bronze_writer import write_bronze, write_dlq

SOURCE = "b3_quotes"
TOPIC = "automesh.market.b3_quotes.v1"

RETRY_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=15),
}


@dag(
    dag_id="dag_ingest_kafka_market",
    schedule="*/5 * * * *",
    start_date=datetime(2026, 7, 31, tzinfo=timezone.utc),
    catchup=False,
    default_args=RETRY_ARGS,
    tags=["ingestion", "kafka", "fase1"],
)
def dag_ingest_kafka_market():
    wait_for_messages = AwaitMessageSensor(
        task_id="wait_for_b3_quotes",
        kafka_config_id="kafka_default",
        topics=[TOPIC],
        apply_function="pipelines.ingestion.common.kafka_config.has_messages",
        commit_offset=False,
        poll_timeout=30,
        poll_interval=15,
    )

    @task
    def consume_microbatch() -> list[dict]:
        return consume_batch(topic=TOPIC, max_messages=500)

    @task
    def validate_and_promote(records: list[dict]) -> None:
        """Shared validate_and_promote step (embedded TaskGroup per Design Decision 1)."""
        valid, invalid = validate_batch(source=SOURCE, records=records)
        if valid:
            write_bronze(source=SOURCE, records=valid)
        if invalid:
            write_dlq(source=SOURCE, records=invalid)

    wait_for_messages >> validate_and_promote(consume_microbatch())


dag_ingest_kafka_market()
```

`commit_offset=False` é deliberado: o sensor e a task `consume_microbatch` compartilham o mesmo consumer group (`group.id` da connection `kafka_default`); se o sensor commitasse o offset da mensagem que disparou o evento, essa mensagem nunca chegaria à task de consumo real — o commit fica a cargo de `consume_batch()`, que usa `enable.auto.commit: False` e commit manual (at-least-once).

### Pattern 3: Contract Validator (loads ODCS-lite YAML, validates a batch)

```python
# pipelines/ingestion/common/contract_validator.py
# Adapted from KB: data-quality/patterns/data-contract-authoring.md + schema-validation.md
from __future__ import annotations

from pathlib import Path

import yaml

CONTRACTS_DIR = Path(__file__).parent.parent / "contracts"

_TYPE_MAP = {
    "string": str,
    "decimal": (int, float),
    "long": int,
    "timestamp": str,  # ISO-8601 string at this stage; cast happens in bronze_writer
}


def _load_contract(source: str) -> dict:
    path = CONTRACTS_DIR / f"{source}.contract.yaml"
    with path.open() as f:
        return yaml.safe_load(f)


def validate_batch(source: str, records: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split a batch into (valid, invalid) per the source's contract. Never raises."""
    contract = _load_contract(source)
    columns = contract["schema"]["columns"]

    valid, invalid = [], []
    for record in records:
        reason = _check_record(record, columns)
        if reason is None:
            valid.append(record)
        else:
            invalid.append({**record, "_failure_reason": reason})
    return valid, invalid


def _check_record(record: dict, columns: list[dict]) -> str | None:
    for col in columns:
        name, required, expected_type = col["name"], col.get("required", False), col["type"]
        value = record.get(name)

        if value is None:
            if required:
                return f"null_violation:{name}"
            continue

        py_type = _TYPE_MAP.get(expected_type)
        if py_type and not isinstance(value, py_type):
            return f"type_mismatch:{name}"

    return None
```

### Pattern 4: Configuration — ODCS-lite contract structure

```yaml
# pipelines/ingestion/contracts/b3_quotes.contract.yaml
apiVersion: v3.1.0-lite
kind: DataContract
metadata:
  name: b3_quotes
  version: 1
  description: "Cotações de ações B3 via brapi.dev — uma linha por ticker por poll"
  owner: automesh-project
  domain: market
  classification: internal

schema:
  type: kafka_topic
  topic: automesh.market.b3_quotes.v1
  columns:
    - name: ticker
      type: string
      required: true
    - name: price
      type: decimal
      required: true
      constraints:
        minimum: 0
    - name: volume
      type: long
      required: false
    - name: quote_timestamp
      type: timestamp
      required: true

quality:
  freshness:
    maxStaleness: PT5M
  completeness:
    ticker: 1.0
    price: 1.0

evolution:
  compatibility: additive-only

consumers:
  - name: fase1_bronze_writer
    usage: "Promoção ao Bronze após validação"
  - name: fase2_self_healing
    usage: "Leitura da DLQ para correção de schema (futuro)"
```

---

## Data Flow

```text
1. B3 Quotes Producer faz polling da brapi.dev a cada 5 min
   │
   ▼
2. Producer publica no tópico Kafka automesh.market.b3_quotes.v1
   (geradores simulados publicam em infra_telemetry/usage_logs, ou geram arquivo pro CRM)
   │
   ▼
3. Airflow (sensor deferrable) detecta mensagens/arquivo novo e dispara o consumo em micro-lote
   │
   ▼
4. Task validate_and_promote chama contract_validator.validate_batch() contra o YAML da fonte
   │
   ├── válidos ──► bronze_writer.write_bronze() → tabela Delta Bronze (particionada fonte/data)
   │
   └── inválidos ─► bronze_writer.write_dlq() → tabela Delta bronze_dlq (motivo anexado)
   │
   ▼
5. Fase 2 consome Bronze (dados válidos) e bronze_dlq (para o futuro agente de self-healing)
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|-------------------|------------------|
| brapi.dev | REST API | Sem auth para o tier gratuito básico (token opcional para rate limit maior — via Airflow Connection se adicionado) |
| Kafka (Confluent Cloud trial) | SDK (`confluent-kafka`) | SASL/SSL com API key + secret via Airflow Connection `kafka_default` |
| Bronze storage (ADLS/S3, conforme provedor trial escolhido) | SDK (`deltalake`) | Credenciais de storage via Airflow Connection/Variable, nunca hardcoded |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|-----------------|
| Unit | `contract_validator.validate_batch` — nulos, tipos, contratos válidos/inválidos | `tests/test_contract_validator.py` | pytest | 80%, cobre AT-002 |
| Unit | `bronze_writer.write_bronze` / `write_dlq` — particionamento, motivo anexado | `tests/test_bronze_writer.py` | pytest + `deltalake` local (tmp dir) | 80% |
| Integration | DAGs importam sem erro, sem dependência circular, `validate_and_promote` embutido corretamente | `tests/test_dags_integrity.py` | pytest + Airflow `DagBag` | Todos os 3 DAGs |
| Integration | Producer → Kafka → consumo em micro-lote (fluxo AT-001) | Manual/CI com Kafka local (`docker-compose` de teste) | pytest + `confluent-kafka` test cluster | Happy path |
| E2E | Fluxo completo: brapi.dev indisponível → retry → DAGs seguem rodando (AT-003) | Manual | Simular falha de rede na chamada `fetch_quotes` | Edge case |

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|----------------------|--------|
| brapi.dev indisponível/timeout | Retry com backoff exponencial (3 tentativas) dentro do producer; se esgotar, loga e pula o ciclo sem quebrar o DAG (AT-003) | Yes |
| Registro viola o contrato (nulo/tipo) | Roteado para `bronze_dlq` com `_failure_reason`; pipeline principal continua (AT-002) | No (fica na DLQ até a Fase 2 tratar) |
| Kafka consumer error (offset/partição) | Log estruturado + `on_failure_callback` (Slack, se configurado); task falha e é retentada pelo Airflow | Yes (`retry_exponential_backoff`, KB `airflow/patterns/error-handling.md`) |
| Falha ao escrever no Bronze/DLQ (Delta) | Task falha, Airflow retenta; se esgotar, alerta via `on_failure_callback` | Yes |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|----------------|
| `KAFKA_BOOTSTRAP_SERVERS` | string | (Connection `kafka_default`) | Endpoint do cluster Kafka trial |
| `B3_POLL_INTERVAL_MINUTES` | int | `5` | Intervalo de polling do producer B3, respeitando o rate limit da brapi.dev |
| `B3_TICKERS` | list[string] | `["PETR4","VALE3","ITUB4"]` | Subconjunto de tickers cobertos no MVP |
| `CONTRACTS_DIR` | string | `pipelines/ingestion/contracts/` | Diretório dos contratos YAML |
| `BRONZE_BASE_PATH` | string | (Variable, definido em Build) | Caminho base das tabelas Delta do Bronze |
| `DLQ_TABLE_PATH` | string | `{BRONZE_BASE_PATH}/_dlq/bronze_dlq` | Caminho da tabela Delta unificada de DLQ |

---

## Security Considerations

- Credenciais de Kafka e de storage nunca hardcoded — sempre via Airflow Connections/Variables (KB `airflow/quick-reference.md`: "Hardcode connections" é pitfall listado)
- Token opcional da brapi.dev (se usado para aumentar rate limit) armazenado como Airflow Connection, não em código
- Nenhuma das fontes desta fase contém PII (contratos marcam `PII: No`); revisitar quando os contratos de PDFs/CRM forem aprofundados na Fase 4/2
- Acesso ao storage do Bronze via credencial com escopo mínimo (somente escrita no path de ingestão), preparando terreno para o RBAC/ABAC completo da Fase 5

---

## Observability

| Aspect | Implementation |
|--------|------------------|
| Logging | Logging estruturado (JSON) em producers e tasks Airflow; motivo de falha sempre anexado ao registro na DLQ |
| Metrics | Contagem de registros válidos vs. DLQ por execução de DAG, exposta via log (base para o Painel Sentinela da Fase 3) |
| Tracing | Fora de escopo nesta fase — não há chamadas distribuídas complexas o suficiente para justificar tracing dedicado ainda |

---

## Pipeline Architecture

### DAG Diagram

```text
[brapi.dev]──extract──►[Kafka b3_quotes]──►[dag_ingest_kafka_market]──┐
[sim infra/logs]──extract──►[Kafka infra.*]──►[dag_ingest_kafka_infra]──┤──► [validate_and_promote] ──► [Bronze Delta]
[sim CRM]──extract──►[dag_ingest_batch_crm]────────────────────────────┘                    │
                                                                                               └──► [bronze_dlq]
```

### Partition Strategy

| Table | Partition Key | Granularity | Rationale |
|-------|-------------------|-------------|--------------|
| `bronze.b3_quotes` | `ingestion_date` | Diária | Volume baixo (~poucos MB/dia); particionamento diário já é suficiente para consultas da Fase 2 |
| `bronze.infra_telemetry`, `bronze.usage_logs` | `ingestion_date` | Diária | Mesmo padrão — sem consumidor definido ainda, mantém simplicidade |
| `bronze.crm_lost_sales` | `ingestion_date` | Diária | Alinhado à cadência de extração batch diária |
| `bronze_dlq` | `source`, `ingestion_date` | Diária | Permite à Fase 2 filtrar rapidamente a DLQ por fonte |

### Incremental Strategy

| Model | Strategy | Key Column | Lookback |
|-------|----------|--------------|-----------|
| `bronze.b3_quotes` | `incremental_by_time` (append-only) | `quote_timestamp` | N/A (sem dedup nesta fase) |
| `bronze.crm_lost_sales` | `incremental_by_time` (append diário) | `ingestion_date` | 1 dia |
| `bronze_dlq` | `incremental_by_time` (append-only) | `ingestion_date` | N/A |

### Schema Evolution Plan

| Change Type | Handling | Rollback |
|-------------|----------|----------|
| New column | Adicionar como opcional no contrato (`required: false`), Bronze aceita `null` até backfill | Remover a coluna do contrato |
| Type change | Período de dual-write não se aplica ainda (volume baixo) — nova versão do contrato (`version: N+1`) com migração manual documentada | Reverter para a versão anterior do contrato |
| Column removal | Marcar como deprecated no contrato por 30 dias antes de remover (`evolution.compatibility: additive-only` já bloqueia remoção direta) | Readicionar a coluna ao contrato |

### Data Quality Gates

| Gate | Tool | Threshold | Action on Failure |
|------|------|-----------|----------------------|
| Campos obrigatórios não-nulos | `contract_validator.validate_batch` | 0 nulos em campos `required: true` | Registro vai para `bronze_dlq` (AT-002) |
| Tipo de dado compatível com o contrato | `contract_validator.validate_batch` | 100% dos campos no tipo esperado | Registro vai para `bronze_dlq` |
| Freshness da B3 | Comparação `quote_timestamp` vs. horário de ingestão | ≤ 5 minutos | Log de alerta (sem bloquear o pipeline — SHOULD, não MUST) |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|------------|
| 1.0 | 2026-07-31 | design-agent | Initial version — a partir de DEFINE_FASE1_INGESTAO.md |
| 1.1 | 2026-08-01 | ship-agent | Shipped and archived |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_FASE1_INGESTAO.md`
