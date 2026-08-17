# DESIGN: agentcode — Framework Unificado de Agentes Claude

> Especificação técnica para construir o agentcode como plugin Claude Code que funde agentspec + ECC + data-agents + agentcodex + mempalace

## Metadata

| Atributo | Valor |
|----------|-------|
| **Feature** | AGENTCODE_UNIFIED_FRAMEWORK |
| **Data** | 2026-05-08 |
| **Autor** | design-agent |
| **DEFINE** | [DEFINE_AGENTCODE_UNIFIED_FRAMEWORK.md](./DEFINE_AGENTCODE_UNIFIED_FRAMEWORK.md) |
| **Status** | Ready for Build |

---

## Architecture Overview

```
FONTES (read-only)                          AGENTCODE (target)
═══════════════════════════════════════     ══════════════════════════════════════════
                                            agentcode/
agentspec/plugin/                            ├── .claude/
  agents/ (58 .md, 8 subdirs)  ──COPY──→   │   ├── agents/
  kb/ (25 domains)             ──COPY──→   │   │   ├── architect/    (OWNED: 8)
  commands/ (33 .md, 6 subdirs)──COPY──→   │   │   ├── cloud/        (OWNED: 10)
  skills/ (5 skills)           ──COPY──→   │   │   ├── data-engineering/ (OWNED:15
  sdd/ (templates+arch)        ──COPY──→   │   │   ├── dev/          (OWNED: 4)
  hooks/hooks.json             ──BASE──→   │   │   ├── platform/     (OWNED: 6)
                                            │   │   ├── python/       (OWNED: 6)
ECC/agents/ (48 .md)           ──COPY──→   │   │   ├── test/         (OWNED: 3)
ECC/.codex/ (5 files)          ──COPY──→   │   │   ├── workflow/     (OWNED: 6)
ECC/.cursor/ (61 files)        ──COPY──→   │   │   ├── languages/    (AGENTCODE:46)
ECC/.claude/rules/ (2 .md)     ──MERGE─→   │   │   └── security/     (AGENTCODE: 2)
                                            │   │
data-agents/kb/databricks/ (9) ──COPY──→   │   ├── kb/
data-agents/kb/fabric/ (9)     ──COPY──→   │   │   ├── [25 agentspec domains] (OWNED)
data-agents/kb/governance/(11) ──COPY──→   │   │   ├── databricks/   (AGENTCODE)
data-agents/kb/pipeline-design/──COPY──→   │   │   ├── fabric/       (AGENTCODE)
data-agents/kb/semantic-modeling──COPY──→  │   │   ├── governance/   (AGENTCODE)
data-agents/kb/migration/      ──COPY──→   │   │   ├── doma-protocol/ (AGENTCODE)
data-agents/kb/constitution.md ──ADAPT─→   │   │   ├── semantic-modeling/ (AGENTCODE)
data-agents/agents/registry/   ──ADAPT─→   │   │   ├── migration/    (AGENTCODE)
  (12 .md agent definitions)               │   │   ├── guardrails/   (AGENTCODE)
                                            │   │   ├── controls/     (AGENTCODE)
agentcodex/.agentcodex/kb/                 │   │   ├── foundations/  (AGENTCODE)
  controls/ foundations/       ──COPY──→   │   │   ├── integrations/ (AGENTCODE)
  integrations/ metadata/      ──COPY──→   │   │   ├── metadata/     (AGENTCODE)
  operations/ orchestration/   ──COPY──→   │   │   ├── operations/   (AGENTCODE)
  patterns/ platforms/         ──COPY──→   │   │   ├── orchestration/(AGENTCODE)
                                            │   │   ├── patterns/     (AGENTCODE)
mempalace/hooks/                           │   │   └── platforms/    (AGENTCODE)
  mempal_save_hook.sh          ──COPY──→   │   │
  mempal_precompact_hook.sh    ──COPY──→   │   ├── commands/
                                            │   │   ├── [6 agentspec subdirs] (OWNED)
                                            │   │   └── data/         (AGENTCODE: 5)
                                            │   │
                                            │   ├── skills/ (agentspec OWNED)
                                            │   ├── sdd/    (agentspec OWNED)
                                            │   └── hooks/
                                            │       ├── hooks.json    (MERGED)
                                            │       ├── mempalace_save.sh
                                            │       └── mempalace_precompact.sh
                                            │
                                            ├── .codex/   (ECC, AGENTCODE)
                                            ├── .cursor/  (ECC, AGENTCODE)
                                            ├── scripts/
                                            │   ├── update-agentspec.sh  (NEW)
                                            │   └── build-plugin.sh      (agentspec)
                                            ├── CLAUDE.md
                                            ├── README.md
                                            └── CHANGELOG.md
```

