# Cobertura medida no CI — 0.3.0a17

<!-- safeops-version: 0.3.0a17 -->

[English](../COVERAGE.md)

O job existente Ubuntu/Python 3.12 mede instruções e decisões do pacote com
`coverage==7.16.2`, apenas para desenvolvimento, em `requirements-ci.txt`.
O pacote continua sem dependências externas em execução. Os outros oito jobs
da matriz e os dois com wheel instalada mantêm a suite completa sem
instrumentação. Continuam a existir doze jobs, incluindo `quality-gate`.

## Medição e gate

`pyproject.toml` seleciona todo o pacote `euromind_safeops`, medição de decisões,
instrumentação de subprocessos e ficheiros de dados separados. Não há omissão
de módulos, exclusões personalizadas de linhas nem erros de código ignorados.
Antes da suite, uma sonda separada lança a CLI num subprocesso real e exige
linhas executadas de `__main__.py`. Os dados da sonda são depois apagados, para
não aumentarem o resultado da suite. Dados/relatórios ficam em `runner.temp`.

Após a suite aprovada, o CI combina os dados, gera JSON e XML Cobertura e exige
**90% de cobertura combinada**: `(instruções cobertas + destinos de decisão
cobertos) / (todas as instruções + todos os destinos de decisão) * 100`.
Não é um mínimo de 90% para cada métrica ou módulo. Exigem-se todos os módulos
`.py` do pacote, dados de decisões, zero linhas excluídas e contagens JSON/XML
iguais. Dados ausentes/inválidos, erros de escrita, testes falhados ou cobertura
abaixo do mínimo fazem falhar o job e o gate. O resumo Markdown recebe apenas
contagens/percentagem agregadas.

A medição inicial Linux/Python 3.12 no código 0.3.0a7
(`8c7607335f966a005e3e9f438eed26bdd98be51d`, em 15 de outubro de 2026) foi:

| Métrica | Observado |
|---|---:|
| Instruções | 958 / 1 018 (94,11%) |
| Destinos de decisão | 311 / 362 (85,91%) |
| Combinada | 91,96% |
| Linhas excluídas | 0 |
| Módulos do pacote | 14 |

São observações datadas, sem garantir totais futuros iguais. A evidência da
PR/main fica na issue e nos logs do workflow. Rever lacunas antes de alterar
o mínimo; não o reduzir para esconder uma regressão.

## Repetir localmente — ambiente de confiança

Instalar o projeto editável e `python -m pip install -r requirements-ci.txt`.
Escolher um diretório temporário existente **fora do checkout**. Em PowerShell,
depois de definir `$SafeOpsReportDir` com esse diretório:

```powershell
$env:COVERAGE_FILE = Join-Path $SafeOpsReportDir "safeops-coverage"
$env:COVERAGE_RCFILE = Join-Path (Get-Location) "pyproject.toml"
python -m coverage erase
python -m coverage run -m euromind_safeops.ci_runner --tests tests --summary "$SafeOpsReportDir/summary.md" --junit "$SafeOpsReportDir/junit.xml"
python -m coverage combine --quiet
python -m coverage json -o "$SafeOpsReportDir/coverage.json"
python -m coverage xml -o "$SafeOpsReportDir/coverage.xml"
python -m coverage report
```

A sonda e validações exatas constam do [CI](../../.github/workflows/ci.yml).
`coverage erase` remove os dados da medição escolhida; usar um destino dedicado.
As regras Git ignore não excluem por si ficheiros gerados dos snapshots SafeOps.
Criar/rever/aprovar o plano novo após terminar as alterações do código. As
verificações aprovadas normais não instalam nem iniciam cobertura por si.

## Limites e referências oficiais

A cobertura regista execução, sem provar asserções úteis, segurança ou
isolamento. Este perfil não estabelece cobertura de Windows/macOS/outros
Python, fornecedores reais ou distribuições instaladas. Morte abrupta,
`os._exit`, hooks desativados e ambientes de subprocessos alterados podem perder
dados. A instrumentação é limitada ao perfil de desenvolvimento e não substitui
os testes normais das plataformas.

JSON/XML e dados brutos podem conter caminhos, números de linhas e datas.
Ficam no runner e são distintos do [JUnit com casos sintéticos](REPORTING.md).
Esta funcionalidade não configura uploads, assinatura nem publicação de
relatórios. Outros perfis e uploads após revisão continuam planeados.

- [Configuração oficial](https://coverage.readthedocs.io/en/7.16.2/config.html)
- [Medição oficial de processos](https://coverage.readthedocs.io/en/7.16.2/subprocess.html)
- [Pacote/versão Coverage.py](https://pypi.org/project/coverage/7.16.2/)
- [Contrato CI](CI.md) e [aprovações de execução](EXECUTION.md)

No CI, os relatórios usam `package-coverage.json` e `package-coverage.xml`,
distintos do prefixo de dados `safeops-coverage`. Assim, a combinação automática
do suporte a subprocessos não trata relatórios como bases de dados paralelas.
