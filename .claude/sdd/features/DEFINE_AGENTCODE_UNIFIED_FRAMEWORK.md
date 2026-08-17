# DEFINE: agentcode — Framework Unificado de Agentes Claude

> Plugin Claude Code único que unifica agentspec, ECC, data-agents, agentcodex e mempalace em um único `claude plugin install`

## Metadata

| Atributo | Valor |
|----------|-------|
| **Feature** | AGENTCODE_UNIFIED_FRAMEWORK |
| **Data** | 2026-05-08 |
| **Autor** | define-agent |
| **Status** | Ready for Design |
| **Clarity Score** | 14/15 |
| **Brainstorm** | `BRAINSTORM_AGENTCODE_UNIFIED_FRAMEWORK.md` |

---

## Problem Statement

Desenvolvedores usando Claude Code têm acesso a 5 frameworks especializados independentes (agentspec, ECC, data-agents, agentcodex, mempalace) que individualmente resolvem problemas distintos — mas mantê-los separados gera fragmentação, conflito de versões e perda de contexto entre sessões. O **agentcode** resolve isso unificando tudo em um único plugin instalável em um comando, com update cirúrgico que nunca destrói customizações.

---

## Target Users

| Usuário | Role | Pain Point |
|---------|------|------------|
| Engenheiro de dados | Data engineer / analytics engineer | Precisa de agentes Databricks/Fabric + workflow SDD + memória de sessão, mas os frameworks ficam em repositórios separados |
| Desenvolvedor de software | Backend/fullstack developer | Precisa de especialistas de linguagem (Go, Rust, Java, Kotlin…) + revisão de segurança, mas ECC e agentspec não se falam |
| Arquiteto de dados | Data architect / tech lead | Precisa de maturity framework, data contracts, governança e lineage — espalhados entre agentcodex e data-agents |
| Usuário agentspec atual | Qualquer usuário do agentspec v3.x | Quer os extras (ECC, data-agents, mempalace) sem aprender um novo sistema e sem quebrar o workflow SDD que já usa |

---

## Goals

| Prioridade | Goal |
|------------|------|
| **MUST** | agentspec v3.x copiado integralmente — 58 agentes, 30 comandos, 23 KB domains, SDD workflow, Judge Layer, Agent Router v2 — todos funcionais |
| **MUST** | `claude plugin install agentcode` (local) funciona e ativa todo o conteúdo |
| **MUST** | `scripts/update-agentspec.sh` atualiza componentes do agentspec sem sobrescrever nenhuma extensão do agentcode |
| **MUST** | 13 agentes especialistas do data-agents representados como `.md` em `agents/data-engineering/` |
| **MUST** | KB domains novos: `databricks`, `fabric`, `doma-protocol`, `maturity-framework`, `guardrails` |
| **MUST** | 48 agentes ECC em `agents/languages/` (especialistas de linguagem) e `agents/security/` (AgentShield) |
| **MUST** | Hooks mempalace em `.claude/hooks/` com detecção condicional — funciona com ou sem mempalace instalado |
| **MUST** | Plugin buildável via `scripts/build-plugin.sh` sem erros |
| **SHOULD** | Cross-harness configs completos: `.codex/`, `.cursor/`, `.gemini/`, `.kiro/`, `.opencode/` |
| **SHOULD** | KB domains adicionais do agentcodex: `governance`, `lineage`, `observability`, `access-control` |
| **SHOULD** | Skills do ECC integradas: token optimization, memory persistence, continuous learning |
| **SHOULD** | Commands data-agents: `/party`, `/sql`, `/spark`, `/workflow`, `/pipeline` |
| **SHOULD** | `CLAUDE.md` unificado com seção de instalação do mempalace e guia de configuração |
| **COULD** | `CHANGELOG.md` rastreando cada merge do agentspec com diff auditável |
| **COULD** | Flag `--dry-run` no update script mostrando o que seria atualizado sem aplicar |

---

## Success Criteria

- [ ] `claude plugin install file://C:/Users/User/ProjetosAgents/agentcode` executa sem erro
- [ ] Contagem de agentes: ≥ 119 agentes `.md` (58 agentspec + 13 data-agents + 48 ECC)
- [ ] Contagem de KB domains: ≥ 31 domains (23 agentspec + 8 novos)
- [ ] `scripts/update-agentspec.sh` completa sem tocar `agents/languages/`, `agents/security/`, `kb/databricks/`, `kb/fabric/`, `hooks/mempalace_*.sh`
- [ ] `/brainstorm`, `/define`, `/design`, `/build`, `/ship` funcionam após instalação
- [ ] `/party`, `/sql`, `/spark` funcionam após instalação
- [ ] Com mempalace ausente: sessão termina → memória salva em `.claude/memory/` (fallback nativo)
- [ ] Com mempalace presente: sessão termina → `mempalace_save.sh` executa automaticamente
- [ ] `scripts/build-plugin.sh` gera `plugin/` com `manifest.json` válido
- [ ] Nenhuma dependência Python obrigatória para uso normal do plugin

