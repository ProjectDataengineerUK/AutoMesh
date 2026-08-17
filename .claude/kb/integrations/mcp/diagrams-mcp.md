# diagrams-mcp-server

Melhor opção para **arquiteto de soluções e dados** que quer gerar diagramas com ícones de cloud e recursos.
Ele usa três engines: **mingrammer/diagrams**, **Mermaid** e **PlantUML**, e é voltado para gerar diagramas de arquitetura cloud, fluxos e sequência. O pacote foi atualizado recentemente e oferece inclusive endpoint hospedado sem instalação. ([PyPI][1])

Config exemplo:
```json
{
  "servers": {
    "diagrams-mcp": {
      "type": "http",
      "url": "https://diagrams-mcp-production.up.railway.app/mcp"
    }
  }
}
```

**Por que serve bem para você:**
* Gera arquitetura com ícones de **AWS, Azure, GCP, Kubernetes, on-premises e multi-cloud**
* Bom para diagramas “as code”
* Útil para arquiteturas de dados: lakehouse, pipelines, ingestão, streaming, APIs, DW, BI, governança
* Exporta visual mais técnico e limpo do que Mermaid puro
* Baseado no ecossistema `diagrams`, que já tem muitos ícones de cloud