# Teste real OpenAI de geração revista — 2026-10-17

[English](../../audits/2026-10-17-openai-generation-smoke.md)

Observado em 2026-10-16T23:28:36Z (17 de outubro, 00:28:36 Europe/Lisbon), no
código **0.3.0a19**. É independente dos testes consultivos antigos do código 0.3.0a2.

Um único pedido real Responses API usou a chave do projeto já autorizada, lida
localmente de `.env.local` ignorado, sem a mostrar nem alterar. Modelo pedido:
`gpt-4.1-mini`; devolvido: `gpt-4.1-mini-2025-04-14`. Consumo observado:
**250 tokens de entrada + 66 de saída = 316**. Limite fixo de saída: 8 192 tokens;
timeout configurado: 60 segundos; sem retry/fallback.

## Fixture não privada e resultado

Workspace temporário novo fora do repositório; único ficheiro selecionado,
`greeting.py`, com 19 bytes:

```python
GREETING = "Hello"
```

A tarefa offline pediu mudar o valor para Olá, mantendo nome e newline final.
A revisão confirmou apenas tarefa, schema, path/hash base/conteúdo selecionados,
instruções/modelo/limites fixos. Não foi enviado código deste repositório,
configuração, histórico Git nem estado privado. Corpo serializado: 1 101 bytes;
store=false. Consentimento de upload ligado ao fingerprint exato antes do pedido.

- Plano `370dd85cb5c4`; proposta `9ff1860119cd`.
- Pedido revisto: `sha256:7e922c20383bd1616acad51556540655679de0cab04387088a00910dc3b7d9ab`.
- Original: `sha256:3ffca746f9bd94691434fdba37ed9d5eab5a5a493346981edacda449eb8e8809`.
- Substituição validada: `sha256:cbb5ec4cae0a9897cbf39aabeac4a7219f66dc506f5e1aee6ea70496c1b429e9`.
- Proposta schema 2/origem estritas e `review-proposal` aprovados como validação
  local, sem conceder aprovação de execução.
- Inspeção AST, sem execução, confirmou uma única atribuição a GREETING, com
  constante Olá. A resposta bruta não foi retida publicamente.
- Original e ficheiro de credenciais permaneceram byte a byte inalterados.
- Zero aprovações/checks, staging, aplicação ao original, operações Git ou nova
  publicação. O candidato ficou não aprovado.

São observações locais e hashes sem chave, não proveniência autenticada. Um
ficheiro não demonstra qualidade geral, retenção do fornecedor, todas as contas/
modelos, geração Anthropic real ou inferência compatível/local. O CI offline/
loopback é validado separadamente antes da integração protegida. Fonte/tag/anexos
públicos GitHub/PyPI 0.3.0a8 mantêm-se.
