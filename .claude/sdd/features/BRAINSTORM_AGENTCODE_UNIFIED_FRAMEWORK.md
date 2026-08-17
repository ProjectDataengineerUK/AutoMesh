# BRAINSTORM: agentcode — Framework Unificado de Agentes

> Sessão exploratória para clarificar intenção e abordagem antes da captura de requisitos

## Metadata

| Atributo | Valor |
|----------|-------|
| **Feature** | AGENTCODE_UNIFIED_FRAMEWORK |
| **Data** | 2026-05-08 |
| **Autor** | brainstorm-agent |
| **Status** | Ready for Define |

---

## Ideia Inicial

**Input original:** Criar um framework unificado chamado "agentcode" que integra 5 fontes: agentspec (base), agentcodex (melhorias), data-agents (complemento), everything-claude-code (enriquecimento), mempalace (memória). O agentspec deve ser copiado integralmente com script de atualização automática.

**Contexto coletado:**
- `agentspec` v3.2.0 — 58 agentes, 30 comandos, 23 domínios KB, workflow SDD, Judge Layer, Agent Router v2. Plugin Claude Code production-ready em `C:/Users/User/ProjetosAgents/agentspec/`
- `agentcodex` — Adaptação Codex-native, maturity framework 13 blocos, project-standard.json com perfis DataOps + LLMOps. Em `C:/Users/User/ProjetosAgents/agentcodex/`
- `data-agents` v1.0.0 — 13 agentes especialistas (Databricks/Fabric), 196 skills Python, protocolo DOMA, party mode, dashboard Chainlit, MCP nativo. Em `C:/Users/User/ProjetosAgents/data-agents/`
- `everything-claude-code` v2.0.0-rc.1 — 48 agentes (especialistas em linguagens), 182 skills, AgentShield CVE scanning, token optimization, cross-harness configs (Codex, Cursor, Gemini, Kiro, OpenCode). Em `C:/Users/User/ProjetosAgents/everything-claude-code/`
- `mempalace` v3.3.4 — memória local-first ChromaDB, 96.6% R@5, 29 tools MCP, AAAK compression, knowledge graph temporal, hooks auto-save. Em `C:/Users/User/ProjetosAgents/mempalace/`
- `agentcode` — diretório alvo, atualmente vazio. Em `C:/Users/User/ProjetosAgents/agentcode/`

**Contexto técnico observado:**

| Aspecto | Observação | Implicação |
|---------|------------|------------|
| Localização core | `.claude/` (plugin Claude Code) | Mesma estrutura do agentspec |
| Distribuição | `claude plugin install agentcode` | Requer `plugin/manifest.json` + build script |
| Update agentspec | Script diff inteligente por diretório | Mapear "ownership" por pasta |
| Runtime Python | Descartado (data-agents/mempalace) | Apenas conhecimento em .md |
| Memória | Hooks condicionais + fallback nativo | Opcional: mempalace, obrigatório: .claude/memory/ |
| Cross-harness | Configs para Codex, Cursor, Gemini, Kiro, OpenCode | Pastas na raiz do repo |

---

## Perguntas de Descoberta & Respostas

| # | Pergunta | Resposta | Impacto |
|---|----------|----------|---------|
| 1 | Como o agentcode será distribuído? | **Plugin Claude Code** (`claude plugin install`) | Core plugin em `.claude/`, build script obrigatório |
| 2 | Como integrar o sistema Python do data-agents? | **Só o conhecimento** — agentes como .md, KB, protocolos | Zero dependência Python; 13 agentes viram .md; 196 skills viram KB domains |
| 3 | Como integrar o mempalace? | **Hooks + guia de configuração** — opcional se instalado | Hooks shell com detecção automática; fallback para memória nativa |
| 4 | Qual arquitetura de fusão? | **Approach A: Camadas Preservadas** — agentspec intacto + extensões em subdiretórios próprios | Update script mapeia "ownership"; nunca sobrescreve pastas de extensão |
| 5 | Cross-harness configs? | **Incluir tudo** (.codex, .cursor, .gemini, .kiro, .opencode) | Pastas na raiz; compatibilidade multi-harness nativa |
| 6 | Quantos agentes ECC de linguagem? | **Todos os 48** | Subdiretório `agents/languages/` dedicado |
| 7 | Estratégia do update script? | **Diff inteligente por diretório** — AGENTSPEC_OWNED lista explícita | Script safe: nunca toca agents/languages/, kb/databricks/, hooks extras |

