# Guia de manutenção

[English](../MAINTAINER_GUIDE.md)

## Proteção verificada em 15 de outubro de 2026

Após autorização expressa do maintainer, foi criado e verificado o ruleset
[Protect main — 25151466](https://github.com/herculespt/euromind-safeops/rules/25151466),
com estado **Active** e alvo exclusivo `refs/heads/main`.

| Requisito | Configuração verificada |
|---|---|
| Pull request antes da integração | Obrigatório |
| Aprovações obrigatórias | 0, por existir um único maintainer |
| Check obrigatório | `quality-gate`, da origem GitHub Actions |
| Branch atualizada antes da integração | Obrigatório |
| Resolução de conversas de revisão | Obrigatória |
| Eliminação e force pushes | Bloqueados |
| Exceções de bypass | Nenhuma |

A API da branch confirmou `protected: true` e a conta autenticada recebeu
`current_user_can_bypass: never`. Esta verificação descreve o estado nessa data;
as definições podem ser alteradas por quem tenha permissões administrativas.

## Procedimento para alterações

1. Abrir uma Issue para alterações de comportamento, execução, permissões ou limites de confiança.
2. Criar uma branch a partir da `main` atual e manter a alteração limitada ao objetivo.
3. Rever o diff completo, executar os testes e atualizar a documentação em inglês e PT-PT, com UTF-8 correto.
4. Abrir uma pull request e aguardar o `quality-gate` dos nove ambientes e dos dois jobs de distribuição; consulta o [guia de CI](CI.md).
5. Resolver as conversas, confirmar que a branch continua atualizada e integrar o commit testado através da PR, com merge commit para preservar os commits e a ascendência da branch.
6. Pedir autorização para alterações administrativas sensíveis e publicação de releases.

Nunca introduzir código proprietário, credenciais ou dados de utilizadores.
Não utilizar force push. Os resultados dos modelos são aconselhamento e não
substituem a revisão humana. Os testes executam código com os privilégios do
operador; a ferramenta não implementa isolamento seguro.

Os passos de reprodução das regras e de publicação constam do
[guia em inglês](../MAINTAINER_GUIDE.md) e do
[procedimento de releases](../RELEASING.md). Consulta também a
[auditoria](audits/2026-10-15.md).

Nas alterações da política de execução, atualizar em conjunto a versão, os
guias EN/PT-PT, o estado implementado/planeado e as notas de atualização. Com
alvos de schema 2, rever a integridade do workspace e dos ficheiros selecionados;
[as caches geradas](TARGETS.md) podem invalidar uma execução posterior. Antes de
fechar a issue, atualizar a lista de critérios e o texto da PR com evidência real
do CI da PR/main, limites restantes e estado de publicação.

Nas alterações JSON/CI, verificar o [contrato do envelope](OUTPUT.md), a saída
predefinida e os códigos do processo. Inspecionar resumos e logs em cada job da
matriz/distribuição. Os totais não substituem o gate nem provam cobertura; manter
outros perfis de cobertura/publicação de relatórios como planeados. Rever o
[gate de cobertura](COVERAGE.md), sonda de subprocessos e exclusões antes de alterar
o mínimo de 90%; nunca reduzi-lo para esconder uma regressão. Inspecionar o [JUnit local](REPORTING.md),
mapeamento de categorias e erros do runner; os identificadores sintéticos não
identificam o teste-fonte que falhou. Rever os dados antes de qualquer upload
de relatórios ou logs normais.

Nas interrupções, seguir a [recuperação do bloqueio](LOCKING.md): verificar de
forma independente os processos principais/filhos, rever o fingerprint e
arquivar com confirmação e razão expressas. Nunca apagar a guarda nem deduzir
o estado dos processos pelo PID. Rever recibo/arquivo/auditoria após um erro;
a recuperação não é uma transação única nem concede aprovação de execução.

O comando de [preview de candidatos](PREVIEW.md) só lê e é independente da
aprovação de execução. Rever diffs localmente: podem conter texto ou segredos,
sem upload automático com relatórios. Não implementa geração por IA ou aplicação
revista de patches.

Nas [propostas persistentes](PROPOSALS.md), revê caminhos exatos explícitos, ligações, privacidade do armazenamento e rejeição de registos alterados/desatualizados. Não publiques texto, registos ou diffs automaticamente. A auditoria pode falhar depois da gravação da proposta: inspeciona o estado antes de repetir. Aplicação explícita tem [contrato separado](APPLICATION.md); geração com IA continua planeada.

Nas [cópias locais](STAGING.md), revê exclusões, escrita independente, confirmação do fingerprint e estado retido nas falhas. O recibo não é sandbox nem aprovação de aplicação ao original. Não elimines cópias parciais nem publiques conteúdo automaticamente. As verificações exigem aprovação nova; ambiente/dependências podem precisar de preparação separada.

## Observação da entrega no registo — 16 de outubro de 2026

A primeira [alfa PyPI 0.3.0a8](https://pypi.org/project/euromind-safeops/0.3.0a8/)
está publicada; a main tinha código 0.3.0a11 nessa entrega. Consulta o [estado atual](STATUS.md). O Trusted Publisher
exato é `herculespt/euromind-safeops`, `publish.yml`, ambiente `pypi`. Esse ambiente
permite apenas a branch `main`, zero tags e nenhum bypass administrativo; não
tem segredos/variáveis nem revisores obrigatórios. A publicação continua manual,
com tag alfa existente expressa e `publish=true`. Preservar estas regras do
ambiente e da main, rever alterações de confiança e manter os ficheiros públicos
imutáveis. Registar hashes, instalação limpa e atestações reais de publicação
separadamente da versão do código e das aprovações de execução SafeOps.
Consulta a [evidência de entrega](audits/2026-10-16-first-alpha.md).

Em `inspect-stage` (código 0.3.0a12), rever a ligação histórica e o resultado da
cópia filtrada separadamente do original atual e dos testes. Código 1 com dados
indica alteração/cópia incompleta; evidência inválida ou insegura devolve 2.
Preservar todos os registos. Validar exclusões, limites/caminhos, ausência de
texto dos ficheiros e de escrita em auditoria/aprovações, incluindo na wheel.

O código 0.3.0a15 acrescenta [aplicação revista e rollback conservador](APPLICATION.md). Ambos os checks fixos da cópia têm de passar com ligações atuais inalteradas e configuração igual à do original; confirmação humana exata e guards nativos precedem backups/journal privados e escrita. Marcador pendente bloqueia checks aprovados/aplicações novos. Inspeção sem escrita e rollback confirmado separadamente preservam evidência e recusam edições humanas observadas. Sem transação de vários ficheiros, garantia de energia/armazenamento, operações Git, pedidos a fornecedores ou isolamento pelo SO. Nesse marco, runner 4/lock 2; aprovação de execução nova ligada à versão obrigatória.

O código 0.3.0a16 acrescenta [supervisão dos processos próprios](SUPERVISION.md): launcher bloqueado à entrada, grupo/âncora PID POSIX ou job Windows com kill-on-close, confirmação nativa e caudas de output drenadas continuamente com limite. Timeout inclui descendentes normais próprios e pipes retidos; limpeza incerta mantém run.lock e intent incompleto sem recibo final. Runner 5/lock 3 exigem aprovação nova ligada à versão. Abrange descendentes cooperantes no grupo POSIX/membros do job, sem conter escapes deliberados de grupo/sessão, isolar código hostil ou decidir recuperação automática. O guia define conclusão, timeout, cancelamento e morte abrupta do principal.

O código 0.3.0a17 aguarda contagem final zero do job Windows no mesmo orçamento de limpeza de três segundos usado para saída do launcher, EOF e limpeza de falha. Contagem positiva transitória não transforma imediatamente um check falhado concluído em erro operacional; confirmação persistente/indisponível mantém recusa e estado retido. Diagnóstico por fases fixas exclui texto nativo de exceções. Mantêm-se runner 5/lock 3 e schemas; versão/política de limpeza atualizadas exigem planos/propostas/aprovações novos e revistos.

Ferramentas de cobertura/release usam conjuntos transitivos de wheels/hashes revistos em perfis Linux/CPython 3.12 dedicados. A [política](TOOLING.md) define instalação/recusa, atualização e exceções dos jobs de compatibilidade. Não fixa o bootstrap do runner/intérprete nem certifica segurança das dependências.
