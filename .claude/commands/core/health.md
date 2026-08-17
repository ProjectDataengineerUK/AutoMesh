---
description: Auto-diagnóstico completo do agentcode — build, hooks, referências, KBs e frescor dos upstreams
---

# /health — Diagnóstico do Plugin

Roda a bateria completa de verificações do agentcode e apresenta um relatório
de saúde único. Use após atualizar o plugin, importar componentes, ou quando
algo parecer quebrado.

## Execution

Rode cada verificação e monte a tabela final:

```bash
# 1. Build do plugin (agents, KBs, estrutura, hooks.json)
bash scripts/validate-build.sh

# 2. Suite de regressão dos hooks (18 cenários)
bash tests/test_hooks.sh

# 3. Sintaxe de todos os shell scripts
find .claude/hooks scripts tests -name "*.sh" -print0 | xargs -0 -n1 bash -n && echo "sintaxe OK"

# 4. Referências do hooks.json resolvem
python3 -c "
import json, os, re
d = json.load(open('.claude/hooks/hooks.json'))
missing = [m for es in d['hooks'].values() for e in es for h in e['hooks']
           for m in re.findall(r'\\\$\{CLAUDE_PLUGIN_ROOT\}/([^\"\s]+)', h['command'])
           if not os.path.exists('.claude/' + m)]
print('hooks refs:', 'OK' if not missing else f'FALTAM {missing}')
"

# 5. Frescor dos repositórios de referência
bash scripts/update-references.sh

# 6. Readiness do próprio repo (agentcodex)
python3 scripts/agentcodex.py preflight . 2>/dev/null | head -8
```

## Output

Apresentar como tabela:

| Verificação | Status | Detalhe |
|-------------|--------|---------|
| Build       | ✔/✘   | N agents, N KB domains |
| Hooks (testes) | ✔/✘ | N passed / N failed |
| Sintaxe shell | ✔/✘ | — |
| Referências hooks.json | ✔/✘ | — |
| Upstreams   | ✔/⚠   | quais repos estão atrás e por quantos commits |
| Preflight   | ✔/⚠   | blocos pendentes |

Se algo falhar: diagnosticar a causa antes de propor correção, e propor o fix
mínimo. Se um upstream estiver atrás, sugerir `scripts/update-references.sh --pull`
(e `update-agentspec.sh` se for o agentspec).
