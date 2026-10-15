# Teste real OpenAI — 15 de outubro de 2026

[English](../../audits/2026-10-15-openai-smoke.md)

## Código e pedido testados

| Campo | Valor observado |
|---|---|
| Versão do código | `0.3.0a2`, pré-versão alfa |
| Commit | `5ff49659500005adf64cfaf12706b49a1de34b34` |
| Fornecedor | Adaptador nativo `openai` |
| Endpoint | `https://api.openai.com/v1/responses` |
| Alias do modelo pedido | `gpt-4.1-mini` |
| Registo do resultado | 15 de outubro de 2026, 11:58:17 UTC |
| Consentimento remoto | Autorização expressa do maintainer e `--allow-remote` |
| Política do pedido | `store: false`, `max_output_tokens: 500`, timeout de operação de rede de 30 segundos |
| Workspace | Diretório temporário novo, separado dos projetos privados e do código |

Tarefa pública enviada:

> Suggest one documentation check for a public Python CLI. Reply in one short sentence.

O adaptador enviou esta tarefa, a instrução fixa do sistema e os metadados do
pedido. Não foram enviados ficheiros de repositórios nem conteúdo privado do
SEND. A credencial foi criada com autorização expressa, mantida fora dos
resultados das ferramentas, Git e artefactos públicos, e fornecida pelo ambiente
do processo. Este registo não inclui credenciais nem identificadores privados da conta.

## Resultado observado

- `init`: código de saída 0.
- `plan`: código 0, um plano guardado com fornecedor `openai` e 125 caracteres de aconselhamento não vazio.
- `review`: código 0, verificando a integridade do plano guardado.
- Aprovações de execução criadas: 0. Não foram executadas verificações fixas nem o texto do modelo.
- Tempo medido na chamada de planeamento: 7,976 segundos; é uma observação, não uma garantia de latência.

Texto devolvido, preservado no idioma original:

> Verify that the CLI's usage instructions clearly describe all available commands, options, and expected input/output formats.

## Limites e estado da documentação

O resultado demonstra um pedido OpenAI nativo autenticado, texto utilizável e
fluxo local de criação/revisão do plano. Não valida Anthropic, modelos
compatíveis/locais, todas as contas/modelos OpenAI, recuperação de limites de
utilização, segurança do modelo, qualidade geral ou prontidão para produção.
Este teste da CLI não mediu tokens, custo faturado nem saldo da conta.
Regista-se o alias pedido; o adaptador não guarda o snapshot devolvido, pelo que
não é afirmada uma versão concreta do modelo.

O [catálogo oficial](https://developers.openai.com/api/docs/models/gpt-4.1-mini)
classifica o modelo como `Deprecated` (obsoleto) no momento deste registo.
A evidência preserva o pedido bem-sucedido, sem adotar um novo modelo por omissão
nem o recomendar para novas integrações. O projeto mantém a escolha explícita do ID.

Esta atualização de documentação mantém a versão 0.3.0a2 e não altera código de
execução, schemas ou contrato de aprovação. O CI normal mantém testes offline e
em loopback, sem credenciais reais nem pedidos faturáveis automáticos. Não são
publicados tags, releases ou pacotes como parte desta validação.

Consultar a [validação dos fornecedores](../PROVIDER_TESTING.md), o
[estado de implementação](../STATUS.md) e a
[issue #12](https://github.com/herculespt/euromind-safeops/issues/12).
