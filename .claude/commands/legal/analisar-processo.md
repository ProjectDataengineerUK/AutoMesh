---
name: analisar-processo
description: Analisa dados processuais a partir do número CNJ do processo.
agent: analista-processual
---

# `/analisar-processo` — Análise Processual

Analisa dados de um processo judicial a partir do número CNJ.

## Uso
```
/analisar-processo "0010023-45.2024.8.26.0100"
/analisar-processo "1001234-56.2023.5.02.0001"
```

## Comportamento
1. Extrai metadados do número CNJ (tribunal, ano, segmento)
2. Consulta MCP DataJud + MCP Tribunal correspondente
3. Retorna: classe, assunto, vara, partes, movimentações, prazos
4. Destaca decisões recentes, sentenças e intimações
