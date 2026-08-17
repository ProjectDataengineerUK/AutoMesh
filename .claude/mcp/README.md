# MCPs Jurídicos — Model Context Protocol

Este diretório contém exemplos de configuração MCP para fontes jurídicas.
Adicione ao `opencode.json` do seu projeto:

```json
{
  "mcp": {
    "juridico-oficial": { "type": "remote", "url": "http://localhost:3001/mcp" },
    "dat jud": { "type": "remote", "url": "http://localhost:3002/mcp" },
    "legislacao-federal": { "type": "remote", "url": "http://localhost:3003/mcp" }
  }
}
```

## MCPs Disponíveis (referência)

| MCP | Função | Agentes que usam |
|-----|--------|------------------|
| `juridico-oficial` | Leis, jurisprudência, diários, citações | Pesquisador, STF, STJ, Redator |
| `dat jud` | Dados processuais (DataJud/CNJ) | Analista Processual |
| `legislacao-federal` | Leis, decretos, MPs (Planalto, LexML) | Pesquisador Legislativo |
| `tribunais-superiores` | STF, STJ, TST, TSE | STF, STJ, TST, Validador |
| `tribunais-regionais` | TJs, TRFs, TRTs | Analista, Especialistas |
| `diarios-oficiais` | DOU, DJEs, diários estaduais | Analista Processual |
| `bigquery-juridico` | Analytics, jurimetria, auditoria | Maestro, Jurimetria |
| `vertex-ai-search` | Grounded search semântica | Todos |
| `receita-federal` | CNPJ, cadastro, situação fiscal | Empresarial, Tributário |
| `software-juridico` | Projuris, Astrea, Legal One | Maestro, Analista |