---

## Components

| Componente | Propósito | Origem | Tipo de operação |
|------------|-----------|--------|-----------------|
| `.claude/agents/` (OWNED) | 58 agentes workflow/data/cloud/arch | agentspec | Cópia direta |
| `.claude/agents/languages/` | 46 agentes ECC (linguagens + gerais) | ECC | Cópia direta |
| `.claude/agents/security/` | 2 agentes ECC (segurança) | ECC | Cópia direta |
| `.claude/agents/data-engineering/` (extensão) | Agentes Databricks/Fabric especializados | data-agents | Adaptação de formato |
| `.claude/kb/` (OWNED, 25) | Conhecimento: dbt, spark, sql, airflow… | agentspec | Cópia direta |
| `.claude/kb/` (AGENTCODE, 9+) | Databricks, Fabric, DOMA, governance… | data-agents + agentcodex | Cópia + extração |
| `.claude/commands/data/` | /sql, /spark, /party, /workflow, /pipeline | data-agents (adaptado) | Criação de .md |
| `.claude/hooks/hooks.json` | Registro de hooks de sessão | agentspec + mempalace | Merge |
| `.claude/hooks/*.sh` | Scripts auto-save/pre-compact | mempalace | Cópia direta |
| `.codex/` | Configuração Codex-native | ECC | Cópia direta |
| `.cursor/` | Regras, hooks, skills para Cursor | ECC | Cópia direta |
| `scripts/update-agentspec.sh` | Atualização cirúrgica do core agentspec | (novo) | Criação |
| `scripts/build-plugin.sh` | Build do plugin para distribuição | agentspec | Cópia |

---

## Key Decisions

### Decision 1: Namespace por ownership (OWNED vs AGENTCODE)

| Atributo | Valor |
|----------|-------|
| **Status** | Accepted |
| **Data** | 2026-05-08 |

**Contexto:** O agentspec será atualizado ao longo do tempo. O update script precisa saber exatamente quais arquivos substituir sem risco de apagar extensões do agentcode.

**Escolha:** Toda pasta adicionada pelo agentcode (não existente no agentspec) tem ownership `AGENTCODE`. O script `update-agentspec.sh` mantém uma lista `AGENTSPEC_OWNED` explícita e nunca toca em qualquer path fora dela.

**Rationale:** Lista explícita é determinística e auditável. Git diff entre agentspec e agentcode é legível. Qualquer eng. pode auditar o delta.

**Alternativas rejeitadas:**
1. `git merge` — requer repo + resolve conflitos manuais
2. Ownership inferido por convenção de nome — frágil, quebra quando agentspec renomeia

**Consequências:**
- Lista `AGENTSPEC_OWNED` precisa de manutenção manual se agentspec reorganizar estrutura
- Delta agentcode vs agentspec é auditável a qualquer momento com `diff -r`

---

### Decision 2: data-agents commands Python → .md Claude Code

| Atributo | Valor |
|----------|-------|
| **Status** | Accepted |
| **Data** | 2026-05-08 |

**Contexto:** Os commands do data-agents são módulos Python (`.py`) que executam lógica de orquestração. O agentcode é um plugin puro (zero Python obrigatório).

**Escolha:** Criar 5 novos arquivos `.md` em `.claude/commands/data/` que reimplementam a intenção dos commands Python como instruções Claude Code nativas, referenciando os KB domains recém-adicionados (databricks, fabric, doma-protocol).

**Rationale:** `.md` commands são a única forma suportada pelo Claude Code plugin. A lógica de negócio vai para os KB domains; o command `.md` apenas orienta o agente.

**Alternativas rejeitadas:**
1. Incluir os `.py` no repo e invocar via Bash — quebraria instalação sem Python; viola constraint "zero dependência"
2. Pular os commands — perderia `/party`, `/workflow`, `/sql` que têm alto valor

**Consequências:**
- Comportamento dos commands é mais simples que a implementação Python original (sem estado, sem sessões)
- `/party` perde o "múltiplos agentes em paralelo" literal, mas ganha o mesmo efeito via agent delegation do Claude Code

---

### Decision 3: ECC agents — split languages/ vs security/ (sem subdir ecc/)

| Atributo | Valor |
|----------|-------|
| **Status** | Accepted |
| **Data** | 2026-05-08 |

**Contexto:** ECC tem 48 agentes. Alguns são especialistas de linguagem, outros são gerais (architect, planner, chief-of-staff). Colocar tudo em `agents/ecc/` cria uma categoria sem semântica clara.

