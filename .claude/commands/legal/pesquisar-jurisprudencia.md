---
name: pesquisar-jurisprudencia
description: Pesquisa jurisprudência por tribunal (STF, STJ, TST, TJ, TRF) e tema.
agent: maestro
---

# `/pesquisar-jurisprudencia` — Pesquisa de Jurisprudência

Pesquisa jurisprudência nos tribunais superiores e regionais.

## Uso
```
/pesquisar-jurisprudencia "STJ responsabilidade civil contratual"
/pesquisar-jurisprudencia "STF repercussão geral ICMS na base do PIS"
/pesquisar-jurisprudencia "TST horas in itinere após reforma"
/pesquisar-jurisprudencia "TJSP indenização por dano moral"
```

## Comportamento
1. Identifica tribunal e tema
2. Invoca o agente especialista do tribunal correspondente
3. Consulta MCP + KB Jurisprudência
4. Retorna ementas, teses e súmulas relevantes com fonte
