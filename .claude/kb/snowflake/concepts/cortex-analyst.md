# Cortex Analyst — NL→SQL sobre Dados Estruturados

> **Propósito:** Responder perguntas de negócio em linguagem natural convertendo para SQL
> sobre dados Snowflake, sem que o usuário precise conhecer SQL.

---

## Como Funciona

```
Pergunta natural → Cortex Analyst → Semantic Model YAML → SQL gerado → Execução → Resultado
```

O **Semantic Model** é o coração do Cortex Analyst: um arquivo YAML que descreve tabelas,
colunas, métricas, dimensões e relacionamentos em linguagem de negócio.

---

## Semantic Model YAML — Estrutura

```yaml
# semantic_model_financeiro.yaml
name: financeiro
description: "Modelo semântico do domínio financeiro — receita, custos e margem"

tables:
  - name: fact_receita
    base_table:
      database: ANALYTICS
      schema: GOLD
      table: FACT_RECEITA
    description: "Fatos de receita por transação"
    
    time_dimensions:
      - name: data_transacao
        expr: DATA_TRANSACAO
        description: "Data da transação"
        unique: false
        data_type: date
    
    dimensions:
      - name: regiao
        expr: REGIAO
        description: "Região geográfica da transação"
        data_type: text
        sample_values: ["Sul", "Sudeste", "Norte", "Nordeste", "Centro-Oeste"]
      
      - name: canal_venda
        expr: CANAL_VENDA
        description: "Canal de venda utilizado"
        data_type: text
        sample_values: ["E-commerce", "Loja Física", "Parceiros"]
    
    measures:
      - name: receita_bruta
        expr: VALOR_BRUTO
        description: "Receita bruta da transação em BRL"
        data_type: number
        default_aggregation: sum
      
      - name: receita_liquida
        expr: VALOR_LIQUIDO
        description: "Receita líquida após descontos e devoluções"
        data_type: number
        default_aggregation: sum
      
      - name: numero_transacoes
        expr: COUNT(DISTINCT ID_TRANSACAO)
        description: "Número de transações únicas"
        data_type: number
        default_aggregation: count

  - name: dim_produto
    base_table:
      database: ANALYTICS
      schema: GOLD
      table: DIM_PRODUTO
    description: "Dimensão de produtos"
    
    dimensions:
      - name: categoria
        expr: CATEGORIA
        description: "Categoria do produto"
        data_type: text
      - name: subcategoria
        expr: SUBCATEGORIA
        description: "Subcategoria do produto"
        data_type: text

relationships:
  - left_table: fact_receita
    right_table: dim_produto
    join_type: left_outer
    relationship_type: many_to_one
    left_columns: ["ID_PRODUTO"]
    right_columns: ["ID_PRODUTO"]

verified_queries:
  - name: receita_por_regiao_q1
    question: "Qual foi a receita bruta por região no primeiro trimestre?"
    sql: |
      SELECT regiao, SUM(valor_bruto) AS receita_bruta
      FROM analytics.gold.fact_receita
      WHERE data_transacao BETWEEN '2026-01-01' AND '2026-03-31'
      GROUP BY regiao
      ORDER BY receita_bruta DESC
```

---

## Usando via API

```python
import snowflake.connector
import json

def ask_cortex_analyst(question: str, semantic_model_path: str, conn) -> dict:
    """
    Pergunta ao Cortex Analyst e retorna SQL + resultado.
    Validar Trust Score antes de apresentar ao usuário.
    """
    response = conn.cursor().execute(
        """
        SELECT SNOWFLAKE.CORTEX.ANALYST(
            ?,
            TO_VARIANT(PARSE_JSON(?))
        )
        """,
        [question, json.dumps({"semantic_model_file": semantic_model_path})]
    ).fetchone()[0]
    
    result = json.loads(response)
    
    # SEMPRE validar Trust Score
    trust_score = result.get("trust_score", 0)
    if trust_score < 0.7:
        raise ValueError(f"Trust Score baixo ({trust_score:.2f}) — resposta não confiável. Refine o Semantic Model.")
    
    return {
        "question": question,
        "sql": result["sql"],
        "trust_score": trust_score,
        "interpretation": result.get("interpretation", "")
    }
```

---

## Trust Score — Interpretação

| Score | Significado | Ação do Agente |
|-------|-------------|----------------|
| ≥ 0.90 | Alta confiança — SQL preciso | Apresentar diretamente |
| 0.70–0.89 | Confiança média — SQL provável | Mostrar SQL ao usuário para revisão |
| 0.50–0.69 | Baixa confiança — ambiguidade | Pedir clarificação ou refinamento |
| < 0.50 | Falha na interpretação | Não apresentar — escalar para `@snowflake-sql-expert` |

---

## Boas Práticas

1. **Verified Queries** no YAML — exemplos pré-aprovados melhoram accuracy em ~30%
2. **Sample Values** em dimensões — ajudam o modelo a mapear termos de negócio
3. **Descriptions claras** — em inglês ou português consistente, sem abreviações
4. **Uma pergunta por vez** — Cortex Analyst não suporta multi-intent em uma query
5. **Fallback SQL** — se Trust Score < 0.7, passar para `@snowflake-sql-expert`

---

## Limitações

- Não suporta queries sobre múltiplas bases de dados em uma só pergunta
- Não executa DML (INSERT, UPDATE) — somente SELECT
- Máximo de ~50 tabelas no Semantic Model (performance degrada acima)
- Perguntas com negação complexa ("vendas fora do Q1 exceto...") têm Trust Score baixo
