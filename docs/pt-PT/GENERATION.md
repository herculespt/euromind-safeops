# Candidatos IA com revisão explícita — 0.3.0a19

<!-- safeops-version: 0.3.0a19 -->

[English](../GENERATION.md)

Operação separada de partilha de código, com consentimento explícito, para OpenAI
Responses, Anthropic Messages e fornecedores compatíveis. `plan` continua a enviar
apenas a tarefa; previews/propostas manuais continuam sem fornecedor.

`review-generation PLAN_ID --provider PROVIDER --model MODEL` não faz pedidos nem
persiste dados. Mostra endpoint, timeout e corpo JSON exatos (incluindo texto dos
ficheiros), ligações locais e fingerprint de confirmação. `--endpoint` aplica-se
só ao fornecedor compatível. Exige plano inicializado, não crítico e inalterado,
com cada ficheiro existente selecionado explicitamente. Recusa diretórios,
links/reparse/hardlinks, caminhos internos/de ambiente/gerados, texto inválido e
padrões óbvios de credenciais.

`generate-proposal PLAN_ID`, com as mesmas opções, exige
`--allow-source-upload` e `--confirm FINGERPRINT`. `--allow-remote` da tarefa não
consente envio de código. Rever o pedido completo antes de confirmar; padrões não
detetam toda a informação privada/credenciais. Envia apenas tarefa,
path/hash base/conteúdo selecionados, schema/instruções fixos e modelo/limites.
Não envia conselho do plano, histórico Git, configuração/estado ou outros ficheiros.
Credenciais entram só nos headers, nunca na revisão/registo. OpenAI usa store=false;
políticas de retenção da conta/fornecedor são externas.

Limites iniciais: 1–4 ficheiros, 8 192 bytes por original, 16 384 no total,
64 000 bytes no payload JSON e no candidato gerado, 16 384 por substituição e
32 768 nas substituições em conjunto. Texto UTF-8/LF sem BOM, com newline final,
sem controlos além de tab/LF e até 5 000 linhas por ficheiro. Limite fixo de
8 192 tokens de output; timeout de 1–60 segundos, por omissão 30. Limitam operações
individuais/armazenamento, sem garantir orçamento da conta, faturação, tempo total
de rede ou quotas de recursos do SO.

A confirmação liga payload, destino/fornecedor/modelo/timeout, versão/política e
contexto atual do plano/código/configuração/alvos/contrato de execução. Leituras
limitadas e contexto são verificados antes/depois do pedido e antes de persistir.
Alterações observadas causam recusa; mantêm-se corridas residuais/ABA e não se pode
recolher um pedido já enviado. Sem manter bloqueio de execução durante a rede nem
afirmar isolamento.

Um único pedido, sem redirects, retries, continuação, fallback, ferramentas ou
streaming. Reutiliza transporte limitado e JSON estrito. Exige conclusão explícita:
OpenAI completed, Anthropic end_turn, compatível finish_reason stop. Recusa
truncamento, recusa do modelo, tools/output não textual, JSON ambíguo/inválido,
campos/caminhos/operações desconhecidos, bases antigas, no-ops e limites excedidos,
sem persistir texto do fornecedor. O candidato usa substituições schema 1 existentes,
para subconjunto selecionado não vazio.

Output válido torna-se **proposta schema 2 não aprovada**, com origem estrita:
kind=ai, fornecedor, modelo e SHA-256 do pedido revisto. Propostas manuais mantêm
schema 1; ambos seguem revisão/staging/aplicação existentes. Metadados locais sem
chave não são proveniência autenticada. Só candidato validado e metadados limitados
ficam na proposta privada; resposta bruta e payload não são guardados. A auditoria
usa apenas ação, ID do plano e estado fixo. Falha de armazenamento/auditoria pode
reter proposta válida não aprovada; inspecionar registos, sem deduzir aprovação ou
eliminar automaticamente.

Continuar explicitamente por `review-proposal`, `stage-proposal`, novo plano e
aprovação de execução na cópia, ambos os checks, revisão do original/aplicação e
confirmação exata. Gerar não executa, prepara cópias, aplica, faz rollback, altera
Git ou concede/renova aprovação. A mudança de versão exige planos/propostas/
aprovações novos. A alfa pública GitHub/PyPI 0.3.0a8 é anterior e mantém-se.

Testes offline/loopback demonstram contratos/recusas, não qualidade do modelo.
Qualquer smoke real separado usa ficheiros sintéticos não privados revistos e
regista fornecedor/modelo/versão/limites, sem credenciais. Candidato válido ou smoke
anterior não demonstram correção semântica nem disponibilidade universal.

Referências: [OpenAI Responses](https://developers.openai.com/api/reference/resources/responses/methods/create),
[conclusão Anthropic](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons).
