# Aplicação revista ao original — 0.3.0a16

<!-- safeops-version: 0.3.0a16 -->

[English](../APPLICATION.md)

Implementado no código. A alfa pública GitHub/PyPI 0.3.0a8 é anterior a estes comandos.

Comandos: `review-application ID_DA_COPIA --run ID_DA_EXECUCAO`,
`apply-stage ID_DA_COPIA --run ID_DA_EXECUCAO --confirm FINGERPRINT_DA_REVISAO`,
`inspect-application ID_DA_APLICACAO` e
`rollback-application ID_DA_APLICACAO --confirm FINGERPRINT_DO_ROLLBACK`.

A revisão exige compatibilidade atual do original, cópia correspondente e execução
aprovada de compile e unit-tests ainda ligada aos inputs atuais da cópia, com a
mesma configuração do original. Não escreve nem concede permissão. A aplicação
exige fingerprint exato, guards nativos e revalidação. Não invoca fornecedores,
subprocessos ou operações Git.

Preparar backups privados limitados dos originais e substituições, seguindo-se
manifesto imutável com hash, antes de criar marcador próprio de operação pendente
ou escrever no original. Só substitui ficheiros de texto UTF-8 existentes e
graváveis, um de cada vez, preservando modo básico e proprietário/grupo POSIX
quando disponíveis. Não cria/elimina/renomeia caminhos do projeto. Ficheiros
internos de substituição no mesmo sistema de ficheiros e registos de controlo são
necessários; não há garantia de atomicidade de vários ficheiros. ACLs, atributos
estendidos e datas ficam fora do contrato inicial de metadados.

Após falha mantém backups, manifesto, substituições restantes e marcador pendente.
O marcador bloqueia execuções aprovadas e novas aplicações no original. A inspeção
mostra hashes/identidades atuais dos ficheiros candidatos sem conteúdo. O rollback
exige fingerprint de inspeção novo e exato, backups originais, identidades
conhecidas, conteúdos/modos atuais correspondentes e guard nativo. Recusa edições
concorrentes observáveis, ficheiros ausentes, caminhos inseguros e estado parcial
desconhecido; nunca força reposição nem descarta evidência automaticamente. Só
restaura ficheiros candidatos, preservando alterações não relacionadas.

Hashes/guards são evidência local cooperativa, não autenticação ou isolamento.
Revalidação não elimina corridas com autores não cooperantes nem alterações
transitórias/ABA. Leitores podem observar estados intermédios. Backups contêm
texto do código local e têm de permanecer privados e ignorados pelo Git. Metadados
públicos excluem conteúdo, output, tarefa/conselho, motivos de aprovação e
credenciais. Planos, aprovações, propostas, cópias, recibos e histórico Git existentes
são preservados.

## Procedimento controlado

1. No original, cria plano com caminhos explícitos, proposta local e cópia confirmada separadamente segundo [propostas](PROPOSALS.md) e [preparação](STAGING.md). Mantém o original inalterado. Não se reutiliza aprovação de execução original.
2. Inspeciona e confia no código copiado, inicializa a cópia e mantém a mesma configuração validada do original, com `compile` e `unit-tests` ativos. Cria/revê/aprova explicitamente plano novo na cópia e executa-o. Guarda o `run_id` devolvido. Recibo só de compile, histórico ou desatualizado não basta.
3. No original, executa a revisão sem escrita abaixo. Revê caminhos, hashes antes/depois, tamanhos e política de metadados. O fingerprint liga original, bytes de controlo, proposta, cópia, execução e versão/contrato atuais; a revisão não concede consentimento.
4. Só após revisão fornece o fingerprint exato a `apply-stage`. Repete-se a observação dupla sob ambos os guards nativos. Alterações observadas exigem nova revisão; texto de aprovação ou autorização anterior de checks não substituem esta confirmação.

