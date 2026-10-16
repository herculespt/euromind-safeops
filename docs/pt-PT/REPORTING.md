# Relatórios JUnit locais — 0.3.0a16

<!-- safeops-version: 0.3.0a16 -->

[English](../REPORTING.md)

O adaptador CI de manutenção pode gerar XML mínimo do tipo JUnit apenas com a
biblioteca padrão. É uma funcionalidade local, separada das verificações
aprovadas de `safeops run`. Executar apenas testes Python de confiança.

```powershell
python -m euromind_safeops.ci_runner --tests tests --summary summary.md --junit results.xml
```

Continua a ser obrigatório `--summary` ou `GITHUB_STEP_SUMMARY`. `--junit` é
opcional, sem valor predefinido pelo ambiente. O diretório de destino tem de
existir. O XML é substituído, não acrescentado: escreve-se um temporário no mesmo
diretório, descarregam-se os dados e substitui-se o destino atomicamente. Erros
normais tratados limpam o temporário; uma terminação forçada pode deixá-lo. Se
falhar a substituição, o XML anterior é preservado. Resumo e XML devem ter destinos
diferentes; aliases de caminho/hard links detetados são rejeitados antes da
descoberta. Os caminhos são escolhidos pelo operador de confiança; isto não é uma
política de acesso nem proteção contra substituição concorrente dos caminhos.

## Contrato do relatório — schema 1

A raiz `testsuites` contém uma `testsuite` chamada `safeops-unittest`. Ambas têm
contagens `tests`, `failures`, `errors` e `skipped`, calculadas pelos casos emitidos.
As propriedades são `safeops_version`, `report_schema` (`1`), `phase` (discovery,
execution ou completed) e `check_exit_code`. Os casos usam a classe fixa
`safeops.unittest` e nomes sequenciais `case-1`, `case-2`, etc. São eventos de
resultado numerados, sem identidade estável dos testes nem localização no código.
Não são exportados tempos, datas, nomes de máquinas ou propriedades personalizadas.
Este formato mínimo não tem certificação de consumidores específicos.

| Resultado observado | Representação XML |
|---|---|
| Teste aprovado | Caso sem elemento de resultado |
| Asserção falhada / erro | `failure type="failure"` / `error type="error"` |
| Teste ou fixture ignorado | `skipped type="skipped"` |
| Falha esperada | `skipped type="expected-failure"` |
| Sucesso inesperado | `failure type="unexpected-success"` |
| Subteste falhado/com erro | Um caso failure/error por subteste sem sucesso reportado |
| Subtestes aprovados | Sem casos separados; unittest reporta o teste principal aprovado |
| Erro de preparação/limpeza da fixture | Caso error, mesmo sem executar métodos |
| Verificação com código 2 | Caso adicional `error type="runner-error"` |

Várias falhas de subtestes, fixtures e erros do runner podem produzir totais XML
diferentes das contagens unittest de métodos executados/descobertos no resumo
Markdown. Falhas esperadas são skipped no XML, mantendo a contagem própria no
resumo. Suites vazias, totalmente ignoradas, inutilizáveis ou interrompidas por
exceções tratadas não surgem como XML vazio aprovado. Numa interrupção tratada,
preservam-se os resultados já observados; os contadores do resumo podem estar
incompletos e a fase assinala-o.

## Código de saída, privacidade e CI

Mantêm-se os códigos 0 (suite utilizável aprovada), 1 (falha de testes) e 2
(suite inutilizável/incompleta). O XML regista esse resultado. Falhar a escrita
do XML ou resumo faz o adaptador sair com 2; o XML pode descrever testes aprovados
quando o adaptador falhou a escrita do resumo. Um erro de escrita XML é também
registado no resumo quando este pode ser escrito. O XML isolado não substitui o
gate; um ficheiro existente pode pertencer à tentativa anterior. Erros de uso ou
terminação não tratada do processo/interpretador podem impedir o relatório.

O XML recebe apenas categorias fixas, versão e metadados numéricos. Exclui nomes
dos testes, parâmetros, motivos de skip, mensagens, exceções, tracebacks,
stdout/stderr e variáveis de ambiente. Os logs normais continuam a receber saída
dos testes, potencialmente sensível. Os casos sintéticos exigem consultar esses
logs para localizar falhas. Isto não remove dados dos logs nem isola testes
maliciosos, que podem modificar o próprio processo e os ficheiros.

Os nove jobs da matriz e os dois com wheel instalada geram XML em `runner.temp`
e analisam contagens, versão e estado concluído aprovado. Os relatórios ficam no
runner; não existe upload, inclusão nos pacotes nem publicação de relatórios.
Mantém-se `quality-gate`. A [cobertura medida](COVERAGE.md) está implementada em
Linux/Python 3.12; outros perfis e publicação de artefactos após revisão continuam
planeados. Não são feitos pedidos a fornecedores.

Consultar [CI](CI.md), [saída estruturada](OUTPUT.md),
[compatibilidade de execução](EXECUTION.md) e [estado](STATUS.md).
