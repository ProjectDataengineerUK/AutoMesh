# DEFINE: Fase 1 — Ingestão (Kafka/Airflow)

> Camada de ingestão unificada que captura cotações B3 reais e fontes corporativas simuladas via Kafka e Airflow, validando cada registro contra um contrato de dados antes de promovê-lo ao Bronze.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | FASE1_INGESTAO |
| **Date** | 2026-07-31 |
| **Author** | define-agent |
| **Status** | ✅ Shipped |
| **Clarity Score** | 14/15 |

---

## Problem Statement

A plataforma Zero-Touch Data Mesh precisa de uma camada de ingestão (Fase 1) que capture dados heterogêneos — cotações B3 reais e fontes corporativas simuladas (CRM, telemetria de infra, logs de uso, PDFs/contratos, transcrições de vídeo) — via Kafka e Airflow, validando cada registro contra um contrato de dados antes de promovê-lo ao Bronze e isolando falhas numa DLQ sem interromper o fluxo.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| Autor do projeto (Jonatas) | Operador do pipeline / autor do portfólio | Precisa de um pipeline de ingestão confiável rodando numa conta cloud trial, sem estourar custo/quota, e sem intervenção manual quando um registro é inválido |
| Recrutador/entrevistador técnico | Avaliador do portfólio | Precisa enxergar, num único painel (Airflow), uma arquitetura de ingestão coesa e rastreável — contratos de dados explícitos, tratamento de erro visível (DLQ) — que demonstre práticas de nível sênior |
| Pipeline da Fase 2 (Bronze → Silver) | Consumidor downstream | Precisa que os dados no Bronze cheguem já validados contra um schema conhecido, particionados de forma previsível, para poder auditar e processar sem re-validar do zero |

---

## Goals

What success looks like (prioritized):

| Priority | Goal |
|----------|------|
| **MUST** | Producer real publica cotações B3 (via brapi.dev) no tópico Kafka `automesh.market.b3_quotes.v1`, consumido em micro-lote e promovido ao Bronze |
| **MUST** | DAG batch ingere o CRM "Lost Sales" simulado e o promove ao Bronze pelo mesmo checkpoint de validação |
| **MUST** | Cada fonte tem um contrato de dados YAML versionado (schema, SLA, owner), validado automaticamente antes da escrita no Bronze |
| **MUST** | Registros que violam o contrato são roteados para uma DLQ com o motivo da falha anexado, sem interromper o restante do pipeline |
| **SHOULD** | Tópicos Kafka de telemetria de infra e logs de uso (simulados) são ingeridos e promovidos ao Bronze, mesmo sem consumidor definido ainda (prova de ingestão multi-fonte) |
| **SHOULD** | Contratos de dados (schema) definidos para PDFs/contratos e transcrições de vídeo, sem parser/OCR implementado nesta fase |
| **COULD** | Estratégia de particionamento do Bronze (por fonte/data) já otimizada desde a primeira versão, em vez de revisada no Design |

**Priority Guide:**
- **MUST** = MVP fails without this
- **SHOULD** = Important, but workaround exists
- **COULD** = Nice-to-have, cut first if needed

---

## Success Criteria

Measurable outcomes:

- [ ] Producer publica cotações B3 no tópico `automesh.market.b3_quotes.v1` com latência de polling ≤ 5 minutos, respeitando o rate limit da brapi.dev
- [ ] No mínimo 4 DAGs Airflow funcionais: `dag_ingest_kafka_market`, `dag_ingest_kafka_infra`, `dag_ingest_batch_crm`, `dag_validate_and_promote`
- [ ] 100% dos registros processados (válidos ou não) passam pelo `dag_validate_and_promote` — nenhum registro pula a validação de contrato
- [ ] 100% dos registros inválidos aparecem na DLQ correspondente com o motivo da falha anexado (nenhuma perda silenciosa)
- [ ] Dados válidos ficam disponíveis como tabelas Delta no Bronze, particionadas por fonte e data, em até 5 minutos (Kafka) / diariamente (batch) após a ingestão

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Happy path — cotação B3 válida | O producer B3 está rodando e publicando no tópico `automesh.market.b3_quotes.v1` | Uma nova cotação chega e passa no contrato de dados | O `dag_validate_and_promote` grava o registro na tabela Delta do Bronze em até 5 min, particionado por fonte/data |
| AT-002 | Erro de contrato — campo obrigatório nulo | Um registro (de qualquer fonte) chega com um campo `nullable: false` vazio (ex: `price` nulo) | O `dag_validate_and_promote` processa o lote | O registro é roteado para a DLQ da fonte com o motivo `null_violation` anexado, e o pipeline continua processando os demais registros normalmente |
| AT-003 | Edge case — fonte real indisponível | A API brapi.dev retorna erro/timeout durante o polling do producer | O producer tenta publicar uma nova cotação | O producer aplica retry com backoff, loga a falha, e os demais DAGs (fontes simuladas) continuam operando sem interrupção |

