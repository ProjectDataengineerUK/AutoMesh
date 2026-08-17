---
source: "Lições reais de build — RadarImovel V2 (2026-06), Licitacerta AGENTE_COMPLIANCE (2026-05), KAFKADATABRICKS (2026-07)"
confidence: high
validated: "2026-07-22"
owner: AGENTCODE   # arquivo extra — não é sobrescrito pelo update-agentspec.sh
---

# Padrões: Lições de Projetos Reais — Python / FastAPI / SQLAlchemy / LangChain

> Gotchas que custaram horas de debug em projetos reais. Consultar antes de escrever
> testes, camadas de serviço ou integrações LLM.
> Agentes: `python-developer`, `python-reviewer`, `test-generator`, `llm-specialist`.

---

## SQLAlchemy / Banco

| # | Padrão |
|---|--------|
| PY1 | **`JSON` nos modelos, `JSONB` só nas migrations** — permite SQLite nos testes de unidade e PostgreSQL em produção sem duplicar modelos. |
| PY2 | **Serviços não chamam `db.commit()`** — quem chama decide a transação. No FastAPI o commit acontece ao fim do request; nos testes, o rollback do teardown limpa. Violar contamina testes com engine module-scoped. |
| PY3 | **UUID PK: `default=new_uuid` é Python-level** — não gera `DEFAULT` na DDL. INSERT raw que omita `id` falha com NOT NULL no SQLite. Usar `server_default=text("gen_random_uuid()")` ou sempre incluir `id` em raw SQL. |
| PY4 | **`COALESCE(EXCLUDED.col, target.col)`** em upserts onde múltiplos loaders atualizam colunas diferentes da mesma linha — sem isso, um loader zera as colunas dos outros. |

## Testes (pytest)

| # | Padrão |
|---|--------|
| PY5 | **`dependency_overrides[get_current_user]`** é mais limpo e robusto que patchar o módulo de auth + header — evita o `HTTPBearer` rejeitar o request antes do mock agir. |
| PY6 | **Patch onde o símbolo vive no momento do patch** — módulo que reexporta (`from services.x import fn`) cria dois nomes para o mesmo objeto; `patch("app.agents.y.fn")` só funciona se `y` importou com `from ... import fn`. |
| PY7 | **Factories de fixture incluem TODOS os campos NOT NULL** — helper `make_property(db, **overrides)` parametrizado elimina o risco de omitir colunas obrigatórias. |
| PY8 | **Fixtures function-scoped + engine module-scoped não se misturam com `db.commit()`** — teste que comita torna dados de fixture permanentes. Ou engine function-scoped para todos, ou IDs totalmente únicos + assertions agnósticas. |
| PY9 | **DeprecationWarnings como erro em CI** (`filterwarnings = error::DeprecationWarning` no pytest.ini) — warnings silenciosos acumulam (ex.: `regex=` → `pattern=` no FastAPI 0.100+). |
| PY10 | **Nova regra de validação → grep por dados sintéticos antigos** — regra nova pode invalidar fixtures de fases anteriores silenciosamente (constituição §11 HV5). |
| PY11 | **Mocks de infraestrutura**: `mongomock` para camada Mongo, `testcontainers` para integração ponta a ponta — testar sem cluster real. |

## LangChain / LLM em produção

| # | Padrão |
|---|--------|
| PY12 | **`include_raw=True` é o único jeito confiável de obter metadados de token** em structured output — `with_structured_output()` padrão descarta o `AIMessage`. Sempre checar `result.get("parsing_error")` e levantar exceção, nunca retornar resultado quebrado em silêncio. |
| PY13 | **OTel opcional: `contextlib.nullcontext()` como fallback** — o anti-padrão de duplo invoke (invoke no `try`, invoke de novo no `except`) faz DUAS chamadas LLM se o OTel falhar depois do span abrir. |
| PY14 | **`ainvoke()` em vez de `asyncio.to_thread(run)`** — `to_thread` consome worker do pool para uma chamada I/O-bound; todos os ChatModels suportam async nativo desde LangChain 0.1. |
| PY15 | **Dependência GCP opcional: singleton lazy (`_get_bq()`)** — checa env var e inicializa sob demanda; melhor que injeção no construtor (não quebra a API pública, mockável por patch no `from_env`). |

## Arquitetura de código testável

| # | Padrão |
|---|--------|
| PY16 | **Lógica de streaming em módulo Python puro** compartilhado entre notebooks e testes (`src/common/transforms.py`) — testa lógica Spark sem cluster real. |
| PY17 | **Resultados como dataclass puro, não `BaseModel`** — engine chamável sem contexto FastAPI/Pydantic; conversão para dict só no router. |
| PY18 | **Fábrica única para canais/integrações** (`build_channels()`) — teste mocka a fábrica retornando `[(mock, "dest")]` sem saber qual canal concreto existe. |
| PY19 | **Seeds YAML com `@lru_cache(maxsize=1)`** + `cache_clear()` após update admin — fallback transparente em teste e produção. |
