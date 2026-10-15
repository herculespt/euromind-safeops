# ADR 0002 — Contrato fixo versionado e execução não vazia

- Estado: aceite para a versão do código 0.3.0a1
- Data: 15 de outubro de 2026
- [English](../../adr/0002-versioned-check-contract.md)

## Problema

O nome de um ficheiro não demonstra a existência de casos de teste. A descoberta
importa código executável, pelo que não deve ocorrer no processo principal antes
da aprovação. O hash da configuração, por si só, também não invalida aprovações
quando a ferramenta instalada ou os comandos fixos mudam.

## Decisão

Manter o schema 1 de configuração e planos. Validar chaves, tipos e nomes únicos
de verificações predefinidas, e ler o estado como JSON UTF-8 sem ambiguidades.
Usar aprovações schema 2 ligadas ao código, plano, configuração e contrato fixo
versionado de execução.

Substituir o comando unittest direto por um adaptador interno e fixo, baseado
na biblioteca padrão. A descoberta e execução só ocorrem no processo filho
aprovado. Suites vazias, sem casos executados ou totalmente ignoradas falham.
Preservar a tabela fixa, execução sem shell, UTF-8, bloqueio exclusivo e timeout.

Adotar a versão 0.3.0a1 para identificar a mudança de compatibilidade das
aprovações e a maturidade alfa. Preservar os registos e exigir novo plano e
aprovação expressa após a atualização, sem converter a intenção anterior.

## Consequências

Não são introduzidos acesso remoto, dependências em execução, autonomia ou
isolamento seguro. A configuração apenas com compilação mantém-se, sem afirmar
cobertura por testes. Código e hooks de confiança podem manipular o interpretador;
uma execução não vazia não certifica asserções, cobertura ou segurança. Futuras
mudanças ao runner exigem atualizar a versão, contrato e documentação.
