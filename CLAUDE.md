# AutoMesh

> Desenho arquitetural (fase de concepção) de uma plataforma corporativa de dados e IA "Zero-Touch Data Mesh": ingestão via Kafka/Airflow, processamento distribuído no Databricks (PySpark/Delta), transformação com dbt/Snowflake, agentes autônomos de self-healing (schema drift, FinOps, retreinamento de modelos), motor RAG corporativo e entrega segura via Microsoft Graph (Teams/Outlook, OAuth2), com Human-in-the-Loop para decisões críticas.

---

## Stack

- **Streaming:** Apache Kafka
- **Orquestração:** Apache Airflow (substitui Azure Data Factory)
- **Processamento distribuído:** Databricks + PySpark, Delta Live Tables
- **Data Warehouse / Transformação:** Snowflake + dbt
- **Governança de dados:** Unity Catalog, Data Contracts (YAML/JSON), RBAC/ABAC
- **MLOps:** Databricks Feature Store, MLflow (data/concept drift, continuous training)
- **LLMOps / RAG:** RAG corporativo sobre SharePoint, RAGAS (avaliação), NeMo Guardrails, LangChain/LangGraph, LiteLLM (roteamento por custo)
- **BI / Visualização:** Databricks SQL (Lakeview), Microsoft Fabric + Power BI (DirectLake, Copilot)
- **Automação de código:** GitHub + GitHub Actions (self-healing abre PRs automaticamente)
- **Segurança:** OAuth2 (Microsoft), Microsoft Sentinel (SIEM)
- **Entrega:** Microsoft Graph API (Teams, Outlook, Adaptive Cards)

## Estrutura

```
AutoMesh/
├── .claude/                        # agentcode: agents, commands, kb, skills, hooks
│   └── sdd/
│       ├── features/                # BRAINSTORM/DEFINE/DESIGN de features em andamento (AGENTCODE_UNIFIED_FRAMEWORK — meta-tooling, Ready for Build)
│       ├── reports/                 # BUILD_REPORT de features em andamento (vazio no momento)
│       └── archive/
│           ├── FASE1_INGESTAO/      # ciclo SDD completo da Fase 1 — Shipped 2026-08-01
│           ├── FASE2_PROCESSAMENTO_SELFHEALING/  # ciclo SDD completo da Fase 2 — Shipped 2026-08-04
│           ├── FASE3_INSIGHTS_FINOPS/            # ciclo SDD completo da Fase 3 — Shipped 2026-08-06
│           └── FASE4_RAG_CONTEUDO/               # ciclo SDD completo da Fase 4 — Shipped 2026-08-11
├── pipelines/
│   ├── ingestion/                   # Fase 1 — Ingestão (Kafka/Airflow) — shipped, primeira fatia implementada
│   │   ├── contracts/               # Contratos de dados YAML (ODCS-lite), um por fonte
│   │   ├── producers/               # Producer real (brapi.dev/B3) + geradores simulados (infra, CRM)
│   │   ├── common/                  # kafka_config, contract_validator, bronze_writer (Delta via deltalake)
│   │   ├── dags/                    # 3 DAGs Airflow 3.0 (kafka_market, kafka_infra, batch_crm)
│   │   ├── tests/                   # pytest — validador, bronze writer, producer B3, integridade dos DAGs
│   │   └── requirements.txt
│   ├── processing/                  # Fase 2 (parte 1) — Bronze→Silver — shipped
│   │   ├── jobs/                    # bronze_to_silver.py (PySpark, MERGE/append por fonte)
│   │   └── dags/                    # dag_process_bronze_to_silver (aciona Job Databricks via provider)
│   ├── self_healing/                 # Fase 2 (parte 2) — diagnóstico via LLM + PR no GitHub — shipped
│   │   ├── common/                  # checkpoint, failure_capture, llm_diagnostician, guardrails, github_pr, rejection_writer
│   │   ├── dags/                    # dag_self_healing_diagnose
│   │   └── tests/                   # pytest — guardrails, LLM/GitHub mockados, checkpoint real, integridade dos DAGs
│   ├── insights/                     # Fase 3 (parte 1) — Isolation Forest + Continuous Training — shipped
│   │   ├── jobs/                    # train_outlier_model, generate_insights, drift_check (MLflow + KS-test)
│   │   ├── dags/                    # dag_train_outlier_model, dag_generate_insights
│   │   ├── model_registry_state.yaml # estado versionado do alias @champion — promoção só via PR
│   │   └── tests/
│   ├── finops/                       # Fase 3 (parte 2) — governança de custo de workload — shipped
│   │   ├── jobs/                    # cost_monitor.py (system.billing.usage + fallback dag_run.duration)
│   │   ├── dags/                    # dag_finops_monitor
│   │   └── tests/
│   └── rag/                          # Fase 4 — Motor RAG + Fábrica de Conteúdo — shipped
│       ├── contracts/               # sharepoint_documents.contract.yaml (ODCS-lite)
│       ├── config/                  # rag_config.yaml (tunáveis) + guardrails/config.yml (NeMo Guardrails)
│       ├── common/                  # graph_client (MSAL/Graph), delta_cursor, chunking, vector_index (Databricks Vector Search), nemo_rails
│       ├── jobs/                    # ingest_sharepoint, retrieval (hybrid+rerank), content_factory (gate RAGAS)
│       ├── dags/                    # dag_ingest_sharepoint_documents, dag_generate_content
│       └── tests/
├── docker-compose.local.yml         # Stack local (Airflow 3.0 + Redpanda) para validar as Fases 1-3 sem a conta cloud trial
├── context.md                       # desenho da arquitetura (fonte deste CLAUDE.md)
└── CLAUDE.md
```

