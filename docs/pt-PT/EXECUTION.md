# Política de execução e compatibilidade

<!-- safeops-version: 0.3.0a7 -->

[English](../EXECUTION.md)

Versão atual do código: **0.3.0a7**, pré-versão alfa. Este guia descreve o que está
implementado; consulta o [estado](STATUS.md) para limitações e publicações.

## Configuração

O `init` mantém por predefinição o schema 1 em `.safeops/config.json`:

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
configuração opcional de schema 2 acrescenta [diretórios das verificações](TARGETS.md),
preservando o schema 1. Não permite plugins, comandos arbitrários ou isolamento
imposto pelo sistema operativo. Os caminhos do plano são informação de âmbito, sem isolamento.

O schema 2 aceita exatamente `schema`, `checks` e `targets`; o mapa de alvos
contém exatamente as verificações ativas. As árvores são validadas sem imports
antes da aprovação/execução e novamente no processo filho. O [guia dos alvos](TARGETS.md)
inclui exemplo JSON, limites e compatibilidade.

## Saída e relatórios do CI

A versão 0.3.0a5 introduziu envelopes `--json` opcionais e resumos agregados do
CI; consultar o [contrato da saída](OUTPUT.md). A apresentação não altera a
autoridade de aprovação. Mantêm-se os schemas 1/2 de configuração, 1 de plano,
2 de aprovação; a versão atual usa protocolo 3 do runner e 1 do bloqueio.
A mudança de versão exige plano/aprovação novos, preservando o histórico. Argumentos inválidos devolvem agora 2 de `main` em
Python; o código do processo mantém-se 2. Ajuda/versão continuam textuais.

## Validação prévia dos caminhos

A versão 0.3.0a3 valida e normaliza os caminhos declarados antes do fornecedor e
da gravação, e volta a verificá-los antes da aprovação/execução. Os planos
históricos continuam disponíveis para revisão; âmbitos inseguros não autorizam
verificações. `--path` não reduz o digest do workspace nem os alvos dos comandos
fixos. A [política de âmbito](SCOPE.md) descreve sintaxe, ficheiros futuros,
ligações e limitações de concorrência.

## Contrato da aprovação

Os planos mantêm o schema 1. As novas aprovações usam o schema 2 e ligam:

- ID e fingerprint do plano, snapshot do código e hash da configuração validada.
- Versão carregada, protocolo do runner/bloqueio nativo, tabela fixa de comandos/adaptador e política UTF-8, através do digest do contrato de execução.
- Na configuração de schema 2, um `targets_digest` adicional de todos os ficheiros regulares selecionados, incluindo exclusões do snapshot normal.

O `doctor` apresenta a versão, o schema de configuração, os diretórios efetivos,
o schema de aprovação e o digest atual. A contagem
recursiva de nomes de ficheiros serve apenas de diagnóstico: não importa código
dos testes nem demonstra a existência de uma suite executável.

Ao atualizar da versão 0.2.0, preserva `.safeops` e o histórico. As configurações
válidas e os planos anteriores continuam legíveis, mas as aprovações antigas
não autorizam a execução. Revê o código atual, cria um plano novo, revê-o e
aprova expressamente o novo ID. Os registos anteriores não são alterados,
apagados ou convertidos automaticamente. Não edites uma aprovação para
contornar esta regra.

Atualizar de 0.3.0a1 para 0.3.0a2 também exige novo plano e aprovação, porque o
contrato existente liga a versão do pacote. Os schemas de configuração/plano 1
e aprovação 2 não mudam nesta atualização da validação dos fornecedores.

Atualizar de 0.3.0a2 para 0.3.0a3 também exige um novo plano e aprovação pela
ligação à versão. Mantêm-se os schemas 1 de configuração/planos e 2 de aprovação.
As formas de caminho agora não suportadas falham antes do fornecedor; os
registos antigos continuam disponíveis para revisão, sem serem reescritos.

Atualizar para 0.3.0a4 exige novo plano/aprovação (protocolo do runner 2).
Mantém-se a configuração de schema 1; optar pelo schema 2 exige `targets_digest`
na aprovação. Mantêm-se os schemas 1 de plano e 2 de aprovação. Caches geradas
nas árvores selecionadas podem invalidar execuções posteriores; rever e criar
novo plano/aprovação.

Atualizar para 0.3.0a6 exige novo plano/aprovação: protocolo 3 do runner e 1 do
bloqueio nativo local. Marcadores antigos/desconhecidos continuam a bloquear;
usar [diagnóstico e recuperação por arquivo](LOCKING.md) apenas após verificar
que os processos principais e filhos terminaram. Nunca apagar a guarda persistente.

A versão 0.3.0a7 acrescenta [JUnit opcional de manutenção](REPORTING.md), mantendo
protocolos 3 do runner e 1 do bloqueio. A ligação à versão exige novo plano e
aprovação revistos. As verificações aprovadas não geram JUnit.

Alterar a versão do pacote ou o contrato dos comandos invalida uma aprovação,
mesmo sem alterações ao projeto ou à configuração. Uma mudança de comportamento
exige atualizar a versão do pacote/protocolo. Estes registos são verificações
locais de integridade, sem assinaturas ou proteção contra um utilizador local
malicioso.

## Verificações e resultados

| Verificação | Configuração schema 1 | Configuração schema 2 |
|---|---|---|
| `compile` | `compileall -q src tests`; exige os dois diretórios | Adaptador fixo compila os `.py` selecionados em memória, sem imports ou escrita de bytecode |
| `unit-tests` | Runner interno em `tests/`, padrão `test*.py` | Mesmo runner sob um único diretório expressamente selecionado |

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
de 1–300 segundos por verificação. A guarda nativa persistente abrange validação
de aprovação/configuração/snapshots e as verificações. O fim/erro normal remove apenas o marcador próprio
e inalterado; a morte abrupta liberta o bloqueio nativo, mas retém o marcador.
O [guia do bloqueio](LOCKING.md) descreve diagnóstico, recuperação, estado antigo
e limites. As verificações falhadas são registadas na auditoria local. A saída capturada mantém UTF-8 e
é truncada no resultado devolvido.

Os testes e hooks de descoberta continuam a executar Python de confiança e
podem modificar ficheiros, terminar o interpretador por APIs de baixo nível ou
manipular resultados. O adaptador não verifica a qualidade das asserções, a
cobertura ou código hostil e não implementa isolamento seguro.

Consulta a [ADR 0002](adr/0002-versioned-check-contract.md), o
[guia de CI](CI.md) e as [referências primárias](../EXECUTION.md#design-and-references).
