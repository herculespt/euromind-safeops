# EuroMind SafeOps — 0.3.0a9 alpha

<!-- safeops-version: 0.3.0a9 -->

A Python 3.11+ command-line tool for advisory engineering plans, explicit human
approval and fixed compile/unittest checks. Apache-2.0; no third-party runtime
dependencies. Optional OpenAI, Anthropic and compatible endpoints provide advice
only, with explicit remote consent.

This is an **alpha development tool**. Tests execute trusted Python with the
operator's privileges. Local hashes, audit records and cooperative locks are not
a sandbox, signatures or protection against a malicious local actor. Empty or
wholly skipped test suites fail. Changing code, configuration or package version
requires a fresh reviewed plan and explicit approval.

For a published PyPI alpha, select the exact version:

~~~bash
python -m pip install euromind-safeops==0.3.0a9
safeops --version
~~~

Source installation remains available from the
[GitHub repository](https://github.com/herculespt/euromind-safeops).
See [publication status](https://github.com/herculespt/euromind-safeops/blob/main/docs/STATUS.md)
before assuming a registry delivery exists.

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
uma versão exata quando publicada no PyPI. Atualizações exigem plano e aprovação
novos, preservando o histórico.

- [Guia PT-PT](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/README.md)
- [Estado e publicação](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/STATUS.md)
- [Fornecedores e testes](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/PROVIDER_TESTING.md)

Copyright 2026 Sérgio Ribeiro. Apache License 2.0.

Read-only local candidate previews are available in source 0.3.0a9: [format and limits](https://github.com/herculespt/euromind-safeops/blob/main/docs/PREVIEW.md).
Previews locais sem escrita disponíveis no código 0.3.0a9: [formato e limites](https://github.com/herculespt/euromind-safeops/blob/main/docs/pt-PT/PREVIEW.md).
