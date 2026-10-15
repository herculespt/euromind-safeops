# Estado de implementação e publicação

<!-- safeops-version: 0.3.0a2 -->

[English](../STATUS.md)

**Versão atual do código: 0.3.0a2 — pré-versão alfa.** O CI cobre Python
3.11–3.13 em Linux, Windows e macOS. Não existem dependências externas em
execução. Este marco do código não é uma release publicada: tags e releases
GitHub exigem autorização própria; a publicação em registos de pacotes não
está configurada nem verificada.

## Implementado

| Capacidade | Limite prático |
|---|---|
| CLI, planos offline, sugestões de risco e especialidade | Classificação heurística e âmbito indicativo |
| Integridade do código/plano e auditoria local | Ligação SHA-256; registos locais alteráveis, sem assinaturas |
| Configuração e JSON estritos | Configuração schema 1, verificações únicas predefinidas e JSON UTF-8 sem chaves repetidas ou números não finitos |
| Aprovações schema 2 ligadas ao contrato de execução | Alterar versão/comandos exige novo plano e aprovação expressa |
| Verificações fixas de compilação e unittest | Suites vazias ou totalmente ignoradas falham; sem isolamento ou garantia de cobertura |
| Saída UTF-8, bloqueio e timeout | Mantêm-se as limitações de crashes, concorrência e código de confiança |
| Adaptadores de aconselhamento OpenAI, Anthropic e compatíveis | Consentimento expresso, envio apenas da tarefa e respostas UTF-8 estritas; contratos offline e HTTP em loopback; pedidos reais separados OpenAI `gpt-4.1-mini` e Anthropic `claude-haiku-5-5`, com revisão dos planos, verificados em 15 de outubro de 2026 |
| Main protegida e comunicação privada de vulnerabilidades | Definições verificadas como observações operacionais datadas |
| CI e validação de distribuição | Nove ambientes, dois jobs de construção e gate agregado obrigatório |
| Guias atuais EN/PT-PT e verificação da versão | Testes comparam metadados, ajuda da CLI e marcadores da documentação |

## Planeado ou não suportado

| Capacidade | Estado |
|---|---|
| Lista explícita de caminhos autorizados no workspace | Planeada |
| Edição autónoma por múltiplos agentes ou aplicação de patches | Não implementada |
| Commits Git ou PRs geradas pelo SafeOps | Não implementados; a manutenção do repositório é externa à ferramenta |
| Comandos arbitrários ou plugins de execução | Não implementados |
| Isolamento por contentor/sistema operativo e execução de código hostil | Não implementados |
| Aprovações assinadas, auditoria inviolável ou atestação remota | Não implementadas |
| Deploy de produção ou publicação automática de releases | Não implementados |
| Inferência real de modelos compatíveis/locais e compatibilidade alargada de contas/modelos | Pendente; os testes separados OpenAI e Anthropic não demonstram estas capacidades |
| Lockfiles de workflows, builds integralmente reproduzíveis e auditoria independente de segredos em todo o histórico | Trabalho separado pendente |

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
[Anthropic](audits/2026-10-15-anthropic-smoke.md). Esta
atualização de documentação mantém a versão 0.3.0a2: não altera comportamento,
schemas ou contrato de execução e não publica uma release.
