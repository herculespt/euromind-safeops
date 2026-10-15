# Política de execução e compatibilidade

<!-- safeops-version: 0.3.0a1 -->

[English](../EXECUTION.md)

Versão atual do código: **0.3.0a1**, pré-versão alfa. Este guia descreve o que está
implementado; consulta o [estado](STATUS.md) para limitações e publicações.

## Configuração

O ficheiro `.safeops/config.json` mantém o schema 1:

```json
{"schema": 1, "checks": ["compile", "unit-tests"]}
```

São aceites apenas estas duas chaves. `schema` tem de ser o inteiro 1, não um
booleano, decimal ou texto. `checks` é uma lista não vazia de nomes únicos entre
`compile` e `unit-tests`, executados pela ordem indicada. Campos desconhecidos,
nomes não suportados ou tipos inválidos produzem um erro controlado. Uma
configuração apenas com `compile` continua válida e não afirma que correu testes.

Os objetos JSON guardados são lidos em UTF-8, com BOM UTF-8 opcional e limite de
256 000 bytes. São rejeitadas chaves repetidas, números não finitos, incluindo
overflow, outras codificações e valores de topo que não sejam objetos. Uma
profundidade excessiva detetada pelo descodificador produz um erro controlado. A
configuração não permite plugins, comandos arbitrários ou uma lista de caminhos
autorizados. Os caminhos do plano são informação de âmbito, sem isolamento.

## Contrato da aprovação

Os planos mantêm o schema 1. As novas aprovações usam o schema 2 e ligam:

- ID e fingerprint do plano, snapshot do código e hash da configuração validada.
- Versão carregada do SafeOps, versão do protocolo, tabela fixa de comandos e política UTF-8, através do digest do contrato de execução.

O `doctor` apresenta a versão, o schema de aprovação e o digest atual. A contagem
recursiva de nomes de ficheiros serve apenas de diagnóstico: não importa código
dos testes nem demonstra a existência de uma suite executável.

Ao atualizar da versão 0.2.0, preserva `.safeops` e o histórico. As configurações
válidas e os planos anteriores continuam legíveis, mas as aprovações antigas
não autorizam a execução. Revê o código atual, cria um plano novo, revê-o e
aprova expressamente o novo ID. Os registos anteriores não são alterados,
apagados ou convertidos automaticamente. Não edites uma aprovação para
contornar esta regra.

Alterar a versão do pacote ou o contrato dos comandos invalida uma aprovação,
mesmo sem alterações ao projeto ou à configuração. Uma mudança de comportamento
exige atualizar a versão do pacote/protocolo. Estes registos são verificações
locais de integridade, sem assinaturas ou proteção contra um utilizador local
malicioso.

## Verificações e resultados

| Verificação | Comportamento implementado |
|---|---|
| `compile` | Comando fixo Python `compileall -q src tests`; exige os dois diretórios |
| `unit-tests` | Módulo Python interno com descoberta unittest em `tests/`, padrão `test*.py` |

A descoberta só ocorre no processo filho aprovado. São suportados pacotes de
testes aninhados, importáveis e com `__init__.py`. Uma descoberta vazia, zero
casos executados ou uma suite totalmente ignorada falham. Uma suite mista pode
passar se existirem casos não ignorados executados com sucesso; as falhas
esperadas mantêm a semântica do unittest. Erros de importação, testes falhados,
saídas inesperadas e tempos excedidos falham. Um `SystemExit(0)` normal durante
a descoberta não é aceite como sucesso.

O runner interno devolve 0 no sucesso, 1 para falhas de testes e 2 para
descoberta/execução inutilizável. O comando `safeops run` devolve código CLI 1
quando uma verificação falha; configuração inválida ou aprovação obsoleta
produzem código CLI 2. O timeout mantém o código -1 no resultado e o limite
de 1–300 segundos por verificação. O bloqueio exclusivo é libertado no fim ou
num erro controlado; um crash pode exigir recuperação manual. As verificações
falhadas são registadas na auditoria local. A saída capturada mantém UTF-8 e
é truncada no resultado devolvido.

Os testes e hooks de descoberta continuam a executar Python de confiança e
podem modificar ficheiros, terminar o interpretador por APIs de baixo nível ou
manipular resultados. O adaptador não verifica a qualidade das asserções, a
cobertura ou código hostil e não implementa isolamento seguro.

Consulta a [ADR 0002](adr/0002-versioned-check-contract.md), o
[guia de CI](CI.md) e as [referências primárias](../EXECUTION.md#design-and-references).
