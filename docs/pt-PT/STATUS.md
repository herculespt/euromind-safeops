# Estado de implementação e publicação

<!-- safeops-version: 0.3.0a20 -->

[English](../STATUS.md)

**Versão atual do código: 0.3.0a20 — pré-versão alfa.** O CI cobre Python
3.11–3.13 em Linux, Windows e macOS. Sem dependências Python externas; o modo Git opcional exige Git instalado. A primeira [release GitHub v0.3.0a8](https://github.com/herculespt/euromind-safeops/releases/tag/v0.3.0a8)
foi publicada em 16 de outubro de 2026 no commit
`035c36b1b646a6c75178d5db6c19d8c55d624dcf`, com wheel, sdist e SHA256SUMS
verificados. Os 12 jobs da main e a validação do candidato passaram; o wheel
instalado passou 209 testes (3 ignorados por plataforma, zero falhas/erros).
Consulta a [evidência datada](audits/2026-10-16-first-alpha.md).
O [PyPI 0.3.0a8](https://pypi.org/project/euromind-safeops/0.3.0a8/) foi publicado
em 16 de outubro de 2026 através do Trusted Publisher autorizado. O workflow
[38874124869](https://github.com/herculespt/euromind-safeops/actions/runs/38874124869)
passou os três jobs: validação dos ficheiros originais, upload OIDC e verificação
dos hashes/instalação limpa pelo registo. Ambos os ficheiros mostram atestações
de publicação verificadas pelo PyPI. O ambiente `pypi` permite apenas a branch
`main`, zero tags e nenhum bypass administrativo. As atestações identificam o
commit do workflow de publicação `95a8bd51b2eb657233a9100f85c87be1b6548649`;
o código do pacote mantém o commit imutável 0.3.0a8 indicado acima. Esta evidência
é de proveniência da publicação; não demonstra builds reproduzíveis nem
aprovações SafeOps assinadas.

O código 0.3.0a20 acrescenta worktrees Git de preparação opcionais, preservando candidatos IA limitados com consentimento exato para partilha de código e propostas não aprovadas, mantendo fluxos manuais, ferramentas revistas e supervisão nativa; ainda não foi publicada uma nova release.

## Implementado

| Capacidade | Limite prático |
|---|---|
| Worktrees Git de preparação explícita | Revisão/consentimento próprios, base literal versionada, índice original preservado e recibos schema 2; [contrato](GIT_STAGING.md). Metadados Git partilhados, sem isolamento pelo SO |
| Geração de candidatos IA com revisão | Revisão offline do pedido, consentimento exato separado, resposta limitada/validada e proposta schema 2 não aprovada; [contrato](GENERATION.md) |
| Ferramentas de manutenção com hashes revistos | Dois perfis Linux/CPython 3.12 com dependências transitivas e instalação restrita; [política](TOOLING.md) |
| Recibos dos checks aprovados e inspeção histórica | Metadados/hashes/resultados limitados, revalidação antes/depois e estados explícitos de timeout/alteração/incompleto; sem output guardado, renovação de aprovação ou aplicação; [contrato](RUN_RECEIPTS.md) |
| Revisão do contexto original atual | Exige cópia correspondente e duas observações limitadas do original/plano/bases/configuração/alvos/versão/contrato; current/stale/incompatible, sem escrita nem aprovação; [contrato](STAGE_REVIEW.md) |
| Inspeção dos recibos/cópias sem escrita | Schema/ligações estritos e duas leituras limitadas; matching/changed/incomplete sem texto dos ficheiros ou escrita; sem revalidar o original atual nem conceder aprovação; [contrato](STAGING.md) |
| Supervisão dos processos próprios | Launcher bloqueado à entrada, grupo POSIX/job Windows, caudas limitadas e limpeza confirmada antes do resultado; limpeza incerta mantém marcador/intent; [contrato](SUPERVISION.md) |
| Aplicação revista ao original e rollback | Revisão atual, compile/testes aprovados e inalterados na cópia, fingerprint exato, backups/journal privados e reposição conservadora; sem atomicidade entre vários ficheiros ou isolamento; [contrato](APPLICATION.md) |
| Cópias locais de preparação | Fingerprint revisto exato, ficheiros independentes, exclusões e manifesto/recibo; sem aplicação ao original, testes automáticos ou sandbox; [contrato](STAGING.md) |
| Propostas locais ligadas ao plano | Caminhos explícitos exatos, ligações ao snapshot/configuração/contrato e revisão sem aplicação nem aprovação; [contrato](PROPOSALS.md) |
| Preview local de candidatos de texto | Hash exato por ficheiro e diff unificado sem escrita; candidatos fornecidos manualmente; [contrato](PREVIEW.md) |
| CLI, planos offline, sugestões de risco e especialidade | Classificação heurística e âmbito indicativo |
| Integridade do código/plano e auditoria local | Ligação SHA-256; registos locais alteráveis, sem assinaturas |
| Configuração e JSON estritos | Configuração predefinida de schema 1 e alvos opcionais de schema 2, verificações únicas predefinidas e JSON UTF-8 sem chaves repetidas ou números não finitos |
| Aprovações schema 2 ligadas ao contrato de execução | Alterar versão/comandos exige novo plano e aprovação expressa |
| Verificações fixas de compilação e unittest | Suites vazias ou totalmente ignoradas falham; sem isolamento ou garantia de cobertura |
| Saída UTF-8 e timeout | Timeout do grupo/job próprio com caudas/limpeza limitadas; sem contenção de escapes deliberados; [contrato](SUPERVISION.md) |
| Guarda nativa local e marcador próprio | Bloqueio cooperativo POSIX/Windows; guarda persistente, marcadores abandonados/antigos bloqueiam |
| Diagnóstico e recuperação explícita por arquivo | Estado/fingerprint no doctor, verificação humana, recibo/auditoria; sem dedução automática ou aprovação |
| Adaptadores de aconselhamento OpenAI, Anthropic e compatíveis | Consentimento expresso, envio apenas da tarefa e respostas UTF-8 estritas; contratos offline e HTTP em loopback; pedidos reais separados OpenAI `gpt-4.1-mini` e Anthropic `claude-haiku-5-5`, com revisão dos planos, verificados em 15 de outubro de 2026 |
| Validação prévia dos caminhos de âmbito | Antes do fornecedor/gravação e novamente na aprovação/execução; os caminhos não restringem os alvos fixos |
| Diretórios explícitos das verificações | Schema 2 opcional; validação recursiva de ligações e digest dos ficheiros selecionados; sem isolamento pelo SO |
| Envelopes JSON da CLI | `--json` global opcional; schema 1, resultados/erros/avisos tratados e códigos 0/1/2; [contrato](OUTPUT.md) |
| Resumos agregados e JUnit XML local | Gerados/validados nos nove ambientes e dois jobs com wheel; casos sintéticos e categorias fixas; [contrato](REPORTING.md) |
| Gate de cobertura medida | Linux/Python 3.12, instruções/decisões do pacote e filhos Python suportados, mínimo combinado de 90%; [limites](COVERAGE.md) |
| Main protegida e comunicação privada de vulnerabilidades | Definições verificadas como observações operacionais datadas |
| CI e validação de distribuição | Nove ambientes, dois jobs de construção e gate agregado obrigatório |
| Guias atuais EN/PT-PT e verificação da versão | Testes comparam metadados, ajuda da CLI e marcadores da documentação |

## Planeado ou não suportado

| Capacidade | Estado |
|---|---|
| Restrição de caminhos imposta pelo sistema operativo | Planeada; selecionar entradas não impede leituras arbitrárias |
| Edição autónoma por múltiplos agentes | Não implementada; candidatos manuais ou IA revistos exigem revisão humana e aplicação explícita |
| Commits Git ou PRs geradas pelo SafeOps | Não implementados; a manutenção do repositório é externa à ferramenta |
| Comandos arbitrários ou plugins de execução | Não implementados |
| Isolamento por contentor/sistema operativo e execução de código hostil | Não implementados |
| Aprovações assinadas, auditoria inviolável ou atestação remota | Não implementadas |
| Deploy de produção ou publicação automática de releases | Não implementados |
| Inferência real de modelos compatíveis/locais e compatibilidade alargada de contas/modelos | Pendente; os testes separados OpenAI e Anthropic não demonstram estas capacidades |
| Bloqueios distribuídos/de rede, contenção hostil/de escapes e recuperação automática | Planeados; bloqueio atual local/cooperativo e recuperação com confirmação humana |
| Cobertura noutros perfis e upload de relatórios | Planeados; medição Linux/Python 3.12, JUnit local e resumos implementados |
| Builds integralmente reproduzíveis e auditoria independente de segredos em todo o histórico | Trabalho separado pendente |

O [roadmap](../../ROADMAP.md) regista o trabalho futuro sem prometer datas ou
atribuir agentes autónomos a esta versão. A [auditoria datada](audits/2026-10-15.md)
mantém o commit e as contagens históricos; não é reescrita como se tivesse
analisado código posterior.

## Controlo da versão e documentação

Uma mudança de comportamento atualiza `pyproject.toml`, `__version__`, a ajuda
dinâmica da CLI, changelog, roadmap, este estado e os guias afetados em EN/PT-PT.
Os documentos atuais com versão têm um marcador `safeops-version`, comparado
pela suite de testes. As referências históricas dos changelogs e auditorias
mantêm-se. Atualizar a versão do código não cria tags, releases, uploads para
lojas ou publicações de pacotes.

Consulta a [compatibilidade de execução](EXECUTION.md), o
[modelo de confiança](../TRUST_MODEL.md), o [CI](CI.md) e o
[procedimento de releases](../RELEASING.md).

A [validação dos fornecedores](PROVIDER_TESTING.md) distingue respostas fixas dos
pedidos reais separados nos registos [OpenAI](audits/2026-10-15-openai-smoke.md) e
[Anthropic](audits/2026-10-15-anthropic-smoke.md), testados na versão 0.3.0a2.
A versão atual 0.3.0a20 acrescenta [supervisão dos processos próprios](SUPERVISION.md), mantendo [aplicação revista e rollback](APPLICATION.md), mantendo [recibos dos checks aprovados](RUN_RECEIPTS.md), mantendo [revisão do original atual](STAGE_REVIEW.md), mantendo [inspeção histórica das cópias](STAGING.md), cópias separadas, [propostas ligadas ao plano](PROPOSALS.md), [previews locais](PREVIEW.md), [cobertura medida](COVERAGE.md), [JUnit local](REPORTING.md),
[bloqueio nativo e recuperação explícita](LOCKING.md),
[saída estruturada/resumos CI](OUTPUT.md), [diretórios opcionais](TARGETS.md),
a [validação do âmbito](SCOPE.md) e o schema 1 predefinido.
A ligação à versão invalida aprovações anteriores; a configuração de schema 2
liga também os ficheiros selecionados. A restrição
completa do sistema de ficheiros continua planeada. A release GitHub e o pacote
PyPI publicados são 0.3.0a8; a main contém código posterior, conforme o estado acima.

Teste real separado OpenAI de geração no código 0.3.0a19: um ficheiro sintético revisto, um pedido, 316 tokens observados, proposta schema 2 não aprovada/revista e original/credenciais inalterados; [evidência](audits/2026-10-17-openai-generation-smoke.md). Geração Anthropic mantém validação offline; os testes consultivos reais antigos continuam específicos de 0.3.0a2.