---

## Inventário de Fontes (substitui Sample Data)

| Fonte | Localização | Conteúdo relevante | Como integrar |
|-------|-------------|-------------------|---------------|
| agentspec | `C:/Users/User/ProjetosAgents/agentspec/plugin/` | 58 agentes, 30 cmds, 23 KB, SDD templates, hooks, settings | Copiar integralmente para `.claude/` |
| agentcodex | `C:/Users/User/ProjetosAgents/agentcodex/.agentcodex/kb/` | 26 domínios (governance, lineage, observabilidade, acesso, contratos) | Adicionar como KB domains novos |
| agentcodex | `C:/Users/User/ProjetosAgents/agentcodex/.agentcodex/project-standard.json` | Maturity framework 13 blocos | KB domain `maturity-framework/` |
| data-agents | `C:/Users/User/ProjetosAgents/data-agents/agents/registry/` | 13 definições de agentes (.md) | `agents/data-engineering/` (novos) |
| data-agents | `C:/Users/User/ProjetosAgents/data-agents/skills/` | 196 skills (Databricks, Fabric, dbt, Spark, Quality) | KB domains `databricks/`, `fabric/` |
| data-agents | `C:/Users/User/ProjetosAgents/data-agents/agents/prompts/` | Protocolo DOMA (7 passos) | KB domain `doma-protocol/` + agente supervisor |
| data-agents | `C:/Users/User/ProjetosAgents/data-agents/commands/` | /sql, /spark, /pipeline, /party, /workflow | Commands adicionais |
| data-agents | `C:/Users/User/ProjetosAgents/data-agents/kb/constitucao.md` | Guardrails (S1-S7 segurança, cost guards) | KB domain `guardrails/` |
| ECC | `C:/Users/User/ProjetosAgents/everything-claude-code/agents/` | 48 agentes especialistas | `agents/languages/` + `agents/security/` |
| ECC | `C:/Users/User/ProjetosAgents/everything-claude-code/.claude/skills/` | 182 skills (token opt, memory persistence, continuous learning) | Skills adicionais |
| ECC | `C:/Users/User/ProjetosAgents/everything-claude-code/.claude/rules/` | Guardrails de execução | Mesclar em settings/rules |
| ECC | `C:/Users/User/ProjetosAgents/everything-claude-code/.codex/` etc. | Cross-harness configs | Pastas na raiz do repo |
| ECC | `C:/Users/User/ProjetosAgents/everything-claude-code/hooks/` | Auto-save, token management, security hooks | `.claude/hooks/` adicionais |
| mempalace | `C:/Users/User/ProjetosAgents/mempalace/hooks/` | mempal_save_hook.sh, mempal_precompact_hook.sh | `.claude/hooks/` com detecção condicional |
| mempalace | `C:/Users/User/ProjetosAgents/mempalace/docs/` | Guias de instalação e configuração | CLAUDE.md + README seção memória |

---

## Abordagens Exploradas

### Approach A: Camadas Preservadas com Namespace Separado ⭐ Selecionada

**Descrição:** agentspec é copiado integralmente para `.claude/`. Todas as extensões de outras fontes entram em subdiretórios próprios que o script de update NUNCA toca.

