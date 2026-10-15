# Validação dos fornecedores e procedimento de teste real

<!-- safeops-version: 0.3.0a5 -->

[English](../PROVIDER_TESTING.md)

Versão atual do código: **0.3.0a5**, pré-versão alfa. Este registo inclui
pedidos reais separados OpenAI e Anthropic verificados, sem afirmar publicação
de release ou validação universal de fornecedores/modelos.

Os registos reais abaixo mantêm a versão testada 0.3.0a2. A saída/relatórios da
versão atual 0.3.0a5, a seleção de diretórios e a admissão prévia de caminhos
são validados offline, sem novo pedido faturável.

## Evidência — 15 de outubro de 2026

| Camada | Verificado | Limite |
|---|---|---|
| Admissão do âmbito (0.3.0a3) | Caminhos inválidos não invocam o fornecedor; caminhos válidos/futuros são guardados; ligações alteradas falham nova validação | Fornecedores simulados; sem allowlist ou isolamento seguro |
| Contratos OpenAI/Anthropic | Origens fixas, cabeçalhos de autenticação, serialização e blocos de texto | Transporte simulado; sem ligação aos fornecedores |
| Falhas de transporte | HTTP 401/429/500, erros de URL, timeout, formatos inválidos e erros sem detalhes sensíveis | Respostas fixas e testes offline |
| JSON e limites | UTF-8/BOM, chaves repetidas, números não finitos, codificação inválida, limite de 256 000 bytes e aconselhamento de 6 000 caracteres | Objetos válidos suportados; descodificador comum ao estado local |
| Integração HTTP compatível | POST real em 127.0.0.1, gravação de plano pela CLI, texto português, sem envio de código nem aprovação automática | Servidor local de teste; sem inferência |
| Redirecionamentos | Respostas reais 301/302/303/307/308; o destino não recebe pedidos | Apenas servidores locais de teste |
| Inferência real OpenAI | **Aprovada: `gpt-4.1-mini`, 15 de outubro de 2026** | Versão testada 0.3.0a2; plano guardado/revisto; consultar [evidência datada](audits/2026-10-15-openai-smoke.md) |
| Inferência real Anthropic | **Aprovada: `claude-haiku-5-5`, 15 de outubro de 2026** | Versão testada 0.3.0a2; plano guardado/revisto; consultar [evidência datada](audits/2026-10-15-anthropic-smoke.md) |
| Inferência real de modelos compatíveis/locais | **Pendente** | Não é afirmada validação real desses endpoints/modelos |

O servidor compatível devolve texto predefinido; não é um modelo de IA. Os testes
do CI não validam autenticação real, qualidade, faturação, recuperação de limites
de utilização ou compatibilidade universal. Os testes separados OpenAI e Anthropic
verificam, cada um, autenticação e texto utilizável para um pedido/conta/modelo,
sem estabelecer as restantes propriedades. `safeops providers` indica a presença
das chaves nos adaptadores nativos. No compatível,
`configured: true` indica disponibilidade do adaptador, sem validar endpoint.
Nenhum destes indicadores comprova conectividade ou saúde do modelo.

A suite completa corre nos nove ambientes Python/SO do CI e contra wheels
construídas com a versão mínima e a mais recente do backend. A integração exige
`quality-gate`. Para repetir os testes locais sem acesso externo:

```bash
python -m unittest discover -s tests -p test_provider_transport.py -v
python -m unittest discover -s tests -v
```

O teste OpenAI consta da [issue #12](https://github.com/herculespt/euromind-safeops/issues/12) e do [registo datado](audits/2026-10-15-openai-smoke.md). O teste Anthropic consta da [issue #17](https://github.com/herculespt/euromind-safeops/issues/17) e do [registo datado](audits/2026-10-15-anthropic-smoke.md). Cada registo preserva commit, tarefa, ID do modelo pedido e resultado. Endpoints compatíveis/locais e compatibilidade alargada de contas/modelos continuam a exigir trabalho próprio.

## Repetir o teste com modelo real — manual e expresso

1. Instalar o código ou a wheel revistos. Fornecer a credencial do fornecedor por
   injeção segura no ambiente ou gestor de segredos. Nunca colocar chaves no chat,
   issues, comandos guardados em Git, capturas de ecrã ou resultados de testes.
2. Selecionar um ID de modelo suportado pela conta, ou configurar um endpoint
   compatível de confiança com modelo local. Uma subscrição de chat não garante
   acesso à API. Um pedido real pode ter custo; não o ativar no CI normal.
3. Usar um workspace temporário novo e a única tarefa pública abaixo. São
   enviados apenas o texto da tarefa e metadados fixos, sem conteúdo privado.
4. Verificar o código de saída e o plano através de `safeops review ID_DO_PLANO`.
   Um sucesso demonstra texto utilizável nesse pedido/modelo. Não aprovar planos,
   executar verificações nem executar o texto do modelo automaticamente neste teste.
5. Registar versão/commit, data, fornecedor/modelo, código de saída e resultado,
   sem credenciais ou informação sensível. Atualizar esta tabela, estado,
   roadmap e issue após verificar. Sem acesso ou resposta utilizável, manter pendente.

PowerShell, depois de configurar `OPENAI_API_KEY` de forma segura:

```powershell
$SafeOpsTestModel = Read-Host "ID do modelo da API"
$SafeOpsTestRoot = Join-Path $env:TEMP ("safeops-live-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $SafeOpsTestRoot | Out-Null
safeops --root $SafeOpsTestRoot init
safeops --root $SafeOpsTestRoot plan "Suggest one documentation check for a public Python CLI." `
  --provider openai --model $SafeOpsTestModel --allow-remote --provider-timeout 30
# Verificar $LASTEXITCODE e o ID apresentado; rever o plano sem o aprovar.
```

Para Anthropic, usar `--provider anthropic` e `ANTHROPIC_API_KEY`. Para um modelo
local, usar `--provider openai-compatible --endpoint ENDPOINT_DE_CONFIANÇA`
e o ID real do modelo, opcionalmente com `SAFEOPS_API_KEY`. As origens nativas
não podem ser substituídas. Consulta a [configuração](PROVIDERS.md). O timeout
limita operações de rede, não garante um prazo total. Não existem tentativas
ou mudanças de fornecedor automáticas.

## Compatibilidade e referências

A versão 0.3.0a2 introduziu a leitura estrita das respostas; a 0.3.0a3 acrescenta
[validação prévia do âmbito](SCOPE.md). A versão 0.3.0a4 acrescenta [configuração
opcional de schema 2](TARGETS.md); mantêm-se a configuração predefinida de schema 1
e os schemas 1 de plano e 2 de aprovação. Atualizar o pacote invalida as
aprovações de execução anteriores através da ligação à versão já existente:
preservar o histórico e criar novo plano e aprovação explícita antes de executar
verificações. Este teste apenas obtém aconselhamento e não exige aprovação de execução.

Consulta a [compatibilidade](EXECUTION.md), o [estado](STATUS.md) e as
[referências primárias](../PROVIDER_TESTING.md#compatibility-and-primary-references).