**Escolha:** Todos os 48 ECC agents vão em 2 dirs AGENTCODE: `agents/languages/` (46 agentes) e `agents/security/` (security-reviewer, healthcare-reviewer). Agentes ECC que "soam gerais" (architect, planner) ficam em `languages/` porque são AGENTCODE-owned e não conflitam com os de mesmo nome no agentspec (diferentes arquivos, diferentes dirs).

**Rationale:** O Claude Code resolve agentes por nome do arquivo. Arquivos em `agents/languages/ecc-architect.md` e `agents/architect/the-planner.md` são nomes distintos — sem colisão.

**Alternativas rejeitadas:**
1. `agents/ecc/` separado — mais claro de onde veio, mas semanticamente vazio para o usuário
2. Mesclar em dirs OWNED (architect/, dev/) — quebraria ownership e update seguro

**Consequências:**
- Usuário pode ter `architect` do agentspec e `architect` do ECC ambos disponíveis
- Prefixar ECC agents com `ecc-` no filename elimina qualquer ambiguidade residual

---

### Decision 4: hooks.json — merge com seção condicional para mempalace

| Atributo | Valor |
|----------|-------|
| **Status** | Accepted |
| **Data** | 2026-05-08 |

**Contexto:** agentspec tem `hooks.json` próprio. mempalace precisa registrar hooks `Stop` e `PreCompact`. Não podemos simplesmente sobrescrever o hooks.json do agentspec.

**Escolha:** O build cria um `hooks.json` mesclado que contém: (a) todos os hooks do agentspec como base, (b) entradas para `mempalace_save.sh` e `mempalace_precompact.sh` com guard `command -v mempalace`. O `update-agentspec.sh` re-executa o merge ao atualizar.

**Rationale:** hooks.json é um arquivo de configuração, não código — merge é a abordagem correta. O guard shell garante que o hook falha silenciosamente se mempalace não está instalado.

**Alternativas rejeitadas:**
1. Dois hooks.json separados — Claude Code não suporta múltiplos hooks.json no mesmo diretório
2. Mempalace hooks como hooks.json independente em subdir — não é como o Claude Code resolve hooks

**Consequências:**
- O update script precisa re-aplicar o merge ao atualizar (não pode simplesmente copiar o hooks.json do agentspec)
- O guard `command -v mempalace` exige que o script funcione tanto em bash quanto em PowerShell

---

### Decision 5: agentcodex KB — copiar só os domínios únicos

| Atributo | Valor |
|----------|-------|
| **Status** | Accepted |
| **Data** | 2026-05-08 |

**Contexto:** agentcodex tem 25 KB domains, dos quais ~17 se sobrepõem com agentspec (dbt, spark, sql-patterns, airflow…). Sobrescrever agentspec KB com versões agentcodex pode degradar qualidade — o agentspec é mais curado.

**Escolha:** Copiar apenas os 8 domínios exclusivos do agentcodex não presentes no agentspec: `controls`, `foundations`, `integrations`, `metadata`, `operations`, `orchestration`, `patterns`, `platforms`. Pular `update-candidates` (conteúdo de trabalho em progresso).

**Rationale:** Preserva a qualidade do agentspec KB. Os domínios únicos do agentcodex adicionam cobertura de governança e maturity sem conflito.

**Alternativas rejeitadas:**
1. Copiar tudo e sobrescrever — degradaria KB agentspec com versões menos curadas
2. Fazer merge conteúdo por conteúdo — escopo infinito, frágil

---

## File Manifest

> Agrupado por operação. `(bulk)` = múltiplos arquivos copiados como-é. `(adapt)` = requer transformação. `(new)` = criado do zero.

### Grupo 1 — agentspec core (OWNED) — cópia direta

| # | Origem | Destino | Ação | Qtd arquivos |
|---|--------|---------|------|--------------|
| G1-01 | `agentspec/plugin/agents/architect/` | `.claude/agents/architect/` | Cópia bulk | 8 .md |
| G1-02 | `agentspec/plugin/agents/cloud/` | `.claude/agents/cloud/` | Cópia bulk | 10 .md |
| G1-03 | `agentspec/plugin/agents/data-engineering/` | `.claude/agents/data-engineering/` | Cópia bulk | 15 .md |
| G1-04 | `agentspec/plugin/agents/dev/` | `.claude/agents/dev/` | Cópia bulk | 4 .md |
| G1-05 | `agentspec/plugin/agents/platform/` | `.claude/agents/platform/` | Cópia bulk | 6 .md |
| G1-06 | `agentspec/plugin/agents/python/` | `.claude/agents/python/` | Cópia bulk | 6 .md |
| G1-07 | `agentspec/plugin/agents/test/` | `.claude/agents/test/` | Cópia bulk | 3 .md |
| G1-08 | `agentspec/plugin/agents/workflow/` | `.claude/agents/workflow/` | Cópia bulk | 6 .md |
| G1-09 | `agentspec/plugin/kb/` (25 domains) | `.claude/kb/` | Cópia bulk | ~200+ .md |
| G1-10 | `agentspec/plugin/commands/` (6 subdirs) | `.claude/commands/` | Cópia bulk | 33 .md |
| G1-11 | `agentspec/plugin/skills/` (5 skills) | `.claude/skills/` | Cópia bulk | 5 dirs |
| G1-12 | `agentspec/plugin/sdd/` | `.claude/sdd/` | Cópia bulk | ~10 files |
| G1-13 | `agentspec/plugin/hooks/hooks.json` | `.claude/hooks/hooks-agentspec-base.json` | Cópia (base para merge) | 1 |
| G1-14 | `agentspec/build-plugin.sh` | `scripts/build-plugin.sh` | Cópia | 1 |

