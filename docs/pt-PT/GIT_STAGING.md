# Worktrees Git de preparação explícita — 0.3.0a20

<!-- safeops-version: 0.3.0a20 -->

[English](../GIT_STAGING.md)

Modo opcional implementado. `stage-proposal` continua a criar uma cópia simples,
independente, com evidência schema 1 e sem invocar Git. Não depende de conta,
saldo de fornecedor ou manifestos de especialistas.

Executar localmente `review-git-stage PROPOSAL_ID`, ler a saída completa e só
depois `stage-git-proposal PROPOSAL_ID --confirm FINGERPRINT`. O fingerprint da
proposta simples não autoriza operações Git. A revisão invoca comandos locais
Git sem mutação e captura output temporário em disco fora do projeto; não cria
cópias, modifica Git, concede aprovação nem acede à rede/fornecedores. A confirmação
liga proposta/código/versão/política, caminho do Git instalado, commit base,
HEAD/índice/configuração/refs originais e hashes das entradas. Os caminhos e hashes
locais podem ser privados; não publicar a revisão indiscriminadamente.

Suporte inicial: worktree principal de repositório SHA-1, diretório `.git` regular,
commit existente, índice igual à base e bytes literais dos ficheiros regulares
iguais aos blobs. Todos os ficheiros incluídos têm de estar versionados e todos
os versionados têm de ser incluídos. Recusam-se alterações/untracked incluídos,
índice alterado, links/reparse points/hardlinks, submódulos, ficheiros versionados
internos/gerados/de ambiente, includes/configuração por worktree, repositórios sem
commit/bare/raiz ligada/SHA-256 e caminhos portáveis ambíguos. Ficheiros de ambiente
convencionais não versionados são omitidos da cópia e permanecem no snapshot do
original. Autocrlf/filtros podem causar recusa mesmo com `git status` limpo; não
há normalização, reset ou sobrescrita automática do original.

A criação adquire o guard nativo/marcador próprios do original e recusa checks
ativos, marcadores antigos ou aplicação pendente. Cria exclusivamente
`.safeops/stages/<id>/`, grava **intent schema 2 antes da mutação Git**, regista
um worktree detached e locked através de `worktree add --no-checkout`, inicializa
apenas o índice novo com `read-tree` e copia o código revisto/substituições com o
writer regular existente. Não expõe shell, filtros/hooks de checkout, inicialização
de submódulos, criação de branches, commits, fetch, push, force ou remoção/prune/
unlock automáticos. Herda apenas uma pequena lista de variáveis do SO; configuração
global/sistema, credenciais interativas, objetos substituídos, hooks, fsmonitor e
manutenção automática ficam desativados nestas operações fixas. O Git instalado e
o repositório/base de objetos local de confiança continuam fronteiras externas.

Limites existentes: 5 000 ficheiros, 12 000 000 bytes por ficheiro, 64 000 000 bytes
copiados e recibo de 1 000 000 bytes. Contexto Git limitado a 3 000 bytes JSON canónicos antes de criar o stage, mantendo o intent dentro dos 4 096 bytes de inspeção. Output Git interpretado limitado a 2 000 000
bytes e timeout de 15 segundos por comando, com erros sanitizados. Captura em disco
evita parsing em memória ilimitado; não impõe quota rígida do disco temporário,
prazo global ou contenção de processos hostis. Não aceita argumentos, executáveis
ou ambientes Git arbitrários; o caminho guardado tem de corresponder ao Git
instalado atualmente resolvido antes de qualquer invocação de inspeção.

O recibo só é gravado após revalidar código copiado, proposta, Git original e
ligação/base/índice novos. Intent/recibo schema 2 acrescentam contexto Git limitado;
propostas mantêm schemas 1 manual / 2 IA. `inspect-stage` suporta cópias schema 1
e Git schema 2; verifica ponteiro, diretório comum, backlink, lock, base detached e
digest do índice antes/depois dos scans. A inspeção histórica não exige que o
código/índice original continue atual, mas precisa do Git instalado, metadados
ligados e localização original do repositório. Mover/reparar/commitar/desbloquear
pode exigir inspeção humana fora deste contrato inicial. Não há reparação automática.

Falhas conservam diretórios parciais, intent e eventual worktree locked; ausência
de recibo significa incompleto. Uma falha de auditoria/persistência pode conservar
uma cópia válida não aprovada. Inspecionar evidência e registo Git antes de recuperação
manual autorizada; não eliminar automaticamente. Persistem corridas de filesystem
e alterações por clientes Git externos; o guard só coordena operações cooperativas.

Continuar explicitamente com `init` na cópia, novo plano/aprovação, compile e testes,
revisão atual/aplicação ao original, confirmação exata e rollback conservador. Nada
disso é automático. A preparação preserva índice, HEAD, refs e código originais;
uma aplicação posterior explicitamente aprovada pode substituir texto original,
mantendo a integração Git sob controlo do maintainer. O ficheiro regular `.git`
passa a ser excluído dos digests como já acontecia com diretórios `.git`; a ligação
dos stages Git é verificada separadamente. A atualização exige novos planos/
propostas/aprovações; histórico preservado e inspeção de cópias simples sem Git.

Worktrees ligados partilham objetos, configuração e muitas refs. Diretório distinto
**não é isolamento pelo SO**. Proveniência SafeOps autenticada continua planeada
em [#61](https://github.com/herculespt/euromind-safeops/issues/61): identidade do
signatário, declaração canónica, confiança/rotação/revogação e verificação antes
de conceder autoridade de assinatura. As atestações GitHub/PyPI existentes são de
publicação, não de aprovações/recibos SafeOps. Não se criam identidades de assinatura,
credenciais, releases ou publicação PyPI neste marco.

Referências: [worktrees](https://git-scm.com/docs/git-worktree),
[read-tree](https://git-scm.com/docs/git-read-tree),
[hooks](https://git-scm.com/docs/githooks).