```bash
safeops --json --root PROJETO_ORIGINAL review-application ID_DA_COPIA --run ID_DA_EXECUCAO
safeops --json --root PROJETO_ORIGINAL apply-stage ID_DA_COPIA --run ID_DA_EXECUCAO --confirm FINGERPRINT_DA_REVISAO
safeops --json --root PROJETO_ORIGINAL inspect-application ID_DA_APLICACAO
# Só depois de inspecionar os ficheiros atuais e o journal retido:
safeops --json --root PROJETO_ORIGINAL rollback-application ID_DA_APLICACAO --confirm FINGERPRINT_DO_ROLLBACK
```

O último comando usa `rollback_fingerprint` novo da inspeção, não o da revisão de aplicação. O rollback dispensa configuração, plano, aprovação e diretório de preparação atuais; exige journal/backups próprios válidos e correspondência dos ficheiros candidatos. Repetir rollback concluído é idempotente. Depois de aplicar ou repor, cria plano revisto/aprovação novos para checks seguintes.

## Estados, persistência e interrupção

Os registos privados ficam em `.safeops/applications/<12hex>/`. O intent schema 1 liga fingerprints de revisão/proposta/cópia/execução e, por caminho, hash, tamanho, identidade dispositivo/inode, modo básico, proprietário/grupo e observações temporais em nanossegundos antes/preparado. Backups: `backup-<index>.bin`; ficheiros novos/de reposição são consumidos por `os.replace` no mesmo sistema de ficheiros. `restore-<index>.json` imutável liga cada reposição antes da instalação. `applied.json` e `rolled-back.json` são conclusões schema 1 separadas ligadas ao fingerprint do intent. Há SHA-256 canónico sem chave e criação exclusiva; backups/controlos começam com modo 0600 e diretórios próprios com 0700 quando suportado. Substituições recebem metadados básicos originais.

| Observação | Significado e ação seguinte |
|---|---|
| Falha de preparação antes de intent/marcador válidos | O original não foi escrito; reter diretório parcial para revisão manual. Sem limpeza/reparação automática. |
| `pending` | Journal válido com marcador próprio retido ou sem conclusão correspondente. Inspecionar estados `original`, `applied`, `restored` e confirmar rollback se não houver conflito. |
| `applied` | Conclusão, candidatos correspondentes aos metadados instalados e ausência de marcador próprio. Histórico, sem aprovar execução nova. |
| `rolled-back` | Conclusão, candidatos correspondentes ao original/reposição própria e ausência de marcador próprio. |
| `conflicted` | Candidato com bytes/identidade/metadados diferentes. Preservar edições humanas; recusar rollback automático. |
| Erro de inspeção (2) | Journal, backup ou candidato ausente/inseguro/excessivo/alterado/inválido, ou artefacto parcial desconhecido. Reter evidência e investigar manualmente. |

Antes de cada escrita e depois da última aplicação, revalidam-se candidatos, snapshot/alvos do original, bytes de controlo, identidades dos diretórios do journal e contexto inalterado da cópia/execução. O rollback verifica candidatos/journal por passo e repõe só ficheiros aplicados, em ordem inversa. Interrupção depois do rename e antes do retorno pode ser reconhecida pela identidade/hash preparados. Intent de reposição válido com ficheiro preparado não consumido permite continuação explícita. Reposição parcial sem intent, backup corrompido, candidato ausente ou conclusão inválida são recusados; não há comando para forçar, reparar ou descartar.

A auditoria precede cada conclusão. Falhas de auditoria/gravação final/libertação do marcador podem devolver 2 após substituir parte ou todo o original; pode existir conclusão com estado `pending`. Inspeciona antes de repetir. Rollback confirmado de novo pode concluir reposição parcial conhecida ou libertar marcador próprio inalterado; nunca remove marcador de outro journal. `recover-lock` trata apenas `run.lock`, nunca `application.pending`. Terminação abrupta liberta guards nativos e preserva estado pendente; não se deduz atividade dos processos nem se decide recuperação automaticamente.