**Total Grupo 1: ~290 arquivos**

---

### Grupo 2 — ECC agents (AGENTCODE) — cópia direta com prefixo

| # | Origem | Destino | Ação | Qtd |
|---|--------|---------|------|-----|
| G2-01 | `ECC/agents/security-reviewer.md` | `.claude/agents/security/ecc-security-reviewer.md` | Cópia | 1 |
| G2-02 | `ECC/agents/healthcare-reviewer.md` | `.claude/agents/security/ecc-healthcare-reviewer.md` | Cópia | 1 |
| G2-03 | `ECC/agents/*.md` (46 restantes) | `.claude/agents/languages/ecc-{name}.md` | Cópia bulk com prefixo `ecc-` | 46 |

**Total Grupo 2: 48 arquivos**

---

### Grupo 3 — ECC cross-harness (AGENTCODE) — cópia direta

| # | Origem | Destino | Ação | Qtd |
|---|--------|---------|------|-----|
| G3-01 | `ECC/.codex/` (5 files) | `.codex/` | Cópia bulk | 5 |
| G3-02 | `ECC/.cursor/` (61 files) | `.cursor/` | Cópia bulk | 61 |

**Total Grupo 3: 66 arquivos**

---

### Grupo 4 — data-agents KB (AGENTCODE) — cópia seletiva

| # | Origem | Destino | Ação | Qtd |
|---|--------|---------|------|-----|
| G4-01 | `data-agents/kb/databricks/` (9 .md) | `.claude/kb/databricks/` | Cópia bulk | 9 |
| G4-02 | `data-agents/kb/fabric/` (9 .md) | `.claude/kb/fabric/` | Cópia bulk | 9 |
| G4-03 | `data-agents/kb/governance/` (11 .md) | `.claude/kb/governance/` | Cópia bulk | 11 |
| G4-04 | `data-agents/kb/pipeline-design/` (9 .md) | `.claude/kb/doma-protocol/` | Cópia bulk | 9 |
| G4-05 | `data-agents/kb/semantic-modeling/` (9 .md) | `.claude/kb/semantic-modeling/` | Cópia bulk | 9 |
| G4-06 | `data-agents/kb/migration/` | `.claude/kb/migration/` | Cópia bulk | ~5 |
| G4-07 | `data-agents/kb/constitution.md` | `.claude/kb/guardrails/constitution.md` | Cópia | 1 |

**Pulados (sobreposição com agentspec):** `data-agents/kb/data-quality/`, `data-agents/kb/sql-patterns/`, `data-agents/kb/spark-patterns/`, `data-agents/kb/python-patterns/`, `data-agents/kb/shared/`

**Total Grupo 4: ~53 arquivos**

---

### Grupo 5 — data-agents agents (AGENTCODE) — adaptação de formato

| # | Arquivo de saída | Origem | Ação |
|---|-----------------|--------|------|
| G5-01 | `.claude/agents/data-engineering/databricks-sql-expert.md` | `data-agents/agents/registry/sql-expert.md` | Adapt agentspec frontmatter |
| G5-02 | `.claude/agents/data-engineering/fabric-pipeline-expert.md` | `data-agents/agents/registry/pipeline-architect.md` | Adapt |
| G5-03 | `.claude/agents/data-engineering/doma-supervisor.md` | `data-agents/agents/registry/*.md` + DOMA protocol | Adapt + sintetizar |
| G5-04 | `.claude/agents/data-engineering/databricks-spark-expert.md` | `data-agents/agents/registry/spark-expert.md` | Adapt |
| G5-05 | `.claude/agents/data-engineering/dbt-fabric-expert.md` | `data-agents/agents/registry/dbt-expert.md` | Adapt |
| G5-06 | `.claude/agents/data-engineering/semantic-modeler.md` | `data-agents/agents/registry/semantic-modeler.md` | Adapt |
| G5-07 | `.claude/agents/data-engineering/data-governance-auditor.md` | `data-agents/agents/registry/governance-auditor.md` | Adapt |
| G5-08 | `.claude/agents/data-engineering/data-migration-expert.md` | `data-agents/agents/registry/migration-expert.md` | Adapt |

