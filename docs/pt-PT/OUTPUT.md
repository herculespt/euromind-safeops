# Saída estruturada da CLI — 0.3.0a16

<!-- safeops-version: 0.3.0a16 -->

[English](../OUTPUT.md)

Usar a opção global `--json` **antes do comando** para obter um contrato comum.
Colocá-la primeiro nas invocações de automatização. Mantém-se a saída predefinida:
duas linhas de texto no `init` bem-sucedido, dados JSON sem envelope nos restantes
comandos e diagnóstico em stderr nos erros tratados.

```powershell
safeops --json --root examples/demo_project init
safeops --json --root examples/demo_project doctor
safeops --json --root examples/demo_project plan "Rever a documentação pública"
```

Inicializar uma única vez; repetir a inicialização é um erro. Não usar
`doctor --json`: a opção fica antes de `doctor`. Uma tarefa após `plan --` pode
conter literalmente `--json` sem ativar o modo global.

## Envelope de schema 1

Os vinte comandos (`init`, `providers`, `doctor`, `scan`, `plan`, `review`,
`approve`, `run`, `recover-lock`, `preview`, `propose`, `review-proposal`, `stage-proposal`, `inspect-stage`, `review-stage`, `inspect-run`, `review-application`, `apply-stage`, `inspect-application`, `rollback-application`) devolvem um único objeto JSON UTF-8 nos resultados tratados:

```json
{
  "schema": 1,
  "safeops_version": "0.3.0a16",
  "command": "scan",
  "ok": true,
  "exit_code": 0,
  "data": {
    "findings": [],
    "count": 0,
    "note": "Pattern checks are not a full security audit"
  },
  "error": null,
  "warnings": []
}
```

| Campo | Significado |
|---|---|
| `schema` | Versão inteira 1 do envelope, independente dos schemas de configuração/plano/aprovação |
| `safeops_version` | Versão instalada do código/pacote |
| `command` | Comando interpretado, ou `null` num erro dos argumentos |
| `ok` | Indica código de saída zero; não é aprovação de execução nem garantia de segurança |
| `exit_code` | Código efetivo do processo: 0, 1 ou 2 |
| `data` | Resultado original; no `init`, localização do estado e configuração inicial; `null` nos erros operacionais/de utilização tratados |
| `error` | `null` ou objeto com `code` e `message` |
| `warnings` | Lista de textos; inclui o aviso de política dos planos críticos |

O código 1 indica resultados do scanner, execuções aprovadas failed/timed-out/changed-inputs/incomplete ou inspeção de cópia alterada/incompleta.
Esses resultados mantêm `data`, com `ok: false` e `error: null`. O código 2 indica
erros tratados de utilização/política/sistema de ficheiros. Os códigos do erro
são `invalid_arguments`, `policy_error` e `filesystem_error`. Os erros dos
argumentos usam texto genérico, sem repetir os valores; os do sistema de ficheiros
omitem os detalhes brutos do SO. Mantêm-se as mensagens controladas da política
e dos fornecedores. Argumentos inválidos passam a devolver 2 de `main`, em vez
de lançar o `SystemExit` de erro do argparse a quem chama a função.

Os avisos/erros tratados não são também escritos em stderr no modo JSON. Um
plano crítico pode ser guardado com código 0 e `ok: true`; o risco e aviso
continuam a impedir a aprovação. Verificar `data`, `warnings` e o código do
processo; `ok` não concede permissão para executar código.

`--help` e `--version` mantêm a saída textual, mesmo com `--json`. O contrato
abrange opções documentadas por extenso e resultados tratados, não erros
inesperados, processos terminados à força, pipes fechados ou falhas do arranque
do interpretador. O modo JSON reconhecido configura stdout em UTF-8. Quem chama
Python e redireciona stdout para um stream próprio gere a respetiva codificação.

## Privacidade e compatibilidade

O estado dos fornecedores não inclui valores das credenciais. Os resultados
podem conter tarefas, aconselhamento, razões de aprovação, caminhos locais e
saída capturada das verificações de confiança. Tratar JSON guardado como
potencialmente sensível. Não é um serviço adicional de remoção de dados, uma
assinatura, autorização automática ou isolamento. A funcionalidade e os testes
offline não exigem pedidos a fornecedores.

A versão 0.3.0a16 preserva os schemas 1/2 de configuração, 1 de plano e 2 de
aprovação; o protocolo 5 do runner usa protocolo 3 do bloqueio nativo. A ligação à versão continua a invalidar
aprovações anteriores: preservar o histórico e criar novo plano revisto e
aprovação. Não há migração automática nem publicação de release ou pacote.

`doctor.data.run_lock` acrescenta diagnóstico momentâneo da guarda/marcador.
`recover-lock` usa o mesmo envelope e exige [confirmações explícitas](LOCKING.md).
Uma recuperação pode falhar após o arquivo: rever recibo/arquivo e `doctor`
antes de repetir. Nunca concede aprovação de execução.

