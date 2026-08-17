---
source: "Lições reais de build — InsuranceLakehousePlatform Fases 1-2 (2026-07), SHIPPED reports"
confidence: high
validated: "2026-07-22"
---

# Padrões: Spark Structured Streaming + Confluent Schema Registry + CDC

> Padrões validados em pipeline real Kafka (Avro) → Bronze → Silver com Debezium CDC.
> Agentes: `spark-streaming-architect`, `databricks-spark-expert`, `streaming-engineer`.

---

## 1. `SchemaRegistryClient` não é serializável entre driver e executors

O client do Confluent Schema Registry **não pode ser capturado na closure** de uma UDF —
falha na serialização driver→executor. Instanciar **lazy, com cache por processo, dentro da UDF**:

```python
_registry_client = None

def _get_registry():
    global _registry_client
    if _registry_client is None:
        from confluent_kafka.schema_registry import SchemaRegistryClient
        _registry_client = SchemaRegistryClient({"url": SR_URL, ...})
    return _registry_client
```

## 2. `from_avro` nativo não é resiliente — padrão DLQ com UDF try/except

O `from_avro` do PySpark **derruba o micro-batch inteiro** ao encontrar uma mensagem
malformada. Para DLQ em streams Avro+Kafka, parsear via UDF com try/except e separar
sucesso/falha em dois DataFrames:

```python
@udf(returnType=parsed_schema)
def parse_avro_safe(value):
    try:
        return deserialize(value, _get_registry())   # sucesso
    except Exception as e:
        return None                                   # vai para a quarentena

parsed = raw.withColumn("parsed", parse_avro_safe("value"))
ok  = parsed.filter("parsed IS NOT NULL")
dlq = parsed.filter("parsed IS NULL")                 # → tabela de quarentena por domínio
```

## 3. Semântica `BACKWARD` do Schema Registry é contraintuitiva

Sob compatibilidade `BACKWARD`: **remover** campo obrigatório é **seguro**;
**adicionar** campo obrigatório **sem default** é o que **quebra**.
Validar a semântica na fase de Design, não descobrir no Build.

## 4. Nomenclatura de tópico Debezium é derivada, não livre

O nome segue `{topic.prefix}.{schema}.{tabela}` — forçar um nome diferente do padrão
nativo adiciona complexidade sem benefício. Verificar convenções nativas da ferramenta
**antes** de fixar nomes "desejados" no DEFINE/Brainstorm.

## 5. Contrato ODCS como fonte única → Avro gerado

Gerar `.avsc` automaticamente a partir do contrato ODCS (tabela de mapeamento de tipos
ODCS→Avro) elimina divergência manual entre contrato e schema. Validar executando o
gerador de verdade no Build — não só o código existir.

## 6. Upserts incrementais multi-loader: `COALESCE` no UPDATE

Quando vários loaders atualizam colunas diferentes da mesma tabela, o UPDATE do upsert
deve usar `COALESCE(EXCLUDED.col, target.col)` — sem isso, uma rodada que só conhece
uma coluna **zera** as demais já populadas por outros loaders.