## Arquivos-chave

| Arquivo | Função |
|---------|--------|
| `context.md` | Especificação completa da arquitetura Zero-Touch Data Mesh — visão de referência do projeto |
| `.claude/sdd/archive/FASE1_INGESTAO/SHIPPED_2026-08-01.md` | Retrospectiva da Fase 1 — o que foi entregue, critérios de sucesso verificados, lições aprendidas |
| `.claude/sdd/archive/FASE1_INGESTAO/DESIGN_FASE1_INGESTAO.md` | Design técnico da Fase 1 — arquitetura, 4 ADRs, file manifest |
| `.claude/sdd/archive/FASE1_INGESTAO/BUILD_REPORT_FASE1_INGESTAO.md` | Relatório de build — testes, bugs encontrados/corrigidos validando contra infra real, blockers restantes |
| `docker-compose.local.yml` | Como reproduzir a validação contra Airflow/Kafka reais localmente (`docker compose -f docker-compose.local.yml up -d`) |
| `pipelines/ingestion/common/contract_validator.py` | Núcleo da validação de contrato de dados (null/tipo/constraint) usado por todos os DAGs |
| `pipelines/ingestion/common/bronze_writer.py` | Escrita das tabelas Delta do Bronze e da DLQ unificada (+ coluna `detected_at`, adicionada na Fase 2) |
| `.claude/sdd/archive/FASE2_PROCESSAMENTO_SELFHEALING/SHIPPED_2026-08-04.md` | Retrospectiva da Fase 2 — o que foi entregue, critérios de sucesso verificados, lições aprendidas |
| `.claude/sdd/archive/FASE2_PROCESSAMENTO_SELFHEALING/DESIGN_FASE2_PROCESSAMENTO_SELFHEALING.md` | Design técnico da Fase 2 — 5 ADRs (Databricks Free Edition, guardrails determinísticos, LLM via Claude, etc.) |
| `.claude/sdd/archive/FASE2_PROCESSAMENTO_SELFHEALING/BUILD_REPORT_FASE2_PROCESSAMENTO_SELFHEALING.md` | Relatório de build da Fase 2 — validado contra Airflow 3.0 real; achou e corrigiu bug de import pesado do `anthropic` |
| `pipelines/self_healing/common/guardrails.py` | As duas camadas de defesa antes de qualquer PR de self-healing/FinOps/promoção de modelo (allowlist de caminho + padrões perigosos) |
| `.claude/sdd/archive/FASE3_INSIGHTS_FINOPS/SHIPPED_2026-08-06.md` | Retrospectiva da Fase 3 — o que foi entregue, critérios de sucesso verificados, lições aprendidas |
| `.claude/sdd/archive/FASE3_INSIGHTS_FINOPS/DESIGN_FASE3_INSIGHTS_FINOPS.md` | Design técnico da Fase 3 — 4 ADRs (aliases MLflow, reuso do self-healing sem mudar sua lógica, promoção via arquivo de estado, shadow-check honesto) |
| `.claude/sdd/archive/FASE3_INSIGHTS_FINOPS/BUILD_REPORT_FASE3_INSIGHTS_FINOPS.md` | Relatório de build da Fase 3 — validado contra Airflow 3.0 e MLflow reais; achou e corrigiu 5 bugs reais (bootstrap, tipo numpy, import pesado, API depreciada) |
| `pipelines/insights/jobs/train_outlier_model.py` | Treino do Isolation Forest + registro no MLflow com alias `@challenger` |
| `.claude/sdd/archive/FASE4_RAG_CONTEUDO/SHIPPED_2026-08-11.md` | Retrospectiva da Fase 4 — o que foi entregue, critérios de sucesso verificados, lições aprendidas |
| `.claude/sdd/archive/FASE4_RAG_CONTEUDO/DESIGN_FASE4_RAG_CONTEUDO.md` | Design técnico da Fase 4 — 6 ADRs (bypass do LLM diagnostician para conteúdo pré-aprovado, gate RAGAS antes do self-healing, Vector Search HYBRID, rerank via Claude, cursor dedicado do Graph delta query, NeMo Guardrails isolado) |
| `.claude/sdd/archive/FASE4_RAG_CONTEUDO/BUILD_REPORT_FASE4_RAG_CONTEUDO.md` | Relatório de build da Fase 4 — 77/77 testes passando, 0 violações de lint; Vector Search/Unity Catalog e o tenant Microsoft 365 Developer seguem pendentes de provisionamento (não validados contra infra real) |
| `pipelines/rag/jobs/content_factory.py` | Gate RAGAS (faithfulness/answer_relevancy) — só rascunhos aprovados viram evento de self-healing; reprovados vão direto para `self_healing_rejections` |
| `pipelines/self_healing/common/llm_diagnostician.py` | `resolve_diagnosis()` (Fase 4): eventos `content_generation` pulam a chamada à LLM para preservar fidelidade ao texto já avaliado pelo RAGAS |