## Resumos do CI

O adaptador de manutenção `python -m euromind_safeops.ci_runner --tests tests`
usa o mesmo unittest que falha de forma conservadora nas verificações aprovadas.
Exige `GITHUB_STEP_SUMMARY` ou `--summary CAMINHO` expresso. Acrescenta Markdown
UTF-8 com contagens de testes descobertos/executados/falhados/com erro/ignorados,
falhas esperadas, sucessos inesperados, fase e código de saída. A contagem de
execução inclui testes ignorados.

Suites vazias ou totalmente ignoradas e falhas de descoberta/execução não passam.
Falhar a escrita do resumo produz código 2. Uma exceção tratada que interrompa
a descoberta/execução identifica a fase incompleta; as contagens podem estar
incompletas. O resumo contém apenas totais e metadados fixos; nomes, mensagens e
conteúdos dos testes ficam nos logs normais. Isto não remove dados desses logs
nem prova cobertura, qualidade das asserções ou isolamento. Uma terminação
forçada pode impedir o resumo. `--junit CAMINHO` opcional escreve XML local com
casos sintéticos por resultado; ver [contrato JUnit](REPORTING.md). Erros de escrita
produzem código 2; o relatório descreve o resultado dos testes, que pode diferir
do código final do adaptador. A [cobertura medida](COVERAGE.md) existe no perfil
Linux/Python 3.12; outros perfis e upload permanecem planeados.

A matriz dos nove ambientes e os dois jobs com wheel instalada usam o adaptador.
Mantêm-se `quality-gate` e as permissões. Consultar o [CI](CI.md), a
[execução](EXECUTION.md) e o [estado](STATUS.md).

[Previews de candidatos](PREVIEW.md) usam este envelope; diffs contêm texto local potencialmente sensível. Um preview aprovado não autoriza execução.

A [criação/revisão de propostas](PROPOSALS.md) usa o mesmo envelope. A criação devolve identificadores/hashes sem o texto; a revisão inclui os diffs completos. O sucesso não aprova execução nem aplicação.

A [preparação da cópia](STAGING.md) devolve IDs, caminho, fingerprint do recibo e contagens, sem texto dos ficheiros. Após criar o diretório, os erros identificam o estado retido; uma falha de auditoria pode deixar recibo pronto mesmo com código 2. Inspeciona antes de repetir.

`inspect-stage` devolve `matching` (0), `changed` (1) ou `incomplete` (1), sem
texto/diffs, escrita ou evento de auditoria. Os caminhos em falta/novos/alterados
são relativos e ordenados. Versão e origem históricas não renovam aprovação;
consulta o [contrato](STAGING.md). Evidência inválida/insegura/excessiva/ilegível
ou alterada durante a inspeção devolve erro genérico de política (2).

`review-stage` usa o mesmo envelope: `current` (0), `stale` (1) ou `incompatible` (1), sem texto dos ficheiros/escrita/aprovação. Evidência inválida/insegura devolve erro de política saneado (2). Consulta [a revisão do original](STAGE_REVIEW.md) para verificações booleanas, códigos fixos e limites. A saída 1 inclui também esta revisão desatualizada/incompatível.

`run` acrescenta `run_id`, `receipt_fingerprint` e `reasons` fixos. `run`/`inspect-run` utilizam passed (0), failed/timed-out/changed-inputs/incomplete (1); erros operacionais/de integridade utilizam 2. A inspeção histórica não devolve output capturado nem revalida o original atual e nunca renova aprovação. Consulta [recibos](RUN_RECEIPTS.md), incluindo persistência parcial e falhas de auditoria.

`review-application` devolve metadados e `fingerprint` atual exato sem escrita. `apply-stage`/`rollback-application` devolvem inspeção após conclusão normal (0); falhas tratadas usam 2 e podem reter original parcialmente alterado, marcador próprio ou conclusão. Inspecionar sempre o estado. `inspect-application` usa `applied`/`rolled-back` (0), `pending`/`conflicted` (1), evidência insegura/inválida/alterada (2); devolve metadados/estados por ficheiro e `rollback_fingerprint` novo, sem texto. Consulta [estados e limites](APPLICATION.md).

O código 0.3.0a16 acrescenta [supervisão dos processos próprios](SUPERVISION.md): launcher bloqueado à entrada, grupo/âncora PID POSIX ou job Windows com kill-on-close, confirmação nativa e caudas de output drenadas continuamente com limite. Timeout inclui descendentes normais próprios e pipes retidos; limpeza incerta mantém run.lock e intent incompleto sem recibo final. Runner 5/lock 3 exigem aprovação nova ligada à versão. Abrange descendentes cooperantes no grupo POSIX/membros do job, sem conter escapes deliberados de grupo/sessão, isolar código hostil ou decidir recuperação automática. O guia define conclusão, timeout, cancelamento e morte abrupta do principal.