**Estrutura resultante:**
```
agentcode/
  .claude/
    agents/
      architect/         ← agentspec (OWNED)
      cloud/             ← agentspec (OWNED)
      data-engineering/  ← agentspec (OWNED) + novos de data-agents
      dev/               ← agentspec (OWNED)
      platform/          ← agentspec (OWNED)
      python/            ← agentspec (OWNED)
      test/              ← agentspec (OWNED)
      workflow/          ← agentspec (OWNED)
      languages/         ← NOVO: ECC 48 agentes (AGENTCODE)
      security/          ← NOVO: ECC AgentShield (AGENTCODE)
    kb/
      [23 domínios agentspec]  ← agentspec (OWNED)
      databricks/              ← NOVO: data-agents skills (AGENTCODE)
      fabric/                  ← NOVO: data-agents skills (AGENTCODE)
      doma-protocol/           ← NOVO: data-agents protocolo (AGENTCODE)
      maturity-framework/      ← NOVO: agentcodex 13 blocos (AGENTCODE)
      guardrails/              ← NOVO: data-agents constituição (AGENTCODE)
      governance/              ← NOVO: agentcodex KB (AGENTCODE)
      lineage/                 ← NOVO: agentcodex KB (AGENTCODE)
      observability/           ← NOVO: agentcodex KB (AGENTCODE)
    commands/
      [agentspec commands]     ← agentspec (OWNED)
      data/                    ← NOVO: /sql, /spark, /party, /workflow (AGENTCODE)
    skills/
      [agentspec skills]       ← agentspec (OWNED)
      [ECC skills]             ← NOVO: token-opt, memory-persist (AGENTCODE)
    hooks/
      [agentspec hooks]        ← agentspec (OWNED)
      mempalace_save.sh        ← NOVO: mempalace (AGENTCODE)
      mempalace_precompact.sh  ← NOVO: mempalace (AGENTCODE)
      agentshield.sh           ← NOVO: ECC (AGENTCODE)
    memory/                    ← fallback memória nativa
    sdd/                       ← agentspec (OWNED)
    settings.json              ← merge de agentspec + ECC rules
  plugin/                      ← build output (gerado por build-plugin.sh)
  .codex/                      ← ECC cross-harness
  .cursor/                     ← ECC cross-harness
  .gemini/                     ← ECC cross-harness
  .kiro/                       ← ECC cross-harness
  .opencode/                   ← ECC cross-harness
  scripts/
    update-agentspec.sh        ← NOVO: diff inteligente com AGENTSPEC_OWNED
    build-plugin.sh            ← copiado do agentspec
  CLAUDE.md                    ← unificado com seção mempalace
  README.md
  CHANGELOG.md

```

**Pros:**
- Update do agentspec é cirúrgico e seguro (lista AGENTSPEC_OWNED explícita)
- Delta agentcode vs agentspec é auditável a qualquer momento
- Qualquer usuário do agentspec se sente em casa imediatamente
- Sem dependências Python obrigatórias

**Cons:**
- Update script precisa de manutenção quando agentspec reorganiza pastas
- Dois "donos" de conteúdo requer disciplina

**Confirmado pelo usuário:** ✅ 2026-05-08

---

### Approach B: Fusão Plana (não selecionada)

**Por que não:** Update do agentspec vira diff complexo. Impossível separar o que é agentspec do que é agentcode após a fusão. Cada nova versão do agentspec requer revisão manual de todos os conflitos.

---

### Approach C: Git Submódulo (não selecionada)

**Por que não:** Requer que usuários entendam git submodules. Build step adicional. Complexidade para contribuir. A Approach A dá o mesmo benefício de update sem a complexidade.

---

## Abordagem Selecionada

| Atributo | Valor |
|----------|-------|
| **Escolhida** | Approach A: Camadas Preservadas |
| **Confirmação** | 2026-05-08 |
| **Motivo** | Update seguro por ownership explícito + zero dependência Python + compatibilidade nativa com agentspec |

---

## Decisões Chave

| # | Decisão | Racional | Alternativa Rejeitada |
|---|---------|----------|-----------------------|
| 1 | Plugin Claude Code (não repo clonado) | Instalação em um comando, updates automáticos | Repo local: mais fricção |
| 2 | Extrair só conhecimento do data-agents (não runtime Python) | Plugin puro, zero dependências | Runtime Python: incompatível com modelo plugin |
| 3 | mempalace como hooks opcionais | Zero dependência obrigatória, funciona sem mempalace | MCP server obrigatório: quebraria instalação simples |
| 4 | Camadas preservadas (não fusão plana) | Update seguro, delta auditável | Fusão plana: update torna-se ingerenciável |
| 5 | Incluir todos os 48 agentes ECC + cross-harness | Cobertura completa multi-linguagem e multi-harness | Selecionar subset: corte arbitrário |
| 6 | Update script com AGENTSPEC_OWNED explícito | Determinístico, sem surpresas, documentado | git merge: requer git repo + resolve conflitos |

---

## Features Removidas (YAGNI)