---

## Out of Scope

Explicitly NOT included in this feature:

- Parser/OCR de PDFs e transcrição de vídeo — apenas o contrato de dados (schema) é definido nesta fase; a implementação fica para a Fase 4 (RAG)
- Agente de self-healing / correção automática de schema — a Fase 1 apenas detecta e isola erros na DLQ; a correção automática é escopo da Fase 2
- Dashboard de FinOps / dimensionamento dinâmico de cluster — escopo da Fase 3
- Motor RAG, entrega via Microsoft Graph (Teams/Outlook), e Human-in-the-Loop — escopo das Fases 4-5
- Consumidor analítico da telemetria de infra e dos logs de uso — os tópicos e a ingestão existem nesta fase, mas nenhum agente os processa ainda

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Technical | brapi.dev tem rate limit próprio | Define o intervalo mínimo de polling do producer (~5 min); nenhuma chamada em loop apertado |
| Resource | Execução limitada a conta(s) cloud trial/gratuita (ex: Confluent Cloud, Astronomer, Databricks trial) | Reforça a escolha do Approach B (micro-batch via Airflow) em vez de streaming contínuo (Spark Structured Streaming), evitando cluster/job rodando 24/7 |
| Resource | Sem orçamento para infraestrutura paga contínua | Serviços gerenciados devem ficar dentro do free-tier/trial; escolha específica de provedor fica para o Design |

---

## Technical Context

> Essential context for Design phase - prevents misplaced files and missed infrastructure needs.

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `pipelines/ingestion/` (nova pasta — projeto ainda não tem código-fonte) | Vai conter DAGs, producers e contratos de dados |
| **KB Domains** | `airflow`, `streaming`, `controls/data-contracts`, `patterns/streaming`, `databricks`, `data-quality`, `orchestration` | Design deve consultar `airflow/quick-reference.md` (asset-aware scheduling), `streaming/quick-reference.md` (DLQ, checkpointing) e `controls/data-contracts/data-contract-baseline.md` |
| **IaC Impact** | New resources — TBD | Provisionamento de conta(s) cloud trial (Kafka gerenciado + Airflow gerenciado) ainda não decidido; Design deve escolher o provedor específico |

**Why This Matters:**

- **Location** → Design phase uses correct project structure, prevents misplaced files
- **KB Domains** → Design phase pulls correct patterns from `.claude/kb/`
- **IaC Impact** → Triggers infrastructure planning, avoids "works locally" failures

---

## Data Contract (if applicable)

### Source Inventory
| Source | Type | Volume | Freshness | Owner |
|--------|------|--------|-----------|-------|
| brapi.dev (cotações B3) | API REST pública (real) | Baixo (~poucos MB/dia, polling 5 min) | ~5 min | Projeto AutoMesh |
| CRM "Lost Sales" | Gerador sintético (simulado) | Baixo/moderado | Diário (batch) | Projeto AutoMesh |
| Telemetria de infra | Gerador sintético (simulado) | Moderado | Streaming (Kafka) | Projeto AutoMesh |
| Logs de uso | Gerador sintético (simulado) | Moderado | Streaming (Kafka) | Projeto AutoMesh |
| PDFs/contratos | Arquivos estáticos (simulado) | Baixo | Batch — schema apenas | Projeto AutoMesh |
| Transcrições de vídeo | Arquivos estáticos (simulado) | Baixo | Batch — schema apenas | Projeto AutoMesh |

