# Diretórios das verificações fixas — 0.3.0a10

<!-- safeops-version: 0.3.0a10 -->

[English](../TARGETS.md)

O schema 2 de configuração permite selecionar os diretórios usados pelas
verificações fixas. O `init` continua a gravar o schema 1, com o comportamento
existente de `src`/`tests`. `plan --path` mantém-se consultivo e não configura alvos.

## Configuração explícita

Após a inicialização, editar `.safeops/config.json` localmente, rever o código e
a configuração e criar/rever/aprovar um plano novo antes da execução:

```json
{
  "schema": 2,
  "checks": ["compile", "unit-tests"],
  "targets": {
    "compile": ["src/demo", "tests/unit"],
    "unit-tests": ["tests/unit"]
  }
}
```

Estes diretórios têm de existir no workspace escolhido. O exemplo não os cria.
No exemplo público do projeto, podem usar-se `src` e `tests`.
O `doctor` apresenta o schema e os diretórios efetivos. A contagem de ficheiros
refere-se à raiz unittest selecionada (zero se desativada), sem importar testes
nem demonstrar que existe uma suite executável.

- São aceites exatamente `schema`, `checks` e `targets`; schema tem de ser o inteiro 2.
- Os nomes e a ordem das verificações seguem a política existente. `targets`
  contém exatamente as verificações ativas. É válida uma configuração só de
  compilação ou só de unittest.
- Cada valor é uma lista não vazia de até vinte nomes canónicos de diretórios
  relativos e portáveis: barras `/`, sem `./`, barras finais/repetidas, `.`,
  travessia, sintaxe de drive, nomes reservados ou componentes internos/gerados
  nos caminhos das raízes. Consultar a [sintaxe do âmbito](SCOPE.md); caminhos
  futuros aceites no âmbito consultivo não são alvos de execução válidos.
- As raízes de compilação não podem sobrepor-se, repetir-se ou diferir apenas
  em maiúsculas/minúsculas. Nesta versão, unittest aceita uma única raiz de
  descoberta. As duas verificações podem selecionar o mesmo diretório. São
  suportados nomes UTF-8 e raízes aninhadas.

## O que é executado

O processo principal valida as árvores sem importar testes na aprovação e na
execução, e novamente antes de cada verificação. O adaptador fixo no processo
filho repete a validação. Todos os descendentes são inspecionados, sem exclusões
silenciosas de diretórios internos/gerados. Ligações, ligações quebradas,
junctions/reparse points Windows, objetos não regulares e erros do sistema de
ficheiros falham. O limite é de 5 000 entradas descendentes por verificação,
incluindo diretórios; cada ficheiro regular selecionado tem até 12 000 000 bytes.
Se o limite for excedido, selecionar um diretório menor.

`compile` lê e compila em memória todos os ficheiros `.py` selecionados, sem os
importar nem gravar bytecode. A ausência de fontes Python é um erro. Diretórios
gerados dentro de uma raiz selecionada são incluídos. `unit-tests` usa o runner
unittest existente, com `test*.py` sob a raiz escolhida; pacotes aninhados
importáveis precisam de `__init__.py`. A raiz é a base de importação da descoberta,
preservando a semântica existente. Descoberta vazia, suites totalmente ignoradas,
erros e tempos excedidos falham. Não são aceites comandos de shell ou do modelo.

## Integridade e limites

Mantém-se o digest do workspace completo, com as exclusões existentes de
diretórios gerados. Um `targets_digest` adicional na aprovação de schema 2 liga
os caminhos e conteúdos de **todos os ficheiros regulares selecionados**,
incluindo recursos e ficheiros gerados excluídos do snapshot normal. Alterações
fora dos alvos continuam a invalidar a aprovação quando abrangidas pelo
snapshot do workspace. Alterar a configuração ou a versão exige também um plano
e aprovação novos. O histórico é preservado, sem reescrita ou migração dos registos.

Os testes podem gerar `__pycache__` ou outros ficheiros nas árvores selecionadas.
Essas alterações podem invalidar o digest numa execução posterior; revê-las e
criar novo plano/aprovação, sem editar a aprovação anterior.

Esta funcionalidade seleciona entradas de compilação/descoberta. Não limita
leituras arbitrárias, imports, hooks, escritas, arranque do interpretador ou
acesso à rede. Os testes continuam a ser código de confiança e as verificações
de metadados/conteúdo não são atómicas com a execução. A restrição imposta pelo
sistema operativo e o isolamento de código hostil permanecem planeados.
A funcionalidade e os seus testes offline não exigem pedidos a fornecedores.

Consultar a [compatibilidade](EXECUTION.md), o [estado](STATUS.md), o
[modelo de confiança](../TRUST_MODEL.md) e a [validação em CI](CI.md).
