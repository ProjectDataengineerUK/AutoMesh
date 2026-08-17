---
source: "Incidentes reais de produção — InsuranceDataPlatform (2026-07), docs/SPECIALIST_HIRING_DOSSIER.md"
confidence: high
validated: "2026-07-22"
---

# Padrões: Incidentes Conhecidos — Databricks / Spark / Kafka

> 9 incidentes reais de produção com causa raiz e correção validada. Consultar **antes** de
> escrever código que toque nas áreas listadas — cada um custou horas de diagnóstico.
> Agentes: `databricks-spark-expert`, `spark-troubleshooter`, `spark-streaming-architect`, `ci-cd-specialist`.

---

## INC-01 — Spark Connect rejeita `.rdd.isEmpty()` sob compute serverless

- **Sintoma:** job falha/inconsistente ao checar DataFrame vazio antes de escrever.
- **Causa raiz:** Spark Connect não expõe `.rdd` como o Spark clássico — API idêntica na superfície, semântica diferente por baixo.
- **Correção:** `.isEmpty()` nativo do DataFrame em todos os pontos de escrita condicional.
- **Regra:** Spark Connect **não é drop-in** do Spark clássico. Ao migrar para serverless, auditar todo o código por `.rdd`, `sparkContext` e APIs de baixo nível ANTES de rodar.

## INC-02 — `CANNOT_DETERMINE_TYPE` ao inferir schema de coluna 100% nula

- **Sintoma:** `createDataFrame` falha quando toda uma coluna é `None`.
- **Causa raiz:** Spark Connect não infere tipo sem nenhum valor não-nulo para ancorar a inferência.
- **Correção:** schema explícito (`StructType`/DDL string) em vez de inferência.
- **Regra:** em qualquer `createDataFrame` de dados sintéticos/esparsos, schema explícito sempre.

## INC-03 — `CAST_INVALID_INPUT`: notação científica no `cast("long")`

- **Sintoma:** `"1.5895008E12"` não converte para `BIGINT` em produção.
- **Causa raiz:** `from_json` serializa inteiros grandes em `StringType` com notação científica — `cast("long")` só aceita dígitos decimais puros.
- **Correção:** `cast("double")` primeiro (aceita notação científica), depois `cast("long")`.
- **Regra:** testes unitários devem reproduzir o **formato real de serialização**, não valores idealizados — teste verde com dado irreal não prova nada.

## INC-04 — KIP-714 (client telemetry) trava conexão com Confluent Cloud

- **Sintoma:** producer trava ~6 minutos e derruba a conexão, sem erro claro.
- **Causa raiz:** requisição `GetTelemetrySubscriptions` (KIP-714) não responde contra alguns clusters Confluent Cloud.
- **Correção:** `"enable.metrics.push": False` na config do producer.

## INC-05 — Tópico Kafka novo não é auto-criado pelo cluster

- **Sintoma:** `UnknownTopicOrPartitionException` ao publicar em tópico recém-criado.
- **Causa raiz:** auto-criação de tópico desabilitada no cluster — suposição implícita do código.
- **Correção:** `AdminClient.create_topics` idempotente antes de publicar, tolerante a "already exists".
- **Regra:** nunca assumir comportamento default de infraestrutura gerenciada sem verificar.

## INC-06 — Corrida de download concorrente derruba threads produtoras

- **Sintoma:** `ChunkedEncodingError`/`EmptyDataError` em 2 de 4 fontes simultâneas.
- **Causa raiz:** threads baixando o mesmo arquivo simultaneamente — escrita não-atômica em disco.
- **Correção:** `threading.Lock` por `dest_path` + escrita em arquivo temporário + `os.replace()` atômico.
- **Regra:** N de M threads falhando ao mesmo tempo é assinatura de corrida, não coincidência.

## INC-07 — `databricks_grants` reverte silenciosamente grants de outro resource

- **Sintoma:** `terraform apply` falha repetidamente com variações de `"permissions ... are [...], but have to be [...]"`.
- **Causa raiz:** `databricks_grants` (plural) é **autoritativo por objeto** — dois resources no mesmo securable competem, cada apply revertendo o grant do outro.
- **Correção:** um único resource `databricks_grants` por securable; ou `databricks_grant` (singular, aditivo). No caso real, o grant era desnecessário (o erro real era `TABLE_OR_VIEW_NOT_FOUND`, não `PERMISSION_DENIED`).
- **Regra:** após 2-3 falhas do mesmo padrão, **parar e testar a hipótese contra o comportamento real** em vez de tentar a 4ª variação — engenharia por evidência.

## INC-08 — UC Model Registry bloqueado por *explicit deny* em bucket policy S3

- **Sintoma:** `MlflowException: AccessDenied` ao registrar versão de modelo.
- **Causa raiz:** deny explícito na bucket policy do S3 do metastore — não um grant de Unity Catalog ausente.
- **Correção (workaround reversível):** rastrear o "campeão" via tag MLflow (`model_stage=champion`) em vez de alias no Registry.
- **Regra:** deny explícito **sempre vence** allow na avaliação IAM da AWS. Distinguir pelo erro se o bloqueio é da nuvem ou do Unity Catalog.

## INC-09 — Bootstrap circular: Databricks App precisa existir antes de receber grant

- **Sintoma:** impossível conceder acesso ao service principal do app antes do primeiro deploy — ele não existe até o app ser criado.
- **Causa raiz:** cada Databricks App cria um service principal dedicado só no primeiro `bundle deploy` — dependência circular entre DAB e Terraform.
- **Correção:** bootstrap em 2 passos (deploy mínimo → apply dos grants → deploy completo).
- **Regra:** dependência circular entre duas ferramentas de deploy é uma **classe** de problema — reaplicar o padrão de bootstrap em 2 passos.
