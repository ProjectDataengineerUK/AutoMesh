---
source: "Lições reais — InsuranceLakehousePlatform Fases 1-4 (2026-07), SHIPPED reports"
confidence: high
validated: "2026-07-22"
---

# Playbook: Terraform Anti-Alucinação

> Protocolo para escrever Terraform **sem inventar sintaxe** quando não há acesso à
> documentação externa. Validado em 4 fases de build reais com providers
> `databricks`, `confluentinc/confluent` e recursos recém-lançados.
> Agentes: `ci-cd-specialist`, `aws-lambda-architect`, `gcp-data-architect`, `fabric-cicd-specialist`.

---

## Ferramentas em ordem de força de evidência

### 1. `terraform providers schema -json` — introspecção do provider instalado

A ferramenta mais valiosa contra alucinação: quando `terraform validate` aponta erro de
schema, a introspecção direta do provider **já instalado** dá a resposta definitiva
sem internet. Usar **proativamente** (antes de escrever o recurso), não só reativamente.

```bash
terraform providers schema -json | python3 -c "
import json,sys
s = json.load(sys.stdin)
# navegar até resource_schemas do provider/recurso em dúvida
"
```

- **Ausência de atributo no schema também é informação real**: se o recurso não expõe o
  campo, a funcionalidade genuinamente não existe via Terraform (ex.: `databricks_app`
  sem `source_code_path` gravável → deploy do código é etapa separada via CLI).

### 2. Exemplo mínimo isolado + `terraform validate`

Quando o schema JSON não decide entre duas sintaxes candidatas (bloco vs. atributo de
lista), construir um exemplo mínimo com **as duas** e rodar `terraform validate` contra
cada — elimina a dúvida antes do código final.

### 3. `terraform validate` — sinal útil, mas parcial

Confirma que nomes de bloco/atributo existem no schema; **não** confirma valores de
configuração livre (strings de `config_nonsensitive`, nomes de conector). Nunca tratar
como validação completa.

## Regras conhecidas de providers

| # | Regra |
|---|-------|
| TF1 | **Herança de provider não é implícita** em módulos filhos quando o namespace não é `hashicorp/*` — todo módulo que usa `databricks`/`confluent` precisa do próprio bloco `required_providers` (`versions.tf`). |
| TF2 | **Warnings de depreciação carregam informação real** mesmo quando o validate passa "limpo" (ex.: `databricks_sql_alert` → `databricks_alert`). Reconferir a cada validate. |
| TF3 | `databricks_grants` (plural) é **autoritativo por objeto** — ver INC-07 em `kb/databricks/patterns/known-incidents.md`. |
| TF4 | Config incerta que não pôde ser validada → marcar `TODO-VALIDAR` na linha exata (ver constituição §11), nunca apresentar como fato. |

## Disciplina de apresentação

- Quando uma conclusão técnica **contraria a preferência do usuário** (ex.: "recurso X
  não existe via Terraform"), apresentar a **evidência verificada** (saída do schema,
  erro do validate) — não a opinião do agente contra a preferência. O usuário pode
  discordar da conclusão, mas nunca ficar sem saber que o plano mudou e por quê.