---

## Acceptance Tests

| ID | Cenário | Given | When | Then |
|----|---------|-------|------|------|
| AT-001 | Instalação básica funciona | agentcode no disco local | `claude plugin install file://...agentcode` | Exit code 0, plugin listado em `claude plugin list` como enabled |
| AT-002 | SDD workflow intacto | Plugin instalado | Usuário executa `/brainstorm "test"` | brainstorm-agent ativa, output estruturado |
| AT-003 | Agentes agentspec preservados | Plugin instalado | Contar `.md` em `.claude/agents/{architect,cloud,platform,python,test,workflow,dev}` | ≥ 58 arquivos encontrados |
| AT-004 | Agentes ECC presentes | Plugin instalado | Contar `.md` em `.claude/agents/languages/` | 48 arquivos, incluindo `go-specialist.md`, `rust-specialist.md`, `kotlin-specialist.md` |
| AT-005 | Update seguro — extensões preservadas | `agents/languages/go-specialist.md` existe | `scripts/update-agentspec.sh` executa | `agents/languages/go-specialist.md` ainda existe, inalterado |
| AT-006 | Update seguro — agentspec atualizado | agentspec local com patch novo em `agents/architect/` | `scripts/update-agentspec.sh` executa | `agents/architect/` reflete a versão nova |
| AT-007 | Fallback memória sem mempalace | mempalace NÃO instalado no sistema | Sessão Claude Code termina (Stop hook) | Arquivo criado/atualizado em `.claude/memory/` |
| AT-008 | Hooks mempalace com mempalace | mempalace instalado (`mempalace --version` funciona) | Sessão Claude Code termina | `mempalace_save.sh` executa sem erro |
| AT-009 | KB databricks acessível | Plugin instalado | Agente data-engineering recebe tarefa Databricks SQL | KB domain `databricks/` referenciado na resposta |
| AT-010 | Build plugin completa | Repo agentcode com conteúdo completo | `bash scripts/build-plugin.sh` | `plugin/manifest.json` gerado, exit code 0 |

---

## Out of Scope

- Runtime Python do data-agents (Chainlit UI, dashboard 9 páginas, MCP executor Python)
- Rust control plane do ECC (ecc2/) — alpha, sem relação com plugin Claude Code
- Publicação em marketplace externo (npm, claude-plugins-official) — MVP é instalação local
- CI/CD automático para o plugin (GitHub Actions, etc.)
- Interface web ou dashboard para o agentcode
- Servidor MCP obrigatório do mempalace (opcional, configurado manualmente pelo usuário)

---

## Constraints

| Tipo | Constraint | Impacto |
|------|------------|---------|
| Técnico | Plugin puro — zero dependências Python obrigatórias | Toda integração de data-agents e mempalace como `.md` + hooks shell |
| Técnico | Compatibilidade agentspec v3.x — core não pode ser modificado | Extensões em subdiretórios próprios, nunca sobrescrevendo arquivos OWNED |
| Técnico | Update-safe — AGENTSPEC_OWNED explícito no script | Lista de pastas OWNED mantida manualmente quando agentspec reorganizar estrutura |
| Plataforma | Windows (PowerShell) + Linux/Mac (bash) | Hooks e scripts devem funcionar em ambos; usar `#!/usr/bin/env bash` + compatibilidade PowerShell |
| Tamanho | Plugin deve ser instalável via `claude plugin install` | Sem limite explícito identificado; monitorar se >200 agentes cria lentidão |
| Versionamento | agentspec upstream pode lançar v4.x com estrutura diferente | Script update precisa de versão mínima declarada |

---

## Technical Context

| Aspecto | Valor | Notas |
|---------|-------|-------|
| **Deployment Location** | `C:/Users/User/ProjetosAgents/agentcode/` | Instalação local via `file://` path |
| **Plugin Surface** | `.claude/` | Agents, KB, commands, skills, hooks, sdd, settings |
| **Build Output** | `plugin/` | Gerado por `build-plugin.sh` (copiado do agentspec) |
| **Scripts** | `scripts/` | `update-agentspec.sh` (novo) + `build-plugin.sh` (copiado) |
| **Cross-harness** | `.codex/`, `.cursor/`, `.gemini/`, `.kiro/`, `.opencode/` | Copiados do ECC integralmente |
| **KB Domains Relevantes** | Todos os 23 agentspec + 8 novos | dbt, spark, sql-patterns, airflow, databricks, fabric, doma-protocol, maturity-framework, guardrails, governance, lineage, observability |
| **IaC Impact** | Nenhum | Operação local de sistema de arquivos; sem infra cloud |

### Mapa de Ownership (para update script)

