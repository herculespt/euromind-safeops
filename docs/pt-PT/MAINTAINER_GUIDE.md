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