## Convenções

- **Linter:** `ruff` (`python -m ruff check pipelines/`) — 0 violações atualmente
- **Formatter:** segue as regras do `ruff` (import sorting incluso); sem formatter dedicado (black/etc.) configurado
- **Testes:** `pytest` (`python -m pytest pipelines/`) — baseline histórico de 77 testes nas Fases 1-4; a remediação acrescentou 6 e a Fase 5 possui 18 testes executáveis próprios. No último gate, 18 delivery + 25 self-healing passaram; DagBags de delivery e self-healing importaram sem erros no Airflow 3.0 isolado. A suíte completa deve rodar no CI Linux, pois o host Windows gerenciado nega acesso ao diretório temporário de alguns testes Delta.
- **Type hints:** obrigatórios em todo código Python novo (convenção do DESIGN/Build, não enforced por mypy ainda)

## Como rodar

### Validação e observabilidade da Fase 6

```bash
python scripts/validation/run_validation.py inventory --environment local
python scripts/validation/generate_report.py --output-dir artifacts/validation/latest
docker compose -f docker-compose.observability.yml up -d
```

O inventário nunca inclui valores de secrets. Probes externos são opt-in e evidências expiradas, puladas ou de outro commit não promovem maturidade. O stack local expõe OTLP em `4317/4318`, Prometheus em `9090` e Grafana em `3000`.

**Fases 1-5** estão implementadas; a Fase 5 (Entrega Segura + HITL) também passou por validação de DagBag no Airflow 3.0 isolado. Integrações Microsoft 365/Teams/Outlook e MLflow/Unity Catalog reais continuam pendentes de validação de infraestrutura.

```bash
# Instalar dependências (Fases 1-4)
pip install -r pipelines/ingestion/requirements.txt
pip install -r pipelines/processing/requirements.txt
pip install -r pipelines/self_healing/requirements.txt
pip install -r pipelines/insights/requirements.txt
pip install -r pipelines/finops/requirements.txt
pip install -r pipelines/rag/requirements.txt
pip install -r pipelines/delivery/requirements.txt

# Rodar lint
python -m ruff check pipelines/

# Rodar testes (não requer Kafka/Airflow/Databricks reais — usa Delta local + mocks)
python -m pytest pipelines/ -v
```

