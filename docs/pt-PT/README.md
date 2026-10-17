# EuroMind SafeOps — Português (Portugal)

<!-- safeops-version: 0.3.0a20 -->

**Ferramenta open source de orquestração de engenharia com aprovação humana e execução controlada de verificações.**

## O que já funciona na versão 0.3.0a20 (pré-versão alfa do código)

- [Aplicação explícita ao original e rollback](APPLICATION.md): revisão atual, ambos os checks aprovados na cópia, confirmação exata, backups privados e journal retido; recusa sobrepor alterações humanas observadas.
- [Supervisão dos processos próprios](SUPERVISION.md): grupos POSIX/jobs Windows, descendentes normais, caudas UTF-8 limitadas e marcador/intent retidos quando a limpeza é incerta; sem isolamento hostil.
- CLI Python 3.11+ sem dependências Python externas obrigatórias; o modo Git opcional exige Git instalado.
- `inspect-run ID_DA_EXECUCAO`: [recibos dos checks aprovados](RUN_RECEIPTS.md), ligados aos inputs antes/depois; resultados passed/failed/timed-out/changed-inputs/incomplete sem guardar output dos testes nem renovar aprovação.
- `review-stage ID_DA_COPIA`: [revisão do original atual](STAGE_REVIEW.md), exige cópia correspondente e verifica plano, original, bases, configuração, alvos, versão e contrato sem escrita nem aprovação.
- `inspect-stage ID_DA_COPIA`: [inspeção histórica do recibo/cópia](STAGING.md), sem escrita, texto dos ficheiros ou aprovação; deteta ficheiros alterados, novos ou em falta.
- `--json` global opcional com envelope comum de resultados/erros/avisos; [contrato](OUTPUT.md).
- Resumos unittest e [JUnit XML local](REPORTING.md) gerados e validados nos nove ambientes CI e nos dois jobs com wheel instalada; identificadores sintéticos e categorias fixas. [Cobertura](COVERAGE.md) medida em Linux/Python 3.12 com mínimo combinado de 90%; uploads permanecem planeados.
- [Cópias locais de preparação](STAGING.md): confirmação do fingerprint, substituições só na cópia e recibo; verificações exigem aprovação própria.
- [Propostas locais ligadas ao plano](PROPOSALS.md): gravação do candidato, revisão dos diffs e rejeição de contexto alterado; sem aplicação nem aprovação.
- [Preview local de candidatos](PREVIEW.md): diffs sem escrita, hashes exatos por ficheiro e formato JSON estrito; sem conceder aprovação.
- Planeamento local de tarefas com classificação de risco e especialidade sugerida.
- Registo de aprovação humana ligado ao conteúdo do plano e do código-fonte.
- Seleção opcional de [diretórios das verificações](TARGETS.md) no schema 2, com validação recursiva e digest dos ficheiros selecionados; sem isolamento pelo sistema operativo.
- Execução de duas verificações predefinidas: compilação Python e testes `unittest`.
- Validação estrita da configuração e de JSON UTF-8; aprovações ligadas à versão e ao contrato de execução.
- Rejeição de suites vazias ou totalmente ignoradas; suporte a subdiretórios de testes com `__init__.py`.
- Registo de auditoria local e pesquisa limitada de padrões típicos de credenciais.
- [Bloqueio nativo e recuperação explícita](LOCKING.md): guarda persistente, marcador próprio, diagnóstico no doctor e arquivo com confirmação humana; sem deduzir que os processos filhos terminaram.
- Validação prévia dos caminhos declarados antes do fornecedor, gravação, aprovação e execução; [política de âmbito](SCOPE.md). Os caminhos continuam consultivos e não restringem os alvos das verificações.
- Aconselhamento opcional através de OpenAI Responses API, Anthropic Messages API (Claude) ou modelos locais compatíveis com Chat Completions.
- Comando `safeops providers`, que informa se existem chaves configuradas sem mostrar o seu valor.
- Respostas de fornecedores com validação JSON UTF-8 estrita, testes de falhas de transporte e integração HTTP real com respostas locais fixas; pedidos reais separados OpenAI `gpt-4.1-mini` e Anthropic `claude-haiku-5-5` verificados na versão 0.3.0a2; modelos compatíveis/locais e compatibilidade alargada ainda por validar.

**Não implementa** agentes autónomos que editem código, isolamento seguro, execução arbitrária, pipelines de produção, proteção garantida contra ataques. O código dos testes executa com os privilégios do utilizador: não utilizes repositórios não confiáveis.

## Instalar e testar