**Nota:** Agentes data-agents que já têm equivalente no agentspec OWNED são pulados: `data-quality-steward` (agentspec tem `data-quality-analyst`), `python-expert` (agentspec tem `python-developer`), `business-analyst` (não tem equivalente — adicionar como G5-09).

**Total Grupo 5: 9 arquivos**

---

### Grupo 6 — agentcodex KB únicos (AGENTCODE) — cópia direta

| # | Origem | Destino | Ação |
|---|--------|---------|------|
| G6-01 | `agentcodex/.agentcodex/kb/controls/` | `.claude/kb/controls/` | Cópia bulk |
| G6-02 | `agentcodex/.agentcodex/kb/foundations/` | `.claude/kb/foundations/` | Cópia bulk |
| G6-03 | `agentcodex/.agentcodex/kb/integrations/` | `.claude/kb/integrations/` | Cópia bulk |
| G6-04 | `agentcodex/.agentcodex/kb/metadata/` | `.claude/kb/metadata/` | Cópia bulk |
| G6-05 | `agentcodex/.agentcodex/kb/operations/` | `.claude/kb/operations/` | Cópia bulk |
| G6-06 | `agentcodex/.agentcodex/kb/orchestration/` | `.claude/kb/orchestration/` | Cópia bulk |
| G6-07 | `agentcodex/.agentcodex/kb/patterns/` | `.claude/kb/patterns/` | Cópia bulk |
| G6-08 | `agentcodex/.agentcodex/kb/platforms/` | `.claude/kb/platforms/` | Cópia bulk |

**Pulados:** `update-candidates/` (conteúdo WIP, não production)

**Total Grupo 6: ~40 arquivos (estimado)**

---

### Grupo 7 — mempalace hooks (AGENTCODE) — cópia + merge

| # | Arquivo | Ação |
|---|---------|------|
| G7-01 | `.claude/hooks/mempalace_save.sh` | Cópia de `mempalace/hooks/mempal_save_hook.sh` |
| G7-02 | `.claude/hooks/mempalace_precompact.sh` | Cópia de `mempalace/hooks/mempal_precompact_hook.sh` |
| G7-03 | `.claude/hooks/hooks.json` | Merge: base agentspec + entradas mempalace condicionais |

**Total Grupo 7: 3 arquivos**

---

### Grupo 8 — Arquivos criados do zero (AGENTCODE)

| # | Arquivo | Propósito |
|---|---------|-----------|
| G8-01 | `.claude/commands/data/sql.md` | Command /sql — Databricks/Fabric SQL expert |
| G8-02 | `.claude/commands/data/spark.md` | Command /spark — PySpark + Databricks expert |
| G8-03 | `.claude/commands/data/party.md` | Command /party — multi-perspective analysis |
| G8-04 | `.claude/commands/data/workflow.md` | Command /workflow — DOMA protocol orchestrator |
| G8-05 | `.claude/commands/data/pipeline.md` | Command /pipeline — pipeline design assistant |
| G8-06 | `scripts/update-agentspec.sh` | Script de update cirúrgico |
| G8-07 | `CLAUDE.md` | Instruções unificadas com seção mempalace |
| G8-08 | `README.md` | Documentação de instalação |
| G8-09 | `CHANGELOG.md` | Rastreamento de merges do agentspec |

**Total Grupo 8: 9 arquivos**

---

**TOTAL ESTIMADO: ~518 arquivos**

---

## Agent Assignment Rationale

| Agente | Grupos atribuídos | Motivo |
|--------|-------------------|--------|
| `@shell-script-specialist` | G8-06 (update-agentspec.sh) | Script bash com lógica de ownership + merge |
| `@python-developer` | G5-01..G5-09 (adaptação agentes) | Transformação de formato .md com frontmatter |
| `@ai-data-engineer` | G4-01..G4-07, G6-01..G6-08 | Curadoria de KB domains data-engineering |
| `@code-documenter` | G8-07..G8-09 (CLAUDE.md, README) | Documentação técnica |
| `(general build)` | G1, G2, G3, G7 (bulk copies) | Operações de cópia direta — sem especialista necessário |

---

## Code Patterns

### Pattern 1: update-agentspec.sh — estrutura completa

