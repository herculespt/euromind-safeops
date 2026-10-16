# Caminhos de âmbito consultivo — 0.3.0a9

<!-- safeops-version: 0.3.0a9 -->

[English](../SCOPE.md)

`plan --path` descreve o âmbito consultivo. A versão 0.3.0a3 valida-o antes de
contactar o fornecedor e de guardar o plano, voltando a verificar as declarações
na aprovação e na execução. Um caminho inválido na validação inicial produz
código CLI 2, sem contactar o fornecedor nem guardar o plano. A regra também
se aplica ao planeamento offline.

## Declarações aceites

- Zero a vinte caminhos, relativos ao workspace escolhido expressamente.
- Barras `/` em todas as plataformas: `src/demo/calc.py`, `docs/novo.md`.
- Nomes UTF-8, ficheiros regulares, diretórios e ficheiros ainda não criados.
- `.` representa a raiz do workspace; uma lista vazia omite as declarações.
- Os planos novos normalizam `./`, barras repetidas e separadores finais.
  Declarações duplicadas após normalização são rejeitadas.

Inicializar o exemplo público uma única vez e criar um plano:

```powershell
safeops --root examples/demo_project init
safeops --root examples/demo_project plan "Rever a documentação do exemplo" --path README.md
```

## Declarações rejeitadas

- Caminhos absolutos, relativos a uma drive, UNC ou com `..`, incluindo `a/../b`.
- Barras invertidas, caracteres de controlo ASCII e pontuação especial Windows
  (`:`, `<`, `>`, `"`, `|`, `?`, `*`), nomes reservados de dispositivos e componentes
  terminados em espaço ou ponto. `--root` mantém a sintaxe normal da plataforma.
- Componentes internos/gerados já excluídos dos snapshots, comparados sem
  distinguir maiúsculas de minúsculas: `.git`, `.safeops`, `.venv`, `venv`,
  `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.tox`, `node_modules`, `dist`, `build`.
  Nomes normais como `.safeops-guide.md` não são componentes internos.
- Ligações existentes ou quebradas, junctions Windows e outros reparse points
  no caminho declarado ou nos seus antecessores; objetos não regulares como
  pipes; antecessores que não sejam diretórios e erros de inspeção do sistema de ficheiros.

São permitidos descendentes inexistentes após a inspeção dos antecessores que
existam. O caminho resolvido tem de permanecer dentro da raiz escolhida. A
validação lê metadados, não conteúdos, e não importa testes. As verificações
repetem-se nas etapas indicadas, mas não são atómicas com o acesso posterior
ao fornecedor nem com a execução.

## Compatibilidade e limites

A configuração de schema 1 continua predefinida; o schema 2 opcional seleciona
[diretórios das verificações](TARGETS.md). Mantêm-se os schemas 1 de plano e 2
de aprovação. A atualização para 0.3.0a4 invalida as aprovações anteriores pela ligação à versão: preservar
o histórico e criar um plano revisto e uma nova aprovação expressa. O comando
`review` continua a permitir consultar planos antigos, incluindo aqueles cujos
caminhos já não cumprem a política atual de aprovação/execução.

Esta validação não implementa uma lista de caminhos autorizados nem isolamento
seguro. Os snapshots continuam a abranger o workspace; as verificações fixas
do schema 1 operam em `src` e `tests`; o schema 2 opcional seleciona
[diretórios das verificações](TARGETS.md), independentemente de `--path`. Não são
inspecionados recursivamente todos os descendentes de um diretório declarado.
Mantêm-se as exclusões dos snapshots e os riscos de concorrência; os testes de
confiança podem aceder a outros ficheiros ou à rede. A restrição de leituras arbitrárias imposta pelo sistema operativo
continua [planeada](../../ROADMAP.md).

Os testes de regressão em `tests/test_scope.py` usam fornecedores simulados.
O CI Windows testa uma junction real; o CI POSIX testa um pipe com nome. Os
registos dos fornecedores reais mantêm a versão testada 0.3.0a2; esta alteração
não efetua pedidos faturáveis adicionais.

Consulta a [compatibilidade de execução](EXECUTION.md), o [estado](STATUS.md) e as
[referências primárias](../SCOPE.md#compatibility-and-limits).
