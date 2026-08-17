# BRAINSTORM: Fase 1 — Ingestão (Kafka/Airflow)

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | FASE1_INGESTAO |
| **Date** | 2026-07-31 |
| **Author** | brainstorm-agent |
| **Status** | ✅ Complete (Defined) |

---

## Initial Idea

**Raw Input:** Explorar a Fase 1 (Ingestão) da arquitetura Zero-Touch Data Mesh descrita em `context.md` — fechar o desenho conceitual completo (contratos de dados, tópicos Kafka, DAGs Airflow, hand-off pro Bronze) antes de partir para scaffolding de código.

**Context Gathered:**
- `context.md` descreve a arquitetura completa de 5 fases da plataforma; nenhum código-fonte existe ainda (`CLAUDE.md`: "Projeto ainda em fase de especificação").
- O projeto é uma peça de portfólio/preparação para entrevistas de Lead/Staff AI Data Engineer — a narrativa de apresentação já está em `context.md` e influencia decisões de design (ex: preferir um único painel de orquestração visível).
- `context.md` já antecipa o padrão de integração Kafka+Airflow: "O Apache Airflow escuta o evento (ex: fechamento do mercado da B3 via Kafka)" — usado como evidência para a escolha de approach.

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|--------|-------------|--------------|
| Likely Location | Nenhuma pasta de código ainda | Sugerir `pipelines/ingestion/` (DAGs, producers, contracts) na fase de Design |
| Relevant KB Domains | `airflow`, `streaming`, `controls/data-contracts`, `patterns/streaming`, `databricks`, `data-quality`, `orchestration` | Consultar para padrões de DAG, contratos e streaming na fase de Define/Design |
| IaC Patterns | N/A — infraestrutura de nuvem ainda não provisionada | Escolha de conta cloud trial (Confluent Cloud / Astronomer / Databricks trial) fica para Design |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Qual fatia da arquitetura explorar neste brainstorm? | Fase 1 — Ingestão (Kafka/Airflow) | Delimita o escopo à fundação de ingestão, não à plataforma inteira |
| 2 | Qual o objetivo principal desta sessão? | Design conceitual completo primeiro; scaffolding de código depois, em sessão separada | Este documento cobre só o desenho — sem artefatos executáveis ainda |
| 3 | Quais fontes de dados a Fase 1 vai ingerir de fato? | Mix: 1 fonte real (B3) + resto simulado | Reduz dependência de integrações externas mantendo credibilidade de portfólio |
| 4 | Qual ambiente de execução está disponível? | Conta cloud gratuita/trial | Descarta opção 100% local; toda decisão de arquitetura precisa considerar custo/quota |
| 5 | Qual o critério de sucesso deste brainstorm? | Visão completa ponta a ponta da Fase 1 (contratos + DAGs + hand-off pro Bronze) | Define o que precisa estar fechado antes de avançar pro `/define` |
| 6 | Há amostras/exemplos disponíveis (payloads, schemas)? | Nenhum ainda | Contratos e schemas serão definidos do zero neste brainstorm |
| 7 | Qual fonte real de dados de mercado (B3) usar? | brapi.dev | Define formato de payload e estratégia de polling do producer |

**Minimum Questions:** 3 ✅ (7 realizadas)

---

## Sample Data Inventory

> Samples improve LLM accuracy through in-context learning and few-shot prompting.

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Input files | N/A | 0 | Nenhum exemplo disponível — schema definido do zero |
| Output examples | N/A | 0 | N/A |
| Ground truth | N/A | 0 | N/A |
| Related code | N/A | 0 | Nenhum código anterior no projeto |

**How samples will be used:**

- N/A nesta sessão — a fase de Design deverá gerar exemplos sintéticos de payload por fonte (B3, CRM, telemetria, logs) para uso como fixtures de teste.

---

## Approaches Explored

### Approach A: Kafka Connect Sink direto pro Bronze

**Description:** Kafka Connect com Sink Connector grava continuamente do tópico direto no Bronze (landing zone). Airflow orquestra só as fontes batch e um DAG periódico de promoção/validação.

**Pros:**
- Desacopla throughput de streaming do scheduler do Airflow
- Padrão comprovado em produção

**Cons:**
- Adiciona um componente de infra extra (cluster Kafka Connect) numa conta trial
- Enfraquece a narrativa de portfólio (Airflow deixa de ser o orquestrador único visível)

---