Para validar os DAGs/producers contra Airflow 3.0 e Kafka de verdade sem depender da conta cloud trial, use o stack local:

```bash
docker compose -f docker-compose.local.yml up -d
# Airflow UI em http://localhost:8080 (user/senha: airflow/airflow)
docker compose -f docker-compose.local.yml down    # ao terminar
```

Essa validação já foi feita para as três primeiras fases:
- **Fase 1** (`SHIPPED_2026-08-01.md`): encontrou/corrigiu 4 bugs de API real (sensor Kafka do Airflow, import de `get_current_context`, flag do CLI de connections, dependência de task faltando). Uma run completa via scheduler até o estado `success` ficou bloqueada por limite de CPU do Docker Desktop desta máquina — não é um problema de código.
- **Fase 2** (`SHIPPED_2026-08-04.md`): encontrou/corrigiu 1 bug real (import pesado do `anthropic` estourando o timeout de parse de DAG do Airflow) e confirmou a API real do `DatabricksRunNowOperator`. O workspace Databricks Free Edition em si nunca foi provisionado (não dá para simular via Docker local).
- **Fase 3** (`SHIPPED_2026-08-06.md`): encontrou/corrigiu 5 bugs reais (2 de bootstrap do modelo sem `@champion`, 1 de tipo `numpy.bool_`, mesmo bug de import pesado do MLflow, e um `TriggerDagRunOperator` depreciado). Pipeline de ML completo (treino → promoção → inferência) validado com MLflow real (SQLite local). `system.billing.usage` real e o workspace Databricks Free Edition seguem pendentes de provisionamento.

**Fase 4** (`.claude/sdd/archive/FASE4_RAG_CONTEUDO/SHIPPED_2026-08-11.md`) segue validada só com Delta local + mocks (77/77 testes, 0 violações de lint) — ainda **não** passou pela validação real via `docker-compose.local.yml`/infra real. Depende de dois provisionamentos: a mesma classe de risco que a Fase 3 já havia deixado pendente (Databricks Vector Search/Unity Catalog) mais um novo desta fase (tenant Microsoft 365 Developer + site SharePoint de teste para o app registration Entra ID).

Rodar contra a conta cloud trial de produção (Confluent Cloud + Astronomer/Databricks trial) ainda está pendente para as quatro fases.

---

## Agentes recomendados (agentcode)

| Agente | Quando usar |
|--------|-------------|
| `@brainstorm-agent` | Explorar e expandir as fases da arquitetura antes de codificar |
| `@the-planner` | Quebrar o mega projeto em entregas sequenciais (Fase 1 → Fase 5) |
| `@design-agent` | Desenhar contratos de dados, schemas Delta, DAGs do Airflow |
| `@databricks-spark-expert` | PySpark, DLT, LakeFlow, Delta Lake (Fase 2 e 3) |
| `@dbt-specialist` | Modelagem no dbt/Snowflake (camada Gold) |
| `@airflow-specialist` | DAGs de orquestração ponta a ponta |
| `@fabric-architect` | Integração DirectLake / Power BI / Copilot |
| `@genai-architect` | Motor RAG, guardrails, roteamento de modelos |
| `@ci-cd-specialist` | GitHub Actions para self-healing (auto-PR) |
| `@security-reviewer` | OAuth2, RBAC/ABAC, Unity Catalog, Sentinel |
| `@code-reviewer` | Sempre, uma vez que o código comece a ser escrito |

## Comandos úteis

| Comando | Quando usar |
|---------|-------------|
| `/brainstorm` | Aprofundar decisões ainda em aberto da arquitetura |
| `/define` | Formalizar requisitos e contratos de dados |
| `/design` | Detalhar design técnico de cada fase |
| `/pipeline` | Scaffolding de DAGs/pipelines quando o código começar |
| `/status` | Checar progresso do projeto |
| `/preflight` | Checagem antes de abrir PRs |

---

_Gerado por `/start` em 2026-07-31._
_Sincronizado em 2026-08-17_ — Fases 1-5 completaram o ciclo SDD. A Fase 5 adicionou outbox transacional, Teams/Outlook adapters, ledger HITL, aplicação MLflow com precondição e integração automática após PR de self-healing. Seus DAGs e o DAG integrado de self-healing importaram sem erros no Airflow 3.0 isolado; infraestrutura Microsoft 365 e Unity Catalog permanece pendente.
