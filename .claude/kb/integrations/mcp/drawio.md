# Draw.io MCP / diagrams.net MCP

Use quando você quiser gerar e depois **editar manualmente** no draw.io.
O Draw.io MCP permite criar, editar e abrir diagramas via MCP, com suporte a XML, CSV e Mermaid; há opção hospedada em `https://mcp.draw.io/mcp` e CLI local via `npx @drawio/mcp`. ([A2A MCP][2])

Config provável:
```json
{
  "servers": {
    "drawio": {
      "command": "npx",
      "args": ["@drawio/mcp"]
    }
  }
}
```

**Quando eu escolheria este:**
* Você precisa entregar para comitê, cliente ou governança
* Quer layout mais bonito e editável
* Precisa de múltiplas páginas: visão executiva, visão técnica, segurança, dados, integrações
* Quer manter o arquivo `.drawio` como artefato oficial