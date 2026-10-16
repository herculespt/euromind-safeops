# Primeira entrega alpha no GitHub — 16 de outubro de 2026

[English](../../audits/2026-10-16-first-alpha.md)

O maintainer autorizou a primeira publicação. A [v0.3.0a8](https://github.com/herculespt/euromind-safeops/releases/tag/v0.3.0a8)
é uma **pré-release GitHub publicada**, no commit imutável
`035c36b1b646a6c75178d5db6c19d8c55d624dcf`. A documentação posterior da main
não move o tag nem substitui os ficheiros publicados.

| Evidência | Resultado verificado |
|---|---|
| Main protegida | Ruleset 25151466 ativo; PR, quality-gate estrito, conversas resolvidas, zero aprovações obrigatórias, sem eliminação/force push/bypass |
| Integração | PRs #33 e #34 integradas após doze jobs aprovados em cada uma |
| CI do commit exato | [38838771250](https://github.com/herculespt/euromind-safeops/actions/runs/38838771250): doze jobs aprovados |
| Candidato | [38838948133](https://github.com/herculespt/euromind-safeops/actions/runs/38838948133): aprovado, publish=false |
| Ficheiros publicados | [38839267524](https://github.com/herculespt/euromind-safeops/actions/runs/38839267524): download do wheel/sdist/SHA256SUMS exatos; hashes, metadados, scans e testes instalados aprovados; publish=false |
| Wheel anexo instalado localmente | Fora do checkout: 209 testes, 3 ignorados por plataforma, zero falhas/erros; Twine estrito aprovado |
| Scan independente | Sem verificação de credenciais pela rede; sete identidades sintéticas revistas no código/sdist e zero findings no wheel; valores novos e baseline inválida rejeitados |
| Comparação privada | Valores das credenciais locais ausentes do código público e pacotes expandidos, sem expor valores em logs ou uploads |
| Anexos | Um wheel, uma sdist construída e SHA256SUMS; digests dos anexos GitHub correspondentes; ZIP/tar do código gerados pelo GitHub são ligações adicionais |

O primeiro [candidato 38836891550](https://github.com/herculespt/euromind-safeops/actions/runs/38836891550)
falhou em fixtures sintéticas. A PR #34 acrescentou a política estrita de hashes
revistos e nove testes de regressão, sem excluir ficheiros de testes. A evidência
da falha mantém-se no histórico.

```text
559e2b89c8d80d02562605c8a517b7b2096d4df9e9958eb35fbe93cdca18436c  packages/euromind_safeops-0.3.0a8-py3-none-any.whl
ff2bae29339d1ac5b9177711409d5e363575de6cda12e902035755f7367a2958  packages/euromind_safeops-0.3.0a8.tar.gz
```

Descarregar SHA256SUMS e colocar os dois pacotes numa subpasta `packages/`.
Executar `sha256sum --check SHA256SUMS` antes da instalação do wheel verificado.
Isto não demonstra builds integralmente reproduzíveis ou proveniência assinada.

**PyPI pendente.** O pedido seguro de autenticação foi interrompido; na última
verificação a conta continuava a exigir login. Não foram verificados registo do
Trusted Publisher, upload, instalação pelo registo ou atestações. O workflow OIDC
está preparado e só foi executado com publicação desativada.

Não foram feitos novos pedidos a modelos. Os testes reais OpenAI/Anthropic
anteriores pertencem à versão 0.3.0a2. Neste tag continuam planeados propostas
de patches, preview de diffs, aplicação revista, isolamento pelo SO e supervisão
da árvore de processos. Consulta o [estado atual](../STATUS.md),
[roadmap](../../../ROADMAP.md) e [procedimento](../RELEASING.md).