| Feature | Fonte | Motivo | Pode adicionar depois? |
|---------|-------|--------|------------------------|
| Runtime Python do data-agents (Chainlit, dashboard 9 páginas) | data-agents | Incompatível com modelo plugin; zero valor sem servidor rodando | Sim — como repo separado |
| Rust control plane (ecc2/) | ECC | Alpha, não relacionado ao framework de agentes | Sim — quando maduro |
| MCP server obrigatório do mempalace | mempalace | Quebraria instalação simples; hooks opcionais cobrem 90% do valor | Sim — como configuração opt-in |

---

## Validações Incrementais

| Seção | Apresentada | Feedback do usuário | Ajustado? |
|-------|-------------|--------------------|-----------| 
| Distribuição (plugin vs repo vs híbrido) | ✅ 2026-05-08 | Plugin Claude Code ✅ | Não |
| Integração data-agents (runtime vs conhecimento vs skills) | ✅ 2026-05-08 | Só o conhecimento ✅ | Não |
| Integração mempalace (hooks vs nativo vs MCP) | ✅ 2026-05-08 | Hooks + guia ✅ | Não |
| Arquitetura de fusão (A vs B vs C) | ✅ 2026-05-08 | Approach A ✅ | Não |
| YAGNI: Cross-harness + agentes ECC | ✅ 2026-05-08 | Incluir tudo ✅ | Não |
| Update script strategy | ✅ 2026-05-08 | Diff inteligente por diretório ✅ | Não |

---

## Requisitos Sugeridos para /define

### Declaração do Problema (Draft)
Desenvolvedores usando Claude Code precisam de um único framework de agentes production-ready que combine o workflow SDD do agentspec, especialistas de linguagem do ECC, conhecimento Databricks/Fabric do data-agents, maturity framework do agentcodex, e memória persistente do mempalace — instalável em um comando e atualizável sem destruir customizações.

### Usuários Alvo

| Usuário | Dor |
|---------|-----|
| Engenheiro de dados | Precisa de agentes Databricks/Fabric + workflow SDD + memória de contexto |
| Desenvolvedor Python/Go/Rust | Precisa de especialistas de linguagem + revisão de segurança |
| Arquiteto de dados | Precisa de maturity framework + data contracts + governança |
| Qualquer usuário agentspec | Quer o agentspec + extras sem aprender novo sistema |

### Critérios de Sucesso (Draft)
- [ ] `claude plugin install agentcode` funciona e ativa todos os agentes/comandos
- [ ] agentspec copiado integralmente — todos os 58 agentes, 30 comandos, 23 KB domains presentes
- [ ] `scripts/update-agentspec.sh` atualiza componentes agentspec sem sobrescrever extensões
- [ ] 13 agentes data-agents representados como .md em `agents/data-engineering/`
- [ ] KB domains novos: databricks, fabric, doma-protocol, maturity-framework, guardrails, governance, lineage, observability
- [ ] 48 agentes ECC em `agents/languages/` + `agents/security/`
- [ ] Hooks mempalace em `.claude/hooks/` com detecção condicional
- [ ] Cross-harness configs presentes: .codex, .cursor, .gemini, .kiro, .opencode
- [ ] CLAUDE.md unificado com seção de instalação do mempalace
- [ ] Plugin buildável com `scripts/build-plugin.sh`

### Constraints Identificadas
- Plugin puro: zero dependências Python obrigatórias
- Compatibilidade: agentspec v3.x deve funcionar sem modificação no core
- Update-safe: pastas AGENTCODE nunca sobrescritas pelo update script
- Tamanho: plugin deve ser instalável via `claude plugin install` (sem limite de tamanho explícito identificado)

### Fora do Escopo (Confirmado)
- Runtime Python do data-agents (Chainlit, dashboard, MCP executor)
- Rust control plane do ECC (ecc2/)
- Publicação em marketplace externo (MVP é instalação local)
- CI/CD automático para o plugin

---

## Sumário da Sessão

| Métrica | Valor |
|---------|-------|
| Perguntas feitas | 7 |
| Abordagens exploradas | 3 |
| Features removidas (YAGNI) | 3 |
| Validações completadas | 6 |
| Fontes analisadas | 5 |

---

## Próximo Passo

**Pronto para:** `/define .claude/sdd/features/BRAINSTORM_AGENTCODE_UNIFIED_FRAMEWORK.md`