```bash
#!/usr/bin/env bash
# update-agentspec.sh — atualiza componentes agentspec sem tocar extensões agentcode
set -euo pipefail

AGENTSPEC_SOURCE="${AGENTSPEC_PATH:-C:/Users/User/ProjetosAgents/agentspec/plugin}"
AGENTCODE_TARGET="$(cd "$(dirname "$0")/.." && pwd)/.claude"
AGENTSPEC_MIN_VERSION="3.2.0"
DRY_RUN=false

[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

# Pastas de PROPRIEDADE do agentspec — seguro sobrescrever
AGENTSPEC_OWNED_DIRS=(
  "agents/architect"
  "agents/cloud"
  "agents/dev"
  "agents/platform"
  "agents/python"
  "agents/test"
  "agents/workflow"
  "kb/ai-data-engineering"
  "kb/airflow" "kb/aws" "kb/cloud-platforms" "kb/data-modeling"
  "kb/data-quality" "kb/dbt" "kb/gcp" "kb/genai" "kb/lakeflow"
  "kb/lakehouse" "kb/medallion" "kb/microsoft-fabric" "kb/modern-stack"
  "kb/prompt-engineering" "kb/pydantic" "kb/python" "kb/shared"
  "kb/spark" "kb/sql-patterns" "kb/streaming" "kb/supabase"
  "kb/terraform" "kb/testing"
  "commands/workflow" "commands/data-engineering" "commands/core"
  "commands/knowledge" "commands/review" "commands/visual-explainer"
  "skills/agent-router" "skills/data-engineering-guide"
  "skills/excalidraw-diagram" "skills/sdd-workflow" "skills/visual-explainer"
  "sdd"
)

# NOTA: agents/data-engineering/ é SHARED — agentspec tem 15, agentcode adiciona 9.
# Tratamento especial: atualizar só arquivos existentes do agentspec, não apagar extensões.
AGENTSPEC_OWNED_DATA_ENG_FILES=(
  # lista explícita dos 15 arquivos do agentspec em data-engineering/
  # populada durante o build inicial
)

copy_or_dry() {
  local src="$1" dst="$2"
  if $DRY_RUN; then
    echo "[DRY-RUN] cp -r '$src' → '$dst'"
  else
    mkdir -p "$(dirname "$dst")"
    cp -r "$src" "$dst"
  fi
}

echo "Atualizando agentspec → agentcode..."
echo "Fonte: $AGENTSPEC_SOURCE"
echo "Destino: $AGENTCODE_TARGET"

for dir in "${AGENTSPEC_OWNED_DIRS[@]}"; do
  src="$AGENTSPEC_SOURCE/$dir"
  dst="$AGENTCODE_TARGET/$dir"
  if [[ -d "$src" ]]; then
    copy_or_dry "$src" "$dst"
    echo "  ✔ $dir"
  else
    echo "  ⚠ $dir não encontrado na fonte (agentspec reorganizou?)"
  fi
done

# Merge hooks.json (não sobrescrever — re-gerar merged)
bash "$(dirname "$0")/_merge-hooks.sh" "$AGENTSPEC_SOURCE/hooks/hooks.json"

echo "✔ Update concluído."
```

---

### Pattern 2: hooks.json — estrutura merged com guard mempalace

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "if command -v mempalace &> /dev/null; then bash \"$(dirname \"$0\")/../hooks/mempalace_save.sh\"; fi"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "if command -v mempalace &> /dev/null; then bash \"$(dirname \"$0\")/../hooks/mempalace_precompact.sh\"; fi"
          }
        ]
      }
    ]
  }
}
```

**Nota:** Os hooks do agentspec base são mesclados ANTES das entradas do mempalace. O arquivo `hooks-agentspec-base.json` preserva o estado original do agentspec para re-merge no update.

---

### Pattern 3: formato de agente adaptado (data-agents → agentspec)

```markdown
---
name: databricks-sql-expert
description: >-
  Databricks SQL specialist for Unity Catalog, Delta Lake queries, and
  Databricks SQL Warehouse optimization. Delegates to Fabric specialists
  when target platform is Microsoft Fabric.
  Use PROACTIVELY when writing Databricks SQL, optimizing query plans,
  or working with Delta tables.
tools: Read, Write, Edit, Bash, Glob, Grep, TodoWrite
---

# Databricks SQL Expert

## Role
Elite Databricks SQL architect specializing in Unity Catalog, Delta Lake,
and Databricks SQL Warehouse query optimization.

## When to Use
- Writing or optimizing Databricks SQL queries
- Unity Catalog object management (schemas, volumes, tags)
- Delta Lake table operations (OPTIMIZE, VACUUM, Z-ORDER)
- Query plan analysis and performance tuning

