# REMEDIATION: auditoria de confiabilidade e rastreabilidade

## Metadata

| Campo | Valor |
|---|---|
| Data | 2026-08-14 |
| Status | In Progress |
| Origem | Auditoria cruzada dos ciclos SDD das Fases 1-4 contra o código atual |

## Taxonomia de status

Os artefatos do projeto passam a distinguir explicitamente:

| Status | Definição |
|---|---|
| Implemented | Código e testes automatizados existem |
| Locally Validated | O fluxo foi exercitado com serviços locais reais |
| Infrastructure Validated | O fluxo foi exercitado contra os serviços externos de destino |
| Operationally Complete | Critérios de aceitação, observabilidade e recuperação foram verificados ponta a ponta |

`Shipped` nos arquivos históricos das Fases 1-4 significa **Implemented**, salvo quando a evidência declara explicitamente um nível superior.

## Matriz de rastreabilidade consolidada

| Fase | Requisito principal | Implementação | Evidência atual | Estado real |
|---|---|---|---|---|
| 1 | Kafka/Airflow -> contrato -> Bronze/DLQ | `pipelines/ingestion/` | Redpanda, brapi.dev, Delta e DagBag reais | Locally Validated; run completa do scheduler pendente |
| 2 | Bronze -> Silver | `pipelines/processing/` | Código e testes estruturais | Implemented; Databricks pendente |
| 2 | Falha -> LLM -> guardrail -> PR | `pipelines/self_healing/` | Componentes testados com mocks | Implemented; Anthropic/GitHub ponta a ponta pendentes |
| 3 | Treino, inferência e drift | `pipelines/insights/` | MLflow SQLite e Delta locais | Locally Validated; Databricks/UC pendentes |
| 3 | FinOps | `pipelines/finops/` | Detecção unitária | Implemented; billing e metastore reais pendentes |
| 4 | SharePoint -> Vector Search | `pipelines/rag/` | Testes com mocks | Implemented; Graph/SharePoint/Vector Search pendentes |
| 4 | Retrieval -> RAGAS -> PR | `pipelines/rag/` + `pipelines/self_healing/` | Testes com mocks | Implemented; execução externa ponta a ponta pendente |

## Correções desta remediação

- [x] Não avançar o cursor Graph quando um download falha.
- [x] Avançar checkpoints pelo maior timestamp efetivamente processado, não pelo relógio ao fim da task.
- [x] Rejeitar traversal, caminhos absolutos e separadores não canônicos nos guardrails.
- [x] Validar o formato do repositório antes da automação de PR.
- [x] Adicionar configuração central de lint/teste e workflow de CI.
- [ ] Executar a suíte completa em CI e validar os DAGs com Airflow.
- [ ] Validar Fase 2 contra Databricks real.
- [ ] Validar self-healing contra repositório e credenciais de teste.
- [ ] Validar Fase 4 contra Microsoft Graph e Vector Search reais.

## Gate para a próxima fase

A próxima fase funcional pode entrar em DEFINE/DESIGN depois que os checks locais estiverem verdes. Ela não deve ser marcada como `Infrastructure Validated` sem evidência externa reproduzível.

