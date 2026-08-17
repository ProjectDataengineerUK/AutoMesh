# MCP Integration for Diagram Generation

This domain provides guidance on using Model Context Protocol (MCP) servers for diagram generation within the agentcode framework.

## Available Diagram MCP Servers

- [diagrams-mcp-server](diagrams-mcp.md) - Generate cloud architecture diagrams with official AWS/Azure/GCP icons using mingrammer/diagrams, Mermaid, and PlantUML engines
- [drawio](drawio.md) - Create and edit diagrams visually via draw.io interface with XML/CSV/Mermaid support
- [mcp-diagrams](mcp-diagrams.md) - Alternative for infrastructure and architecture diagrams via MCP with simple commands (refer to external documentation)

## Escolha Prática
Para o seu perfil de arquiteto de soluções e dados:
**Geração técnica inicial:** `diagrams-mcp-server`
**Refino visual / entrega final:** `Draw.io MCP`
**Diagramas rápidos em documentação Markdown:** Mermaid via MCP ou diretamente no editor

## Prompt Exemplo
Consulte os arquivos específicos de cada MCP server para exemplos de uso e prompts detalhados.

[1]: https://pypi.org/project/diagrams-mcp-server/?utm_source=chatgpt.com "diagrams-mcp-server · PyPI"
[2]: https://a2a-mcp.org/entry/drawio-mcp?utm_source=chatgpt.com "Draw.io MCP - Official MCP Server for AI-Powered Diagrams in draw.io"
[3]: https://pypi.org/project/mcp-diagrams/?utm_source=chatgpt.com "mcp-diagrams · PyPI"