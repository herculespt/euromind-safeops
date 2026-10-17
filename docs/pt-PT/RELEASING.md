# Release alfa e publicação do pacote — 0.3.0a20

<!-- safeops-version: 0.3.0a20 -->

[English](../RELEASING.md)

O maintainer autorizou esta primeira entrega alfa em 15 de outubro de 2026.
Releases futuras exigem autorização própria. O [estado](STATUS.md) e a
[issue #31](https://github.com/herculespt/euromind-safeops/issues/31) registam a
publicação efetiva. Aprovar uma validação de candidato não publica no PyPI.

Primeira entrega alfa (16 de outubro de 2026): release GitHub e [PyPI 0.3.0a8](https://pypi.org/project/euromind-safeops/0.3.0a8/) publicados, com hashes dos ficheiros originais iguais, instalação limpa pelo registo e atestações de publicação verificadas pelo PyPI. O código atual mantém a versão 0.3.0a20. Consulta a [evidência verificada](audits/2026-10-16-first-alpha.md).

## Revisão e pré-release GitHub

Integrar por PR com proteção main ativa e todos os checks aprovados. Rever
commit/versão exatos, documentação EN/PT-PT, licença, conteúdo público e limites
alfa. Preservar histórico e evidência datada. As ferramentas diretas/transitivas usam hashes revistos em requirements-release.txt no perfil dedicado suportado; ver [política](TOOLING.md). Imagens dos runners e reprodução integral continuam separadas.

A descrição do pacote vem de [PACKAGE.md](../PACKAGE.md), bilingue e com ligações
absolutas para o registo. Validar metadados wheel/sdist com twine check --strict,
executar a suite completa da wheel fora do checkout e inspecionar código/pacotes
com scanner interno e independente, sem verificação de credenciais pela rede.
Os scanners não garantem ausência de todos os segredos.

Criar uma tag nova correspondente, como v0.3.0a8, no commit exato com CI de push
main aprovado. Não reutilizar/mover tags públicas. Publicar como Pre-release com
notas EN/PT-PT, testes/cobertura, aprovação de atualização e estado PyPI separado.
Anexar wheel, sdist e SHA256SUMS validados. Confirmar tag/commit, estado, notas e
nomes/bytes dos downloads. Os arquivos automáticos GitHub são distintos dos
pacotes construídos para o registo.


O scanner independente usa uma baseline de hashes revista para sete fixtures
sintéticas em três ficheiros de testes (revisão em 16 de outubro de 2026). Não
contém valores de credenciais nem exclui ficheiros de testes. O ficheiro de
controlo passa por um schema estrito antes de excluir os próprios hashes; a cópia
no pacote tem de corresponder aos bytes revistos do código. Um valor alterado
ou novo exige revisão; nunca regenerar a baseline apenas para aprovar a
publicação. Código seguido pelo Git e pacotes expandidos usam a mesma baseline,
com verificação de credenciais pela rede desativada.

## Workflow manual

[Alpha package publication](../../.github/workflows/publish.yml) só arranca
manualmente na main deste repositório, nunca por PR/tag/release. publish é falso
por predefinição. Sem tag valida apenas um candidato; uma tag expressa exige
uma release alfa GitHub existente e publicada.

A construção verifica ascendência main, o CI de push main mais recente para o
SHA exato, quality-gate e correspondência tag/versão alfa. O candidato é
construído do código. Com tag, obtém os ficheiros wheel/sdist/SHA256SUMS exatos
da release GitHub e valida nomes/hashes, preservando os bytes revistos para o
PyPI. Verifica metadados e toda a suite da wheel instalada. Guarda apenas
pacotes/checksums num artefacto Actions durante sete dias; não envia relatórios
de testes, JUnit, cobertura nem estado local.

Com publish=true e tag alfa expressa, um job separado no ambiente pypi verifica
SHA-256 e usa o publisher PyPA fixado. Só esse job recebe id-token: write, sem
checkout nem token permanente. A construção tem apenas leitura contents/actions.
O job final compara nomes/hashes reais no PyPI e instala a versão exata do
registo num ambiente novo, verificando metadados/CLI. Uma falha posterior de
verificação não desfaz o upload: inspecionar o estado antes de repetir e nunca
ignorar/substituir silenciosamente uma versão existente.

As Actions oficiais revistas são upload-artifact v7.0.2
(cf430e030ddbb5b0abf93d22962f4752f3646cd9), download-artifact v8.0.2
(9000827ccba6bdab643e8b6fd33ac0654aef8333) e publisher PyPA v1.14.2
(dc37677b2e1c63e2034f94d8a5b11f265b73ba33). Checkout/setup-python mantêm os
pins do [CI](CI.md). Só se afirmam attestations verificadas após examinar os
ficheiros reais do registo, embora o publisher as solicite.

## Conta e Trusted Publisher PyPI

Autenticar de forma segura na conta pretendida, com email/2FA conforme exigido.
Nunca enviar credenciais ou códigos de recuperação pelo chat, Git ou logs.
Configurar um publisher pendente para um projeto novo com estes campos exatos:

| Campo | Valor |
|---|---|
| Projeto PyPI | euromind-safeops |
| Proprietário GitHub | herculespt |
| Repositório | euromind-safeops |
| Nome do workflow | publish.yml |
| Ambiente GitHub | pypi |

Verificado em 16 de outubro de 2026: este publisher foi registado e utilizado
com sucesso. O ambiente GitHub `pypi` permite apenas a branch selecionada `main`
(uma branch, zero tags), sem bypass administrativo. Não tem segredos nem
variáveis configurados. Não exige revisores enquanto existir um maintainer.
Alterar esta relação de confiança ou reduzir proteções exige revisão expressa
e a confirmação administrativa aplicável.

Confirmar propriedade/disponibilidade do nome e rever a concessão exata antes
de gravar. Um publisher pendente não reserva o nome. Guardar o workflow no GitHub
não concede acesso ao PyPI. Não existe alternativa com API token configurada.
Verificar o publisher e proteções aplicáveis ao ambiente antes de publicar.
Após uma simulação aprovada, publicar apenas a alfa autorizada e registar URLs,
ficheiros/hashes, instalação e estado real das attestations. Manter PyPI pendente
se autenticação, registo ou verificação não estiverem concluídos.

## Alterações posteriores

Não reescrever tags nem substituir bytes públicos. Preparar uma correção revista
e nova versão autorizada; usar comunicação privada para segurança quando adequado.
Atualizações documentais do estado seguem por PR sem mudar a versão publicada,
distinguindo commit imutável da release e main atual. Mudanças de código,
configuração/versão exigem novo plano revisto e aprovação expressa no SafeOps,
sem renovação automática ou reescrita do histórico.

## Referências oficiais

- [Publisher pendente](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
- [Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
- [Modelo de segurança](https://docs.pypi.org/trusted-publishers/security-model/)
- [Publisher PyPA](https://github.com/pypa/gh-action-pypi-publish)

Preparar ferramentas fixadas a partir do código do workflow antes de selecionar o tag histórico. Tags antigos podem não ter locks; a política atual vem do workflow e a verificação dos ficheiros originais continua obrigatória.


Preparação Git no código 0.3.0a20: worktrees locais detached com confirmação própria e evidência de ligação schema 2; cópias simples mantêm schema 1. [Contrato](GIT_STAGING.md). Metadados Git partilhados não constituem isolamento; commits/pushes/PRs automáticos e proveniência SafeOps assinada não estão implementados. Aprovação/testes/aplicação mantêm gates explícitos. O pacote público GitHub/PyPI 0.3.0a8 mantém-se inalterado.