```
AGENTSPEC_OWNED (atualizado pelo update script):
  .claude/agents/architect/
  .claude/agents/cloud/
  .claude/agents/data-engineering/   ← parcial: só arquivos agentspec
  .claude/agents/dev/
  .claude/agents/platform/
  .claude/agents/python/
  .claude/agents/test/
  .claude/agents/workflow/
  .claude/kb/[23 domínios agentspec]
  .claude/commands/workflow/
  .claude/commands/data-engineering/
  .claude/commands/core/
  .claude/skills/[agentspec skills]
  .claude/sdd/
  scripts/build-plugin.sh

AGENTCODE_OWNED (NUNCA tocado pelo update script):
  .claude/agents/languages/          ← ECC 48 agentes
  .claude/agents/security/           ← ECC AgentShield
  .claude/kb/databricks/             ← data-agents
  .claude/kb/fabric/                 ← data-agents
  .claude/kb/doma-protocol/          ← data-agents
  .claude/kb/maturity-framework/     ← agentcodex
  .claude/kb/guardrails/             ← data-agents constituição
  .claude/kb/governance/             ← agentcodex
  .claude/kb/lineage/                ← agentcodex
  .claude/kb/observability/          ← agentcodex
  .claude/commands/data/             ← data-agents commands
  .claude/skills/[ECC skills]        ← ECC skills
  .claude/hooks/mempalace_save.sh    ← mempalace
  .claude/hooks/mempalace_precompact.sh ← mempalace
  .claude/hooks/agentshield.sh       ← ECC
  .codex/ .cursor/ .gemini/ .kiro/ .opencode/  ← ECC cross-harness
  scripts/update-agentspec.sh        ← agentcode original
  CLAUDE.md                          ← agentcode version
  README.md
  CHANGELOG.md
```

---

## Assumptions

| ID | Assumption | Se errada, impacto | Validado? |
|----|------------|-------------------|-----------|
| A-001 | `agentspec/plugin/` tem estrutura estável copiável (não gera via build runtime) | Build script copiaria artefatos gerados em vez de source | [ ] Verificar antes do Design |
| A-002 | `claude plugin install file://PATH` funciona sem registry externo | MVP precisaria de outro mecanismo de distribuição | [ ] Testar antes do Build |
| A-003 | Hooks `.sh` executam no Windows via Git Bash / WSL (não só PowerShell) | Hooks mempalace precisariam de versão `.ps1` paralela | [ ] Verificar ambiente do usuário |
| A-004 | Nenhum limite de tamanho de plugin impede 119+ arquivos `.md` | Seria necessário split do plugin em módulos | [ ] Verificar durante Build |
| A-005 | Todos os 5 diretórios fonte permanecem em `C:/Users/User/ProjetosAgents/` durante o build | Script de merge falharia com path not found | [x] Confirmado — paths verificados na exploração |
| A-006 | ECC agents são arquivos `.md` independentes que funcionam como agentes Claude Code nativos | Precisariam de adaptação de formato | [ ] Verificar formato durante Design |

---

## Clarity Score Breakdown

| Elemento | Score (0-3) | Notas |
|----------|-------------|-------|
| Problema | **3** | Específico: 5 ferramentas → 1 install. Impacto claro: fragmentação, conflito, perda de contexto |
| Usuários | **3** | 4 personas com roles e pain points distintos e concretos |
| Goals | **2** | MUST/SHOULD/COULD estruturados; goals de contagem específicos (58, 48, 23 KB) — -1 por não ter SLA de performance |
| Sucesso | **3** | 10 acceptance tests testáveis, todos com Given/When/Then concretos |
| Escopo | **3** | Fora-de-escopo explícito (6 itens), constraints detalhadas, mapa de ownership |
| **Total** | **14/15** | Acima do mínimo 12/15 — Ready for Design |

---

## Open Questions

1. **A-001:** A pasta `agentspec/plugin/` contém source diretamente ou é output de build? Se for output, o Build phase precisará rodar o build do agentspec antes de copiar. → Verificar antes do Design.
2. **A-003:** O ambiente Windows do usuário tem Git Bash ou WSL disponível para executar hooks `.sh`? Se não, hooks mempalace precisam de versão PowerShell (`.ps1`). → Verificar antes do Build.
3. **Versão mínima agentspec:** O script `update-agentspec.sh` deve declarar uma versão mínima suportada (ex: `AGENTSPEC_MIN_VERSION="3.2.0"`) para evitar aplicar updates de v4.x com estrutura incompatível?

---

## Revision History

| Versão | Data | Autor | Mudanças |
|--------|------|-------|---------|
| 1.0 | 2026-05-08 | define-agent | Versão inicial a partir de BRAINSTORM validado |

---

## Next Step

**Pronto para:** `/design .claude/sdd/features/DEFINE_AGENTCODE_UNIFIED_FRAMEWORK.md`
