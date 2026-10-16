# Primeira entrega alfa no GitHub e PyPI — 16 de outubro de 2026

[English](../../audits/2026-10-16-first-alpha.md)

O maintainer autorizou a primeira publicação. A [v0.3.0a8](https://github.com/herculespt/euromind-safeops/releases/tag/v0.3.0a8)
é uma **pré-release GitHub publicada**, no commit imutável
`035c36b1b646a6c75178d5db6c19d8c55d624dcf`. A documentação posterior da main
não move o tag nem substitui os ficheiros publicados.
Os mesmos ficheiros originais foram publicados no
[PyPI 0.3.0a8](https://pypi.org/project/euromind-safeops/0.3.0a8/) na mesma data.

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
| Trusted Publisher autorizado | `herculespt/euromind-safeops`, `publish.yml`, ambiente `pypi`; autorização expressa no momento da concessão em 16 de outubro de 2026 |
| Ambiente de publicação | Apenas branch selecionada `main`, uma branch/zero tags, bypass administrativo desativado; sem segredos ou variáveis e sem revisor obrigatório enquanto existir um maintainer |
| Entrega PyPI e instalação pelo registo | [38874124869](https://github.com/herculespt/euromind-safeops/actions/runs/38874124869), tentativa 1: três jobs aprovados, ficheiros originais obtidos sem reconstrução, suite da wheel com 209 testes/3 ignorados por plataforma, nomes/SHA-256 exatos e instalação limpa/versão CLI pelo registo verificados |
| Atestações de publicação | As páginas dos dois ficheiros mostram Trusted Publishing utilizado e atestação PyPI Publish assinada por GitHub Actions e verificada pelo PyPI em 16 de outubro de 2026; sujeitos e SHA-256 correspondem aos ficheiros abaixo |

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

**Entrega PyPI concluída.** As interrupções anteriores de acesso mantêm-se no
histórico da issue #31; a autenticação segura e a concessão autorizada ao publisher
foram depois concluídas. A wheel foi enviada às 08:31:15 UTC e a sdist às 08:31:17
UTC. O registo contém exatamente a wheel e a sdist originais, com os SHA-256
acima. SHA256SUMS mantém-se como anexo GitHub, sem upload como pacote no PyPI.

Foram inspecionados os [detalhes da wheel](https://pypi.org/project/euromind-safeops/0.3.0a8/#euromind_safeops-0.3.0a8-py3-none-any.whl)
e os [detalhes da sdist](https://pypi.org/project/euromind-safeops/0.3.0a8/#euromind_safeops-0.3.0a8.tar.gz).
Cada atestação identifica o repositório `herculespt/euromind-safeops`, workflow
`.github/workflows/publish.yml`, commit de publicação
`95a8bd51b2eb657233a9100f85c87be1b6548649` e execução 38874124869, tentativa 1.
Os índices do registo de transparência mostrados pelo PyPI são 3276393757 (wheel)
e 3276393456 (sdist). Estas observações confirmam a identidade da publicação
verificada pelo PyPI; não constituem verificação Sigstore local independente,
build reproduzível ou assinatura dos planos/aprovações SafeOps. O workflow correu
na main atual e obteve os ficheiros da release; o código do pacote mantém o
commit `035c36b1b646a6c75178d5db6c19d8c55d624dcf`.

Instalar a alfa publicada num ambiente virtual novo:

```powershell
python -m venv .venv
# Ativar o ambiente virtual na shell utilizada e depois executar:
python -m pip install --no-cache-dir --no-deps --index-url https://pypi.org/simple euromind-safeops==0.3.0a8
safeops --version
```

Na publicação PyPI, a main tinha código 0.3.0a11, com previews, propostas e cópias de preparação
posteriores, ausentes do pacote imutável 0.3.0a8. Atualizar documentação/notas da
release não reescreve a descrição incorporada no pacote publicado.

Não foram feitos novos pedidos a modelos. Os testes reais OpenAI/Anthropic
anteriores pertencem à versão 0.3.0a2. Neste tag continuam planeados propostas
de patches, preview de diffs, aplicação revista, isolamento pelo SO e supervisão
da árvore de processos. Consulta o [estado atual](../STATUS.md),
[roadmap](../../../ROADMAP.md) e [procedimento](../RELEASING.md).
