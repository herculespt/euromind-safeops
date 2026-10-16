# EuroMind SafeOps — 0.3.0a12 alpha

<!-- safeops-version: 0.3.0a12 -->

A Python 3.11+ command-line tool for advisory engineering plans, explicit human
approval and fixed compile/unittest checks. Apache-2.0; no third-party runtime
dependencies. Optional OpenAI, Anthropic and compatible endpoints provide advice
only, with explicit remote consent.

This is an **alpha development tool**. Tests execute trusted Python with the
operator's privileges. Local hashes, audit records and cooperative locks are not
a sandbox, signatures or protection against a malicious local actor. Empty or
wholly skipped test suites fail. Changing code, configuration or package version
requires a fresh reviewed plan and explicit approval.

Current source is 0.3.0a12. The published registry alpha is
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
preparação e inspeção de recibos do código atual 0.3.0a12. Hashes, instalação e atestações de publicação
verificadas pelo PyPI foram confirmados em 16 de outubro de 2026. Atualizações
exigem plano e aprovação novos, preservando o histórico.

- [Guia PT-PT](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/README.md)
- [Estado e publicação](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/STATUS.md)
- [Fornecedores e testes](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/PROVIDER_TESTING.md)

Copyright 2026 Sérgio Ribeiro. Apache License 2.0.

Read-only local candidate previews are available in source 0.3.0a12: [format and limits](https://github.com/herculespt/euromind-safeops/blob/main/docs/PREVIEW.md).
Previews locais sem escrita disponíveis no código 0.3.0a12: [formato e limites](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/PREVIEW.md).

Plan-bound local proposals are available in source 0.3.0a12: [workflow and limits](https://github.com/herculespt/euromind-safeops/blob/main/docs/PROPOSALS.md). They store candidate text locally without applying it or granting approval.
Propostas locais ligadas ao plano disponíveis no código 0.3.0a12: [procedimento e limites](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/PROPOSALS.md). Guardam o texto localmente sem o aplicar nem aprovar execução.

Separate local staging copies are available in source 0.3.0a12: [workflow and limits](https://github.com/herculespt/euromind-safeops/blob/main/docs/STAGING.md). Exact-fingerprint confirmation writes replacements only to a new copy; checks require fresh approval.
Cópias locais separadas disponíveis no código 0.3.0a12: [procedimento e limites](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/STAGING.md). A confirmação do fingerprint escreve só na cópia; os testes exigem aprovação nova.

Read-only historical stage inspection is available in source 0.3.0a12:
[contract](https://github.com/herculespt/euromind-safeops/blob/main/docs/STAGING.md).
`inspect-stage` reports filtered matching/changed/incomplete observations, without
file text, writes, current-source revalidation or execution/application approval.
Inspeção histórica sem escrita disponível no código 0.3.0a12:
[contrato PT-PT](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/STAGING.md).
Sem texto dos ficheiros, revalidação do original atual ou aprovação.
