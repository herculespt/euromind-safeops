# CI e requisitos de construção do pacote

[English](../CI.md)

## Check obrigatório

O nome estável `quality-gate` mantém-se. O job executa com `always()` e só passa
quando a matriz dos nove ambientes e os dois jobs de distribuição passam.
Uma falha, cancelamento ou job ignorado não pode produzir um gate aprovado.
A proteção da branch exige também que a PR esteja atualizada.

A matriz cobre Python 3.11, 3.12 e 3.13 em Linux, Windows e macOS alojados pelo
GitHub. Cada ambiente instala o pacote, executa os testes, compila o código,
pesquisa padrões de credenciais e constrói uma wheel. Os jobs têm limites de
tempo explícitos.

## Actions revistas em 15 de outubro de 2026

| Action | Versão | Commit oficial |
|---|---|---|
| `actions/checkout` | v7.0.0 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/setup-python` | v7.0.0 | `5fda3b95a4ea91299a34e894583c3862153e4b97` |

Os SHAs foram obtidos nos repositórios oficiais e comparados com as notas de
versão e os metadados das Actions. Ambas utilizam Node 24 e requerem runner
2.327.1 ou posterior; este projeto utiliza runners alojados pelo GitHub.
As novas restrições do checkout v7 para PRs de forks afetam eventos
privilegiados `pull_request_target` / `workflow_run`, ausentes deste CI.
O parâmetro removido `pip-install` do setup-python não é utilizado;
`python-version` continua suportado.

O checkout define `persist-credentials: false`, porque os testes não fazem push.
O workflow mantém `contents: read`, não recebe segredos de produção e não
publica pacotes. O Dependabot continua a propor atualizações para os SHAs
fixados; as propostas têm de ser revistas antes da integração.

Os SHAs fixam as referências diretas das Actions. Não tornam imutáveis as imagens
dos runners, as versões Python descarregadas ou todas as dependências de
construção. Os lockfiles de workflows e a reprodução integral das builds ficam
para trabalho separado.

## Ferramentas e artefactos

Foi reproduzida a falha da versão mínima anterior, `setuptools>=68`, ao ler a
expressão SPDX da licença. Embora esse formato exija pelo menos a versão 77,
a versão mínima suportada e testada passa a ser **83.0.0**, incluindo correções
posteriores das dependências e dos padrões Unicode do manifesto. Mantém-se o
suporte a Python 3.11+. O setuptools já fornece o construtor de wheels, pelo
que deixa de ser necessária uma dependência separada e sem versão de `wheel`.
Não são adicionadas dependências externas em execução.

Os dois jobs de distribuição usam Linux / Python 3.11 e, respetivamente, a versão
exata 83.0.0 e a versão compatível mais recente de setuptools. Executam `python
-m build --no-isolation`, construindo a wheel a partir do arquivo de código com
a ferramenta selecionada. Verificam nome, versão, licença SPDX, ficheiro da
licença, marcador de tipos, ausência de dependências em execução, documentação
EN/PT-PT e ausência dos caminhos comuns de estado local e `.env`. Esta verificação
complementa a pesquisa por padrões e não prova a inexistência de todos os segredos.

O `MANIFEST.in` inclui documentos da comunidade, documentação, demonstração,
testes e ficheiros de CI necessários aos testes de organização. Exclui estado
gerado e ficheiros de ambiente. Cada job instala depois a wheel sem acesso ao
índice nem resolução de dependências, num ambiente virtual novo, e testa as duas
formas de iniciar a CLI fora do checkout. Nenhum artefacto é publicado.

## Revisão e reversão

Depois de o CI passar, rever o diff completo e integrar o commit testado. Se uma
alteração ao CI falhar após a integração, preparar uma PR de reversão com o mesmo
gate, preservando o histórico e as regras. As releases exigem autorização própria.

As [referências primárias](../CI.md#primary-references) constam do guia em inglês.
