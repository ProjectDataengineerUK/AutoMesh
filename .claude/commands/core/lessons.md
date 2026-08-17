---
description: Ver, analisar e gerenciar as lições capturadas automaticamente (LESSON_LEARNED)
---

# /lessons — Lições Aprendidas

Gerencia o buffer de lições capturadas pelos hooks `lesson_capture.sh` (triggers
`error`/`slow_op` em tool calls) e injetadas no início das sessões por `lesson_recall.sh`.

## Usage

```
/lessons              → resumo: contagem por trigger/tool, lições recorrentes
/lessons show [N]     → mostra as N lições mais recentes (default 10)
/lessons clear        → arquiva o buffer atual (move buffer/ → archive/)
/lessons purge        → apaga TUDO (buffer + archive) — pedir confirmação
```

## Execution

Os dados vivem em `~/.mempalace/lessons/`:

- `buffer/{session_id}.jsonl` — lições da(s) sessão(ões) ainda não mineradas
- `archive/*.jsonl` — buffers já minerados/arquivados
- `timing/` — marcadores internos de t0 (ignorar)

### Resumo (default)

```bash
python3 - <<'PY'
import glob, json, os
from collections import Counter
root = os.path.expanduser("~/.mempalace/lessons")
lessons = []
for p in glob.glob(f"{root}/buffer/*.jsonl") + glob.glob(f"{root}/archive/*.jsonl"):
    with open(p) as f:
        lessons += [json.loads(l) for l in f if l.strip()]
print(f"Total: {len(lessons)} lições")
print("Por trigger:", dict(Counter(t for l in lessons for t in l.get("triggers", []))))
print("Por tool:  ", dict(Counter(l.get("tool","?") for l in lessons).most_common(8)))
rec = Counter((l.get("tool",""), str(l.get("context",""))[:60]) for l in lessons)
print("Recorrentes (>=2x):")
for (tool, ctx), n in rec.most_common(10):
    if n >= 2:
        print(f"  {n}x  {tool}: {ctx}")
PY
```

Depois do resumo, **interprete**: aponte padrões (mesmo erro se repetindo entre
sessões = candidato a correção definitiva ou a entrada nova em
`kb/databricks/patterns/known-incidents.md` / `kb/python/patterns/project-lessons.md`).

### show / clear / purge

- `show`: exibir as N últimas linhas dos JSONL formatadas (ts, trigger, tool, contexto, evidência).
- `clear`: `mkdir -p ~/.mempalace/lessons/archive && mv ~/.mempalace/lessons/buffer/*.jsonl ~/.mempalace/lessons/archive/ 2>/dev/null`
- `purge`: confirmar com o usuário antes; então `rm -rf ~/.mempalace/lessons/{buffer,archive}/*.jsonl`.

## Promoção a conhecimento permanente

Se uma lição recorrente for genérica e valiosa, proponha promovê-la a KB
(o equivalente manual do `failure_pattern_promote` do agentcodex):
adicionar entrada no KB de padrões adequado e citar a evidência.