Ficheiros são descarregados/fsynced antes da substituição. Entradas dos diretórios não têm fsync: durabilidade após falha de energia/armazenamento e transações de vários ficheiros ficam fora do contrato. Locks coordenam apenas versões locais cooperantes; continuam possíveis leitores/autores não cooperantes. Modo básico Windows difere de POSIX; substituir ficheiro aberto externamente pode falhar. Sem garantia ACL/xattr/datas, sistemas de ficheiros de rede ou proteção contra proprietário hostil.

## Limites, saída e compatibilidade

- Candidato: 1–20 ficheiros existentes, até 256 000 bytes por original/substituição e 1 000 000 bytes combinados; regras LF/sem BOM/newline final do preview mantidas. Sem bits especiais nem modo de proprietário só de leitura; caminhos/antecessores seguros, ficheiros regulares sem hard links/reparse points.
- Registos: 64 000 bytes cada e até 85 artefactos conhecidos por aplicação. JSON UTF-8 estrito recusa chaves duplicadas, valores não finitos, campos extra, datas/IDs/fingerprints inválidos, metadados identidade/modo/tamanho incorretos e artefactos desconhecidos. Aplicam-se também limites de original/cópia/alvos/contexto da [revisão atual](STAGE_REVIEW.md) e dos [recibos](RUN_RECEIPTS.md).
- Revisão/inspeção não escrevem nem invocam fornecedores/código do projeto. Envelope comum schema 1. Inspeção devolve 0 em `applied`/`rolled-back`, 1 em `pending`/`conflicted`; erros operacionais/integridade tratados devolvem 2 sem detalhes sensíveis. Saída com caminhos, hashes, tamanhos e metadados locais, sem conteúdo. Revisão devolve `fingerprint`; inspeção devolve `rollback_fingerprint` e `rollback_candidate` pontual, que não concede permissão por si.
- Runner mantém protocolo 4; lock nativo passa a 2 porque qualquer entrada pendente bloqueia checks aprovados/aplicações novos. Mantêm-se configuração 1/2, plano 1, aprovação 2 e envelope 1. Atualizar exige planos/propostas/aprovações novos ligados à versão; journals schema 1 retidos permitem inspeção/recuperação independente com `version_matches`, sem renovar aprovação.

Regressões offline cobrem vários ficheiros, checks reais de confiança, terminação real do processo, aplicação/rollback parciais, falhas de auditoria/conclusão/libertação, confirmações antigas, edições humanas, identidade, caminhos inseguros e limites estritos. A mesma suite é usada com wheels instaladas e matriz SO/Python suportada. Sem pedido faturável nem aplicação real no repositório para estes testes. Geração de candidatos com IA, criar/eliminar/renomear, worktrees/escritas Git, proveniência assinada, isolamento pelo SO e contenção de processos hostis continuam planeados.

A maioria dos testes de ciclo/parser usa respostas sintéticas de checks bem-sucedidos; um caso separado executa compile/unittest aprovados reais. O teste de terminação abrupta executa aplicação num processo filho real e termina-o após a primeira substituição.

O código 0.3.0a16 acrescenta [supervisão dos processos próprios](SUPERVISION.md): launcher bloqueado à entrada, grupo/âncora PID POSIX ou job Windows com kill-on-close, confirmação nativa e caudas de output drenadas continuamente com limite. Timeout inclui descendentes normais próprios e pipes retidos; limpeza incerta mantém run.lock e intent incompleto sem recibo final. Runner 5/lock 3 exigem aprovação nova ligada à versão. Abrange descendentes cooperantes no grupo POSIX/membros do job, sem conter escapes deliberados de grupo/sessão, isolar código hostil ou decidir recuperação automática. O guia define conclusão, timeout, cancelamento e morte abrupta do principal.
