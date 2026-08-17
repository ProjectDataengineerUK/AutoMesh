# Cortex Analyst Patterns

## Semantic Model YAML — Estrutura Completa

```yaml
name: financeiro
description: "Métricas financeiras: receita, margem, canais de venda"
tables:
  - name: fact_sales
    description: "Fatos de vendas diárias"
    base_table: analytics.gold.fact_sales
    primary_key: sale_id
    time_dimensions:
      - name: sale_date
        description: "Data da venda"
        column: sale_date
    dimensions:
      - name: region
        description: "Região geográfica"
        column: region_code
        synonyms: ["área", "zona", "localidade"]
      - name: channel
        description: "Canal de venda: loja, online, parceiro"
        column: channel
    measures:
      - name: total_revenue
        description: "Receita total em BRL"
        column: revenue
        agg: SUM
        synonyms: ["faturamento", "receita bruta"]
      - name: order_count
        description: "Número de pedidos"
        column: order_id
        agg: COUNT_DISTINCT

  - name: dim_customer
    description: "Dimensão de clientes"
    base_table: analytics.gold.dim_customer
    relationships:
      - join_to: fact_sales
        join_on: "fact_sales.customer_id = dim_customer.customer_id"
        join_type: LEFT
    dimensions:
      - name: segment
        description: "Segmento: varejo, corporativo, SMB"
        column: customer_segment
```

## Python API com Trust Score

```python
import snowflake.connector
from snowflake.cortex import CortexAnalystService

conn = snowflake.connector.connect(**connection_params)
analyst = CortexAnalystService(conn)

def query_financeiro(question: str) -> dict:
    result = analyst.query(
        question=question,
        semantic_model_file="@analytics.cortex.semantic_models/financeiro.yaml"
    )

    if result["trust_score"] < 0.7:
        return {"error": f"Low confidence ({result['trust_score']:.2f}). Rephrase the question."}

    return {
        "sql": result["sql"],
        "data": result["data"],
        "trust_score": result["trust_score"]
    }
```

## Trust Score Thresholds

| Score     | Ação                                    |
|-----------|-----------------------------------------|
| ≥ 0.90    | Apresentar resultado direto             |
| 0.70–0.89 | Apresentar com aviso de confiança média |
| 0.50–0.69 | Pedir refinamento da pergunta           |
| < 0.50    | Escalar para @snowflake-sql-expert      |

## Boas Práticas para Semantic Models

- `synonyms` reduzem ambiguidade — adicionar termos do negócio local (PT-BR)
- `description` em cada campo → Analyst usa como contexto para NL→SQL
- Uma tabela fato + N dimensões por semantic model — evitar modelos > 10 tabelas
- Campos de data → sempre declarar como `time_dimensions` (não `dimensions`)
- Métricas derivadas → declarar como `measures` com fórmula, não computar em SQL

## Limitações

- Cortex Analyst não suporta subqueries arbitrárias — usar semantic model bem modelado
- Janelas de tempo relativas ("mês passado") dependem de `time_dimensions` configurado
- Joins complexos > 2 tabelas → considerar view materializada como base