### Approach B: Airflow Asset-aware (evento) + consumidor micro-batch ⭐ Recomendado

**Description:** Producer faz polling da brapi.dev e publica no tópico Kafka `automesh.market.b3_quotes.v1`. Um DAG do Airflow 3.0 usa `@asset`/sensor deferrable para "escutar" o tópico e consumir em micro-lote, gravando no Bronze (Delta). Fontes simuladas entram como DAGs batch separadas, convergindo no mesmo checkpoint de validação de contrato.

**Pros:**
- Todo o fluxo visível num único painel (Airflow UI) — forte para demonstração em entrevista
- Consumo em micro-lote controla custo numa conta cloud trial (nada roda continuamente)
- Usa nativamente o *asset-aware scheduling* do Airflow 3.0 (KB `airflow/quick-reference.md`)

**Cons:**
- Cadência de consumo acoplada ao intervalo do DAG (não é streaming "puro")
- Mais código customizado de producer/consumer do que usar Kafka Connect pronto

**Why Recommended:** Bate diretamente com a narrativa já existente em `context.md` ("Airflow escuta o evento via Kafka"), é a opção mais barata para uma conta cloud trial (sem cluster/job contínuo) e centraliza toda a orquestração num único painel, reforçando a mensagem de portfólio. Confiança: 0.85 (padrão de KB + evidência textual do próprio projeto, ainda sem precedente direto no código).

---

### Approach C: Spark Structured Streaming contínuo (estilo "textbook" Databricks)

**Description:** Job Databricks com Spark Structured Streaming lê do Kafka continuamente e grava no Bronze via `writeStream`. Airflow orquestra só as fontes batch.

**Pros:**
- Padrão de engenharia de streaming mais "correto"/production-grade
- Já prepara terreno para o Delta Live Tables da Fase 2

**Cons:**
- Exige cluster/job rodando continuamente — queima quota/crédito rápido numa conta trial
- Projeto já prevê um "Agente FinOps" justamente para esse tipo de custo — introduzi-lo cedo demais cria tensão com a Fase 3

---

## Data Engineering Context

### Source Systems

| Source | Type | Volume Estimate | Current Freshness |
|--------|------|-----------------|--------------------|
| brapi.dev (cotações B3) | API REST pública (real) | Baixo (poucos MB/dia, polling ~5 min) | Quase real-time (~5 min) |
| CRM "Lost Sales" | Gerador sintético (simulado) | Baixo/moderado | Diário (batch) |
| Telemetria de infra | Gerador sintético (simulado) | Moderado | Streaming (Kafka) |
| Logs de uso | Gerador sintético (simulado) | Moderado | Streaming (Kafka) |
| PDFs/contratos | Arquivos estáticos (simulado) | Baixo | Batch — só contrato de dados nesta fase |
| Transcrições de vídeo | Arquivos estáticos (simulado) | Baixo | Batch — só contrato de dados nesta fase |

### Data Flow Sketch
```text
[brapi.dev]  ─┐
[infra telemetry sim]─┤→ [Kafka topics] → [Airflow: asset/sensor micro-batch] ─┐
[usage logs sim]────┘                                                          │
                                                                                 ├→ [dag_validate_and_promote] → [Bronze Delta] → (Fase 2)
[CRM Lost Sales sim]──┐                                                        │        └→ [DLQ] → (futuro agente self-healing, Fase 2)
[PDFs/contratos sim]──┤→ [Airflow: DAGs batch] ──────────────────────────────┘
[transcrições sim]────┘
```

