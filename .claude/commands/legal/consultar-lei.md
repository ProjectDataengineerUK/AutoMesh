---
name: consultar-lei
description: Consulta legislação federal vigente por tema, número, artigo ou palavra-chave.
agent: pesquisador-legislativo
model: opencode/nemotron-3-super-free
---

# `/consultar-lei` — Pesquisa Legislativa

Consulta a legislação federal brasileira.

## Uso
```
/consultar-lei "artigo tal do CPC sobre prazos"
/consultar-lei "Lei 13.709/2018 art. 5º"
/consultar-lei "requisitos da reconvenção CPC"
/consultar-lei "alterações da reforma trabalhista na CLT"
```

## Comportamento
1. Identifica o tema ou dispositivo legal
2. Consulta a KB Legislação Federal + MCP Legislação
3. Retorna o texto legal, fundamento e informações de vigência
4. Inclui alterações recentes e revogações se houver