Para instalar a alfa publicada num ambiente virtual:
`python -m pip install euromind-safeops==0.3.0a8`.
Essa versão ainda não inclui previews, propostas persistentes, cópias locais
de preparação nem inspeção de recibos. Os comandos abaixo instalam o código atual 0.3.0a20 do checkout.

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
safeops --root examples/demo_project init
safeops --root examples/demo_project plan "Melhorar a documentação do exemplo"
```

Copia o ID apresentado em `plan` e executa, substituindo `ID_DO_PLANO`:

```powershell
safeops --root examples/demo_project review ID_DO_PLANO
safeops --root examples/demo_project approve ID_DO_PLANO --confirm ID_DO_PLANO --reason "Revisei o código e os testes"
safeops --root examples/demo_project run ID_DO_PLANO
```

O plano **não modifica código**. A execução necessita de aprovação explícita e é bloqueada quando o projeto muda desde o planeamento.

Ao atualizar da versão 0.2.0, preserva o workspace e o histórico. A configuração
válida de schema 1 continua suportada, mas as aprovações antigas não podem ser
reutilizadas: revê o código, cria um plano novo e aprova-o expressamente. Consulta
a [política de execução e compatibilidade](EXECUTION.md) e o
[estado do que está implementado e planeado](STATUS.md). A versão do código não
cria uma publicação automaticamente. A [primeira alpha GitHub](https://github.com/herculespt/euromind-safeops/releases/tag/v0.3.0a8)
e o [pacote PyPI 0.3.0a8](https://pypi.org/project/euromind-safeops/0.3.0a8/)
foram publicados em 16 de outubro de 2026. Hashes originais, instalação pelo
registo e atestações de publicação verificadas pelo PyPI foram confirmados.
O código 0.3.0a20 ainda não foi publicado como pacote. Consulta a
[evidência de entrega](audits/2026-10-16-first-alpha.md).

Atualizar para 0.3.0a20 exige novo plano/aprovação pela ligação à versão.
Mantém-se o schema 1 predefinido; o schema 2 opcional seleciona diretórios e
exige digest dos ficheiros selecionados. Mantêm-se os schemas 1 de plano e 2 de aprovação.

Para utilizar OpenAI ou Claude, configura `OPENAI_API_KEY` ou `ANTHROPIC_API_KEY` no ambiente e fornece o modelo pretendido e `--allow-remote`. Vê [as instruções completas dos fornecedores](PROVIDERS.md) e a [evidência dos testes](PROVIDER_TESTING.md). Uma subscrição de chat não inclui necessariamente créditos de API.

Consulta a [documentação principal](../../README.md), [âmbito e origem do projeto](PROJECT_SCOPE.md), [arquitetura](../ARCHITECTURE.md), [modelo de confiança](../TRUST_MODEL.md) e [regras de segurança](SECURITY.md).

## Manutenção e validação

A proteção da `main` foi ativada e verificada em 15 de outubro de 2026: exige
pull request, `quality-gate` de GitHub Actions, branch atualizada e conversas
resolvidas. Não permite force pushes, eliminação ou exceções de bypass. São
exigidas zero aprovações enquanto existir apenas um maintainer.

Consulta o [guia de manutenção](MAINTAINER_GUIDE.md) e a
[auditoria de 15 de outubro de 2026](audits/2026-10-15.md), incluindo as limitações
e os próximos trabalhos. A saída das verificações Python passa a utilizar UTF-8
explicitamente para preservar os acentos em `stdout` e `stderr`, mesmo quando
o ambiente herdado pede ASCII. Esta correção está incluída no marco de código
`0.3.0a1` do changelog; a publicação continua a exigir autorização própria.

O [guia de CI e construção do pacote](CI.md) descreve as Actions fixadas por SHA,
a versão mínima de construção e a validação dos artefactos fora do checkout.

Licença: Apache 2.0. Projeto open source autónomo.

O código atual mantém perfis de manutenção com dependências transitivas e hashes revistos; ver [política de ferramentas](TOOLING.md). A matriz de compatibilidade mantém-se e o pacote público continua 0.3.0a8.

O código 0.3.0a20 permite [gerar candidatos IA com revisão explícita](GENERATION.md). `review-generation` mostra offline o pedido completo; `generate-proposal` exige o fingerprint exato e `--allow-source-upload`. Mantêm-se revisão, testes e aplicação confirmados em separado. `plan` continua a enviar só a tarefa com `--allow-remote`.

Teste real OpenAI de geração no código 0.3.0a19 aprovado com um ficheiro sintético de 19 bytes, sem aprovação/checks/aplicação e com original/credenciais inalterados; [evidência datada](audits/2026-10-17-openai-generation-smoke.md).


Preparação Git no código 0.3.0a20: worktrees locais detached com confirmação própria e evidência de ligação schema 2; cópias simples mantêm schema 1. [Contrato](GIT_STAGING.md). Metadados Git partilhados não constituem isolamento; commits/pushes/PRs automáticos e proveniência SafeOps assinada não estão implementados. Aprovação/testes/aplicação mantêm gates explícitos. O pacote público GitHub/PyPI 0.3.0a8 mantém-se inalterado.
