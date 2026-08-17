# Databricks AI Surface

## Purpose

Map the Databricks AI capabilities found in `data-agents` into AgentCodex
routing and design guidance.

## Capability Map

| Capability | Use |
|---|---|
| AI Functions | SQL/PySpark-native classification, extraction, summarization, translation, masking, similarity, document parsing, forecasting |
| `ai_query` | Complex custom endpoint calls and structured responses when task-specific functions are not enough |
| Agent Bricks | Knowledge Assistants, Genie Spaces, and Supervisor Agents |
| Genie | Natural-language exploration of curated Unity Catalog data |
| Vector Search | Managed vector indexes for RAG and semantic retrieval |
| Model Serving | Real-time inference endpoints for classic ML, pyfunc, and GenAI agents |
| MLflow Evaluation | evaluation datasets, scorers, traces, prompt optimization, judge alignment |
| Databricks Apps | Python web apps with Databricks auth and resources |
| Lakebase | Postgres-compatible operational database patterns inside Databricks-oriented apps |

## AI Functions

Prefer task-specific functions before generic `ai_query`.

| Task | Prefer |
|---|---|
| sentiment | `ai_analyze_sentiment` |
| fixed label classification | `ai_classify` |
| field extraction | `ai_extract` |
| summarization | `ai_summarize` |
| PII redaction | `ai_mask` |
| translation | `ai_translate` |
| document parsing | `ai_parse_document` |
| time-series forecasting | `ai_forecast` |
| complex endpoint call | `ai_query` |

## Agent Bricks

Agent Bricks from the `data-agents` source:

- Knowledge Assistant for document Q&A from files in Unity Catalog Volumes
- Genie Space for natural-language SQL exploration over governed tables
- Supervisor Agent for orchestration across endpoints, Genie Spaces, Unity Catalog functions, and MCP servers

Design rules:

- Use the current `Supervisor Agent` naming in new docs and prompts.
- Verify regional availability and compliance profile requirements before implementation.
- End users need explicit permissions on subagents and underlying data.
- For external MCP servers, model the required connection, authentication, and `USE CONNECTION` privilege.

## Vector Search

Choose endpoint and index type before writing ingestion.

| Choice | Use |
|---|---|
| Standard endpoint | lower latency and real-time use cases |
| Storage-optimized endpoint | very large scale and lower cost where supported |
| Delta Sync managed embeddings | simplest RAG path from Delta tables |
| Delta Sync self-managed embeddings | custom embedding model requirements |
| Direct access index | manual vector CRUD or real-time updates |
| Hybrid search | semantic plus keyword retrieval |

## Model Serving

Use Model Serving when the system needs a stable inference endpoint instead of
ad hoc notebook execution.

Review points:

- package dependencies and model resources are declared
- endpoint input/output schema is tested
- serving endpoint permissions are explicit
- observability includes logs, traces, latency, and failure modes

## Databricks Apps

For Databricks Apps, keep app configuration explicit:

- choose framework: Streamlit, Dash, Gradio, Flask, FastAPI, or Reflex
- use SDK configuration rather than hardcoded tokens
- reference Databricks resources through app configuration
- use production servers for Flask/FastAPI, not development servers
- decide app auth, user auth, or both before implementation

## Review Checklist

- [ ] Capability selection is explicit: AI Functions, Vector Search, Serving, Genie, Agent Bricks, or Apps.
- [ ] Unity Catalog data and volume dependencies are identified.
- [ ] Permissions are defined for users, service principals, endpoints, and functions.
- [ ] Model names and endpoint names are centralized, not scattered in SQL or notebooks.
- [ ] Evaluation and monitoring are part of the design for GenAI or RAG workflows.
- [ ] Regional availability is checked before committing to managed AI features.

## Source Notes

- Enriched from `data-agents/skills/databricks/databricks-ai-functions/`
- Enriched from `data-agents/skills/databricks/databricks-agent-bricks/`
- Enriched from `data-agents/skills/databricks/databricks-vector-search/`
- Enriched from `data-agents/skills/databricks/databricks-model-serving/`
- Enriched from `data-agents/skills/databricks/databricks-mlflow-evaluation/`
- Enriched from `data-agents/skills/databricks/databricks-app-python/`