### Schema Contract
Exemplo representativo (`automesh.market.b3_quotes`, v1) — os demais contratos seguem o mesmo padrão, detalhados no Design:

| Column | Type | Constraints | PII? |
|--------|------|-------------|------|
| ticker | STRING | NOT NULL | No |
| price | DECIMAL | NOT NULL | No |
| volume | LONG | Nullable | No |
| quote_timestamp | TIMESTAMP | NOT NULL | No |

### Freshness SLAs
| Layer | Target | Measurement |
|-------|--------|-------------|
| Bronze (fontes Kafka: B3, infra, logs) | Dentro de 5 minutos da publicação no tópico | Timestamp de ingestão vs. `quote_timestamp`/equivalente |
| Bronze (fontes batch: CRM, PDFs, vídeo) | Atualizado diariamente até o fim da execução do DAG | Timestamp de conclusão do DAG |

### Completeness Metrics
- 100% dos registros publicados (válidos ou não) chegam ao `dag_validate_and_promote` — nenhum registro descartado antes da validação
- 0% de perda silenciosa: todo registro inválido é rastreável na DLQ com motivo de falha

### Lineage Requirements
- Cada registro no Bronze é rastreável ao contrato de dados que o validou (nome + versão) e à fonte original (tópico Kafka ou arquivo, com timestamp de ingestão)
- Registros na DLQ preservam o payload original completo, junto do motivo da falha

---

## Assumptions

Assumptions that if wrong could invalidate the design:

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|-------------------|--------------|
| A-001 | brapi.dev permanece gratuita, estável e disponível durante o desenvolvimento do projeto | Seria necessário trocar de fonte real (ex: Yahoo Finance/yfinance ou Alpha Vantage) e re-desenhar o contrato de dados correspondente | [ ] |
| A-002 | A(s) conta(s) cloud trial escolhida(s) oferecem tempo/quota suficiente para demonstrar o pipeline fim a fim | Seria necessário migrar para execução local via Docker (approach considerado e descartado no brainstorm) | [ ] |
| A-003 | O provedor de Airflow escolhido no Design suporta Airflow 3.0 (asset-aware scheduling) | Seria necessário usar fallback com sensors clássicos (Airflow 2.x), perdendo o encaixe nativo com eventos que embasou a escolha do Approach B | [ ] |

**Note:** Validate critical assumptions before DESIGN phase. Unvalidated assumptions become risks.

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Sentença única, específica, com escopo (fontes, mecanismo de validação, isolamento de erro) herdada diretamente do brainstorm validado |
| Users | 2 | Três personas identificados com pain points claros; "recrutador" é um persona atípico para um sistema técnico, o que impede o 3 |
| Goals | 3 | MoSCoW aplicado a todos os goals, com justificativa herdada do YAGNI do brainstorm |
| Success | 3 | Todos os critérios têm números (5 min, 4 DAGs, 100%, particionamento) |
| Scope | 3 | Out of scope explícito com 5 itens, cada um mapeado para uma fase futura específica |
| **Total** | **14/15** | Acima do gate de 12/15 — pronto para Design |

**Scoring Guide:**
- 0 = Missing entirely
- 1 = Vague or incomplete
- 2 = Clear but missing details
- 3 = Crystal clear, actionable

**Minimum to proceed: 12/15**

---

## Open Questions

None — ready for Design. O Design deverá resolver a escolha específica de provedor cloud trial (Confluent Cloud vs. Astronomer vs. Databricks trial) e o formato exato dos demais contratos de dados (infra telemetry, usage logs, CRM, PDFs, vídeo), seguindo o padrão do contrato de `b3_quotes` já esboçado aqui.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-31 | define-agent | Initial version — extraído de BRAINSTORM_FASE1_INGESTAO.md |
| 1.1 | 2026-08-01 | ship-agent | Shipped and archived |

---

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_FASE1_INGESTAO.md`