## Capabilities
{conteúdo extraído de data-agents/agents/registry/sql-expert.md}

## KB Domains
- kb/databricks/ — Databricks-specific patterns
- kb/sql-patterns/ — Cross-platform SQL (agentspec)
- kb/doma-protocol/ — DOMA workflow integration

## Examples
{exemplos do data-agents adaptados}
```

---

### Pattern 4: command .md — estrutura para /sql, /spark, /party

```markdown
# SQL Command

> Ativa o agente especialista em SQL para Databricks e Microsoft Fabric

## Usage

```bash
/sql <query-or-problem>
/sql "optimize this Delta table query"
/sql "write a Unity Catalog migration script"
```

## What This Does

Delegates to `@databricks-sql-expert` with full context from:
- `kb/databricks/` — Databricks patterns
- `kb/fabric/` — Microsoft Fabric patterns
- `kb/sql-patterns/` — Cross-platform SQL (agentspec)

## Process

1. Detect target platform (Databricks vs Fabric vs generic)
2. Load relevant KB domain
3. Apply DOMA protocol: KB-first → Spec-first → Implementation
4. Validate output against guardrails (kb/guardrails/)

## References
- Agent: `agents/data-engineering/databricks-sql-expert.md`
- KB: `kb/databricks/`, `kb/fabric/`, `kb/sql-patterns/`
```

---

### Pattern 5: AGENTCODE_OWNED manifest para validação

```bash
# Arquivo: .claude/hooks/.agentcode-manifest.json
# Gerado durante o build — usado pelo update script para validar ownership
{
  "version": "1.0",
  "built_at": "2026-05-08",
  "agentspec_version": "3.2.0",
  "agentcode_owned": [
    "agents/languages",
    "agents/security",
    "kb/databricks",
    "kb/fabric",
    "kb/governance",
    "kb/doma-protocol",
    "kb/semantic-modeling",
    "kb/migration",
    "kb/guardrails",
    "kb/controls",
    "kb/foundations",
    "kb/integrations",
    "kb/metadata",
    "kb/operations",
    "kb/orchestration",
    "kb/patterns",
    "kb/platforms",
    "commands/data",
    "hooks/mempalace_save.sh",
    "hooks/mempalace_precompact.sh"
  ]
}
```

---

## Data Flow

```
FASE 1: Foundation (sequencial — G1 primeiro)
│
├── 1. Copiar agentspec/plugin/ → .claude/ (bulk, ~290 arquivos)
│   └── Salvar hooks-agentspec-base.json separado
│
FASE 2: Enriquecimento (paralelo — G2..G6 independentes)
│
├── 2a. Copiar ECC/agents/*.md → .claude/agents/languages/ + security/
├── 2b. Copiar ECC/.codex/, .cursor/ → raiz do repo
├── 2c. Copiar data-agents/kb/ (selecionado) → .claude/kb/ (novos domains)
├── 2d. Adaptar data-agents/registry/*.md → .claude/agents/data-engineering/ (novos)
├── 2e. Copiar agentcodex KB únicos → .claude/kb/
│
FASE 3: Integração (sequencial — depende da Fase 1)
│
├── 3a. Copiar mempalace hooks .sh → .claude/hooks/
├── 3b. Gerar hooks.json merged (base agentspec + mempalace entries)
├── 3c. Gerar .agentcode-manifest.json
│
FASE 4: Assets do repo
│
├── 4a. Criar scripts/update-agentspec.sh
├── 4b. Criar .claude/commands/data/*.md (5 commands)
├── 4c. Criar CLAUDE.md, README.md, CHANGELOG.md
│
FASE 5: Validação
│
└── 5. Verificar contagens: ≥119 agentes, ≥31 KB domains, hooks.json válido
```

---

## Integration Points

| Sistema externo | Tipo de integração | Quando ativo |
|----------------|-------------------|--------------|
| mempalace | Hook shell condicional | Se `mempalace` instalado no PATH |
| agentspec upstream | Script `update-agentspec.sh` | Quando usuário executa manualmente |
| Claude Code harness | Plugin manifest + `.claude/` dir | Sempre (plugin instalado) |
| Cursor IDE | `.cursor/` rules + hooks | Quando usando Cursor |
| Codex | `.codex/` AGENTS.md + config | Quando usando OpenAI Codex |

---

## Testing Strategy

| Tipo | Escopo | Arquivo | Ferramenta | Critério |
|------|--------|---------|------------|----------|
| Estrutural | Contagem de arquivos após build | `scripts/validate-build.sh` | bash + find | ≥119 agents, ≥31 KB domains |
| Funcional AT-001 | Plugin install | Manual | `claude plugin install` | Exit 0, plugin listed |
| Funcional AT-002 | SDD workflow | Manual | `/brainstorm test` | Output gerado |
| Funcional AT-005 | Update-safe | `scripts/test-update-safety.sh` | bash | Extensões AGENTCODE intactas |
| Funcional AT-007 | Fallback memória | Manual (sem mempalace) | Claude Code session end | `.claude/memory/` atualizado |
| Funcional AT-008 | hooks mempalace | Manual (com mempalace) | Claude Code session end | `mempalace_save.sh` executado |

### `scripts/validate-build.sh` — verificação pós-build

```bash
#!/usr/bin/env bash
ERRORS=0

agent_count=$(find .claude/agents -name "*.md" | wc -l)
kb_count=$(find .claude/kb -maxdepth 1 -type d | wc -l)

[[ $agent_count -ge 119 ]] || { echo "FAIL: agents=$agent_count (min 119)"; ERRORS=$((ERRORS+1)); }
[[ $kb_count -ge 31 ]]     || { echo "FAIL: kb_domains=$kb_count (min 31)"; ERRORS=$((ERRORS+1)); }

[[ -f ".claude/hooks/hooks.json" ]]               || { echo "FAIL: hooks.json missing"; ERRORS=$((ERRORS+1)); }
[[ -f ".claude/hooks/mempalace_save.sh" ]]        || { echo "FAIL: mempalace_save.sh missing"; ERRORS=$((ERRORS+1)); }
[[ -f "scripts/update-agentspec.sh" ]]            || { echo "FAIL: update-agentspec.sh missing"; ERRORS=$((ERRORS+1)); }
[[ -d ".codex" ]]                                 || { echo "FAIL: .codex/ missing"; ERRORS=$((ERRORS+1)); }
[[ -d ".cursor" ]]                                || { echo "FAIL: .cursor/ missing"; ERRORS=$((ERRORS+1)); }

[[ $ERRORS -eq 0 ]] && echo "✔ Build válido ($agent_count agentes, $kb_count KB domains)" || exit 1
```

---

## Error Handling

| Erro | Estratégia | Retry? |
|------|------------|--------|
| Arquivo fonte não encontrado (update script) | `echo "⚠ não encontrado" + continua` | Não — avisa usuário |
| `hooks.json` malformado após merge | Validar com `python -m json.tool` antes de salvar | Não — abortar merge |
| ECC agent sem frontmatter válido | Prefixar com frontmatter mínimo `---name: ecc-{filename}---` | Não — auto-fix |
| data-agents registry sem campo `description` | Usar nome do arquivo como fallback | Não — auto-fix |
| Plugin install falha por tamanho | Verificar com `du -sh .claude/` e reportar ao usuário | Não — investigar |

---

## Configuration

| Variável | Tipo | Default | Onde configurar |
|----------|------|---------|----------------|
| `AGENTSPEC_PATH` | env | `../agentspec/plugin` | Shell environment ou .env |
| `AGENTSPEC_MIN_VERSION` | string no script | `"3.2.0"` | `scripts/update-agentspec.sh` linha 6 |
| `DRY_RUN` | flag | `false` | `update-agentspec.sh --dry-run` |
| `MEMPALACE_HOOKS_ENABLED` | bool em hooks.json | `true` (com guard) | `.claude/hooks/hooks.json` |

---

## Security Considerations

- O script `update-agentspec.sh` usa `cp -r` não `rm -rf + cp` — menor blast radius; arquivos extras em pastas OWNED são preservados
- hooks mempalace usam guard `command -v mempalace` antes de executar — não expõe erro se ausente
- Nenhuma credencial, token ou secret entra no repositório — agentcodex e data-agents não têm credenciais nos KB domains
- ECC `.cursor/hooks/` contém scripts JS de hook — verificar manualmente que não executam código arbitrário antes do build

---

## Observability

| Aspecto | Implementação |
|---------|--------------|
| Build validation | `scripts/validate-build.sh` — saída stdout com contagens |
| Update audit | `update-agentspec.sh` imprime cada dir copiado; pipe para log se necessário |
| Plugin install | `claude plugin list` mostra versão e status enabled/disabled |
| Memory persistence | `.claude/memory/` (nativo) ou `mempalace list` (se instalado) |

---

## Revision History

| Versão | Data | Autor | Mudanças |
|--------|------|-------|---------|
| 1.0 | 2026-05-08 | design-agent | Versão inicial |

---

## Next Step

**Pronto para:** `/build .claude/sdd/features/DESIGN_AGENTCODE_UNIFIED_FRAMEWORK.md`
