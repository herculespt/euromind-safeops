# Fornecedores de aconselhamento — 0.3.0a5

<!-- safeops-version: 0.3.0a5 -->

[English](../PROVIDERS.md)

Os adaptadores nativos foram introduzidos na versão 0.2.0. A versão 0.3.0a2
introduziu JSON estrito; a 0.3.0a3 acrescenta [validação prévia do âmbito](SCOPE.md)
antes do fornecedor, mantendo os protocolos apenas consultivos.
A [evidência dos testes](PROVIDER_TESTING.md) distingue contratos simulados,
HTTP real em loopback e pedidos reais separados OpenAI `gpt-4.1-mini` e Anthropic
`claude-haiku-5-5`, aprovados na versão 0.3.0a2 em 15 de outubro de 2026. A inferência de modelos
compatíveis/locais e a compatibilidade universal continuam por validar.

| `--provider` | Protocolo | Autenticação | Consentimento remoto |
|---|---|---|---|
| `offline` | Aconselhamento local determinístico | Nenhuma | Não aplicável |
| `openai` | OpenAI Responses API | `OPENAI_API_KEY` | Obrigatório |
| `anthropic` | Anthropic Messages API | `ANTHROPIC_API_KEY` | Obrigatório |
| `openai-compatible` | API compatível com Chat Completions | `SAFEOPS_API_KEY` opcional | Obrigatório |

O ID do modelo é explícito em `--model` e tem de ser suportado pela conta.
Uma subscrição ChatGPT ou Claude.ai não equivale a créditos de API. Os pedidos
podem ter custos. A ferramenta não envia ficheiros do projeto: envia a tarefa,
a instrução fixa do sistema e metadados como o modelo e o limite de saída.
Nunca incluir segredos ou dados privados na tarefa; a pesquisa heurística é limitada.

## Configuração

Instalar com `python -m pip install -e .`. Executar `safeops providers` para ver
a presença das chaves nativas. No adaptador compatível, `configured: true`
indica disponibilidade, sem validar endpoint. O comando não comprova ligação,
créditos ou compatibilidade do modelo. Injetar as chaves no ambiente através de
um mecanismo seguro; nunca as colocar no chat, em Git ou em resultados públicos.

Inicializar o workspace uma única vez:

```powershell
safeops --root examples/demo_project init
```

Com a variável `OPENAI_API_KEY` já configurada:

```powershell
safeops --root examples/demo_project plan "Rever a estratégia de testes" `
  --provider openai --model ID_DO_MODELO_OPENAI --allow-remote
```

Com `ANTHROPIC_API_KEY` já configurada:

```powershell
safeops --root examples/demo_project plan "Rever os limites dos módulos" `
  --provider anthropic --model ID_DO_MODELO_CLAUDE --allow-remote
```

Usar uma chave Anthropic limitada a um único workspace. O adaptador atual não
envia `anthropic-workspace-id`; as chaves com vários workspaces não estão
validadas. O modelo testado é evidência, não uma nova predefinição. Consulta o
[registo Anthropic](audits/2026-10-15-anthropic-smoke.md).

Para um modelo local compatível, com o serviço efetivamente iniciado:

```powershell
safeops --root examples/demo_project plan "Rever a documentação pública" `
  --provider openai-compatible `
  --endpoint http://127.0.0.1:8080/v1/chat/completions `
  --model ID_DO_MODELO_LOCAL --allow-remote
```

O endereço acima é um exemplo; não demonstra que existe um serviço nessa porta.
Alguns serviços compatíveis exigem `SAFEOPS_API_KEY`. O endpoint exige HTTPS,
exceto HTTP em loopback literal. Não pode conter credenciais, query ou fragmento.
As origens nativas OpenAI/Anthropic são fixas e não aceitam substituição por
`--endpoint`. Os redirecionamentos são rejeitados.

O SafeOps lê credenciais do ambiente do processo; não carrega `.env.local`
automaticamente. Um ficheiro local autorizado deve ficar fora do Git/artefactos e
ser carregado por um mecanismo de confiança. A pesquisa heurística continua a
inspecionar ficheiros ignorados dentro do workspace; validar o código público
num checkout limpo sem credenciais locais, sem enfraquecer as regras de pesquisa.

## Comportamento e limites

- Não há chamadas remotas durante `init`, `doctor`, `scan`, `review`, `approve`,
  `run` ou planeamento offline. O acesso exige `--allow-remote`.
- OpenAI recebe `store: false`; a política de retenção depende também do fornecedor.
- O timeout de operação de rede é 15 segundos por omissão, configurável entre 1
  e 60 com `--provider-timeout`; não garante um prazo total para o pedido.
- A leitura é limitada a 256 001 bytes e rejeita respostas acima de 256 000.
  O texto final fica limitado a 6 000 caracteres. Não há retries nem fallback automáticos.
- As respostas têm de ser objetos JSON UTF-8, com BOM UTF-8 opcional. Chaves
  repetidas, números não finitos/overflow, outras codificações, JSON inválido ou
  valores de topo que não sejam objetos produzem erro controlado.
- É necessário texto utilizável. Blocos não textuais não são executados.
  A resposta fica no plano como aconselhamento não confiável; não aprova ações.
- A classificação de risco e os controlos de integridade/execução são determinísticos.
- O CI usa simulações e HTTP real local com respostas fixas. Não valida contas,
  inferência ou todos os modelos. O [procedimento de teste real](PROVIDER_TESTING.md)
  regista separadamente os pedidos reais OpenAI e Anthropic já verificados e as restantes validações pendentes.

Consulta as [referências de protocolo](../PROVIDER_TESTING.md#compatibility-and-primary-references),
o [estado de implementação](STATUS.md) e a [segurança](SECURITY.md).
