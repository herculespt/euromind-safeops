# EuroMind SafeOps — 0.3.0a17 alpha

<!-- safeops-version: 0.3.0a17 -->

A Python 3.11+ command-line tool for advisory engineering plans, explicit human
approval and fixed compile/unittest checks. Apache-2.0; no third-party runtime
dependencies. Optional OpenAI, Anthropic and compatible endpoints provide advice
only, with explicit remote consent.

This is an **alpha development tool**. Tests execute trusted Python with the
operator's privileges. Local hashes, audit records and cooperative locks are not
a sandbox, signatures or protection against a malicious local actor. Empty or
wholly skipped test suites fail. Changing code, configuration or package version
requires a fresh reviewed plan and explicit approval.

Current source is 0.3.0a17. The published registry alpha is
[0.3.0a8](https://pypi.org/project/euromind-safeops/0.3.0a8/), verified on
2026-10-16 with original wheel/sdist hashes, clean installation and PyPI-verified
publishing attestations. It predates previews, proposals, staging copies and receipt inspection.
Install that exact published version:

~~~bash
python -m pip install euromind-safeops==0.3.0a8
safeops --version
~~~

Source installation remains available from the
[GitHub repository](https://github.com/herculespt/euromind-safeops).
See [publication status](https://github.com/herculespt/euromind-safeops/blob/main/docs/STATUS.md)
for the distinction between current source and published distributions.

- [Quick start](https://github.com/herculespt/euromind-safeops/blob/main/docs/QUICKSTART.md)
- [Execution and approvals](https://github.com/herculespt/euromind-safeops/blob/main/docs/EXECUTION.md)
- [Implemented and planned](https://github.com/herculespt/euromind-safeops/blob/main/docs/STATUS.md)
- [Security reporting](https://github.com/herculespt/euromind-safeops/blob/main/SECURITY.md)
- [License](https://github.com/herculespt/euromind-safeops/blob/main/LICENSE)

## Português (Portugal)

Ferramenta Python 3.11+ para planos consultivos, aprovação humana expressa e
verificações fixas de compilação e unittest. Sem dependências externas em execução.
Os fornecedores opcionais dão aconselhamento; não executam as respostas nem
concedem aprovação.

**Versão alfa:** utilizar apenas código e testes de confiança. Não implementa
isolamento seguro nem alterações autónomas de código. A instalação acima escolhe
a versão PyPI publicada 0.3.0a8, anterior aos previews, propostas e cópias de
preparação e inspeção de recibos do código atual 0.3.0a17. Hashes, instalação e atestações de publicação
verificadas pelo PyPI foram confirmados em 16 de outubro de 2026. Atualizações
exigem plano e aprovação novos, preservando o histórico.

- [Guia PT-PT](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/README.md)
- [Estado e publicação](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/STATUS.md)
- [Fornecedores e testes](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/PROVIDER_TESTING.md)

Copyright 2026 Sérgio Ribeiro. Apache License 2.0.

Read-only local candidate previews are available in source 0.3.0a17: [format and limits](https://github.com/herculespt/euromind-safeops/blob/main/docs/PREVIEW.md).
Previews locais sem escrita disponíveis no código 0.3.0a17: [formato e limites](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/PREVIEW.md).

Plan-bound local proposals are available in source 0.3.0a17: [workflow and limits](https://github.com/herculespt/euromind-safeops/blob/main/docs/PROPOSALS.md). They store candidate text locally without applying it or granting approval.
Propostas locais ligadas ao plano disponíveis no código 0.3.0a17: [procedimento e limites](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/PROPOSALS.md). Guardam o texto localmente sem o aplicar nem aprovar execução.

Separate local staging copies are available in source 0.3.0a17: [workflow and limits](https://github.com/herculespt/euromind-safeops/blob/main/docs/STAGING.md). Exact-fingerprint confirmation writes replacements only to a new copy; checks require fresh approval.
Cópias locais separadas disponíveis no código 0.3.0a17: [procedimento e limites](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/STAGING.md). A confirmação do fingerprint escreve só na cópia; os testes exigem aprovação nova.

Read-only historical stage inspection is available in source 0.3.0a17:
[contract](https://github.com/herculespt/euromind-safeops/blob/main/docs/STAGING.md).
`inspect-stage` reports filtered matching/changed/incomplete observations, without
file text, writes, current-source revalidation or execution/application approval.
Inspeção histórica sem escrita disponível no código 0.3.0a17:
[contrato PT-PT](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/STAGING.md).
Sem texto dos ficheiros, revalidação do original atual ou aprovação.

Current original-context review is available in source 0.3.0a17: [contract and limits](https://github.com/herculespt/euromind-safeops/blob/main/docs/STAGE_REVIEW.md). `review-stage` requires a matching copy and checks current original bindings; it grants no approval or application authority.
Revisão do original atual disponível no código 0.3.0a17: [contrato e limites](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/STAGE_REVIEW.md). Exige cópia correspondente e verifica ligações atuais; não concede aprovação nem aplica alterações.

Approved-check receipts are available in source 0.3.0a17: [contract](https://github.com/herculespt/euromind-safeops/blob/main/docs/RUN_RECEIPTS.md). Results bind observed before/after inputs, exclude captured output from persistence and support historical `inspect-run` without approval renewal or application authority.
Recibos dos checks aprovados disponíveis no código 0.3.0a17: [contrato](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/RUN_RECEIPTS.md). Ligam inputs observados antes/depois, excluem output capturado da persistência e permitem inspeção histórica sem renovar aprovação nem autorizar aplicação.

Explicit reviewed original replacements and conservative rollback are available in source 0.3.0a17: [workflow and limits](https://github.com/herculespt/euromind-safeops/blob/main/docs/APPLICATION.md). Require current unchanged passed staged compile/tests, exact human confirmation, native guards and private bounded backups/journals. Inspection and fresh-confirmed rollback preserve evidence and refuse observed human edits; no Git operations, multi-file atomicity, power-loss durability or OS isolation. Public package 0.3.0a8 predates this capability.

Aplicação explícita revista ao original e rollback conservador disponíveis no código 0.3.0a17: [procedimento e limites](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/APPLICATION.md). Exigem compile/testes aprovados e inalterados na cópia, confirmação humana exata, guards e backups/journals privados limitados. Inspeção/rollback preservam evidência e recusam edições humanas observadas; sem operações Git, atomicidade de vários ficheiros, durabilidade após falha de energia ou isolamento pelo SO. O pacote público 0.3.0a8 é anterior a esta capacidade.

Owned fixed-check group/job supervision and bounded UTF-8 output tails are available in source 0.3.0a17: [lifecycle and limits](https://github.com/herculespt/euromind-safeops/blob/main/docs/SUPERVISION.md). Native cleanup uncertainty retains blocking/incomplete evidence; cooperating process ownership is not hostile-code isolation.

Supervisão dos grupos/jobs dos checks e caudas UTF-8 limitadas disponíveis no código 0.3.0a17: [ciclo e limites](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/SUPERVISION.md). Limpeza nativa incerta mantém bloqueio/evidência incompleta; supervisão cooperativa não isola código hostil.

Source 0.3.0a17 refines final Windows job accounting and shares one bounded cleanup budget across release/EOF/failure handling. Código 0.3.0a17 afina a contagem final do job Windows e partilha um orçamento limitado de limpeza entre libertação/EOF/falhas; os limites cooperativos documentados mantêm-se.