### Key Data Questions Explored

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Qual o volume esperado? | Baixo — projeto de portfólio, não produção real | Permite usar tiers gratuitos/trial sem preocupação de escala |
| 2 | Qual SLA de freshness é necessário? | ~5 min para B3 (quase real-time); diário para CRM | Confirma micro-batch em vez de streaming contínuo (Approach B sobre C) |
| 3 | Quem consome a saída? | Fase 2 (Bronze/Databricks); DLQ alimenta o futuro agente de self-healing | Define o contrato mínimo do Bronze e o formato da DLQ |

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach B — Airflow Asset-aware + consumidor micro-batch |
| **User Confirmation** | 2026-07-31 (confirmado no chat) |
| **Reasoning** | Alinha com a narrativa já existente no `context.md`; controla custo numa conta cloud trial (sem cluster/job contínuo); centraliza a orquestração num único painel, reforçando a mensagem de portfólio |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|----------|-----------|------------------------|
| 1 | Airflow 3.0 asset/sensor deferrable consome Kafka em micro-lote | Custo em conta trial + narrativa unificada no Airflow | Kafka Connect Sink direto (A); Spark Structured Streaming contínuo (C) |
| 2 | brapi.dev como única fonte real de dados | API dedicada à B3, gratuita, mais usada e mais "real" para este nicho específico | Yahoo Finance/yfinance (não-oficial/instável); Alpha Vantage (rate limit de 25 chamadas/dia incompatível com polling) |
| 3 | Telemetria de infra e logs de uso mantidos no escopo, mesmo sem consumidor definido ainda | Provar capacidade de ingestão multi-fonte heterogênea desde a Fase 1, como diferencial de portfólio | Cortar esses tópicos até a Fase 3 (FinOps) ter um consumidor definido |
| 4 | PDFs/contratos e transcrições de vídeo entram só como contrato de dados (schema), sem parser/OCR | Evita acoplar o design da Fase 1 à implementação da Fase 4 (RAG) | Implementar o parser/OCR já nesta fase |

---

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed | Can Add Later? |
|--------------------|------------------|------------------|
| Parser/OCR de PDFs e transcrição de vídeo | Não é responsabilidade da ingestão (Fase 1); pertence à Fase 4 (RAG) — implementá-lo agora acoplaria fases sem necessidade | Yes — no brainstorm da Fase 4 |
| Agente de self-healing consumindo a DLQ | Fora do escopo da Fase 1 — esta fase só detecta e isola erros; a correção automática é responsabilidade da Fase 2 | Yes — no brainstorm da Fase 2 |

---

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---------|-----------|-----------------|------------|
| Topologia geral (tópicos, DAGs, fontes) | ✅ | Confirmado sem ajustes ("sim") | No |
| Formato do contrato + tratamento de erro (DLQ) | ✅ | Confirmado sem ajustes ("sim") | No |

**Minimum Validations:** 2 ✅

---

## Suggested Requirements for /define

### Problem Statement (Draft)
A plataforma precisa de uma camada de ingestão unificada (Fase 1) que capture dados heterogêneos — cotações B3 reais e fontes corporativas simuladas (CRM, telemetria, logs, PDFs, vídeos) — via Kafka e Airflow, validando cada registro contra um contrato de dados antes de promovê-lo ao Bronze, isolando falhas numa DLQ sem interromper o fluxo.

### Target Users (Draft)
| User | Pain Point |
|------|------------|
| Recrutador/entrevistador avaliando o portfólio | Precisa enxergar uma arquitetura de ingestão coesa e rastreável (contratos, DLQ) num único painel |
| Autor do projeto, como operador do pipeline | Precisa rodar isso numa conta cloud trial sem estourar custo/quota |

### Success Criteria (Draft)
- [ ] Producer real publica cotações B3 (brapi.dev) no tópico `automesh.market.b3_quotes.v1` em polling de ~5 min
- [ ] Pelo menos 4 DAGs Airflow funcionais: ingestão Kafka (market + infra), ingestão batch (CRM), validação/promoção
- [ ] Cada fonte tem um contrato de dados YAML versionado, validado automaticamente antes da escrita no Bronze
- [ ] Registros inválidos são roteados para uma DLQ com o motivo da falha anexado
- [ ] Dados promovidos ficam disponíveis como tabelas Delta no Bronze, particionadas por fonte/data

### Constraints Identified
- Execução numa conta cloud trial/gratuita (ex: Confluent Cloud, Astronomer, Databricks trial) — atenção a limites de tempo/quota
- Sem orçamento para infraestrutura paga contínua
- brapi.dev tem rate limits próprios que o producer precisa respeitar

### Out of Scope (Confirmed)
- Parser/OCR de PDFs e transcrição de vídeo (Fase 4)
- Agente de self-healing / correção automática de schema (Fase 2)
- Dashboard de FinOps / dimensionamento de cluster (Fase 3)
- Motor RAG, entrega via Microsoft Graph, Human-in-the-Loop (Fases 4-5)

---

## Session Summary

| Metric | Value |
|--------|-------|
| Questions Asked | 7 |
| Approaches Explored | 3 |
| Features Removed (YAGNI) | 2 |
| Validations Completed | 2 |
| Duration | 1 sessão de chat |

---

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_FASE1_INGESTAO.md`
