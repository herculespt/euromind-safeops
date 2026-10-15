# Teste real Anthropic — 15 de outubro de 2026

[English](../../audits/2026-10-15-anthropic-smoke.md)

## Código e pedido testados

| Campo | Valor observado |
|---|---|
| Versão do código | `0.3.0a2`, pré-versão alfa |
| Commit testado | `c13c2cb039565512c50a98fec2f7cb17a941d2bf` |
| Fornecedor | Adaptador nativo `anthropic` |
| Endpoint | `https://api.anthropic.com/v1/messages` |
| ID do modelo pedido | `claude-haiku-5-5` |
| Resultado registado | 15 de outubro de 2026, 13:22:49 UTC |
| Consentimento remoto | Autorização expressa do maintainer e `--allow-remote` |
| Política do pedido | `anthropic-version: 2023-06-01`, `max_tokens: 500`, timeout de operação de rede de 30 segundos |
| Workspace | Diretório temporário novo, separado do código e de projetos privados |

A Models API da conta apresentou o modelo pedido antes do teste de aconselhamento.
A credencial foi criada com autorização expressa, mantida fora do código público
e dos resultados das ferramentas, e fornecida pelo ambiente do processo. Este
registo não contém chaves, identificadores privados da conta nem dados de faturação.

Tarefa pública enviada:

> Suggest one documentation check for a public Python CLI. Reply in one short sentence.

Foram enviados apenas esta tarefa, a instrução fixa do sistema e os metadados do
pedido. Não foram enviados ficheiros de repositórios nem dados privados.

## Resultado observado

- `init`: código de saída 0.
- `plan`: código de saída 0, exatamente um plano guardado com fornecedor `anthropic` e 170 caracteres de aconselhamento não vazio.
- `review`: código de saída 0, confirmando a integridade do plano guardado.
- Aprovações de execução criadas: 0. O teste não executou verificações predefinidas nem texto do modelo.
- Tempo medido para o pedido de planeamento: 7,692 segundos; uma observação, sem garantia de latência.

Texto de aconselhamento recebido:

> Verify that the README's installation and quick-start commands run exactly as written on a clean environment, and that the `--help` output matches the documented options.

## Limites e estado da documentação

Foi verificado um pedido autenticado ao adaptador nativo Anthropic e o fluxo
local de criação/revisão do plano. Não ficam validados modelos compatíveis/locais,
todas as contas/modelos Anthropic, recuperação de limites de utilização,
qualidade geral do modelo, segurança do modelo ou preparação para produção.
É registado o ID pedido; o adaptador não guarda um snapshot devolvido do modelo
nem metadados de utilização. Este teste pela CLI não mediu tokens efetivos nem
custo faturado. O pedido OpenAI bem-sucedido mantém o seu
[registo histórico separado](2026-10-15-openai-smoke.md).

Esta atualização de documentação mantém a versão 0.3.0a2 e não altera código de
execução, schemas nem contrato de execução. O CI normal mantém testes offline e
em loopback, sem credenciais reais nem pedidos faturáveis automáticos. Esta
validação não publica tags, releases nem pacotes.

Consulta a [validação dos fornecedores](../PROVIDER_TESTING.md), o
[estado de implementação](../STATUS.md) e a
[issue #17](https://github.com/herculespt/euromind-safeops/issues/17).
