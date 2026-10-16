# Recibos dos checks aprovados — 0.3.0a19

<!-- safeops-version: 0.3.0a19 -->

[English](../RUN_RECEIPTS.md)

`run ID_DO_PLANO` continua a exigir plano não crítico revisto e aprovação de
execução explícita e válida. Atribui agora um ID aleatório de 12 caracteres
hexadecimais minúsculos e regista metadados limitados em
`.safeops/runs/ID_DA_EXECUCAO/`. Os IDs são exclusivos: uma colisão falha sem
sobrescrever nem repetir automaticamente.

```bash
safeops --json --root PROJETO run ID_DO_PLANO
safeops --json --root PROJETO inspect-run ID_DA_EXECUCAO
```

Só `run` invoca os checks fixos. `inspect-run` lê evidência retida sem escrita,
importação de código do projeto, fornecedores, execução de checks, auditoria ou
aprovação. Não exige os ficheiros atuais de configuração/plano/aprovação nem
compatibilidade com o original atual. Mantém estes registos fora do Git público.

## Ciclo de vida e falhas

1. Lê plano/âmbito com segurança, adquire o guard nativo/marcador existente e
   compara duas observações limitadas dos ficheiros de controlo/original/alvos.
   Rejeita aprovação desatualizada antes de atribuir execução ou iniciar checks.
2. Cria exclusivamente `intent.json` antes do primeiro processo filho. Regista
   schema 1, IDs, início UTC, versão SafeOps, checks fixos ativados por ordem,
   timeout por check, ligações iniciais em `bindings` e fingerprint canónico.
3. Após **cada** check concluído, compara duas observações adicionais. Para antes
   do seguinte se falhou/excedeu timeout, os inputs mudaram ou não puderam ser
   observados em segurança. O retorno zero do filho, por si só, não estabelece
   que o contexto testado se manteve igual.
4. Após limpeza bem-sucedida do marcador próprio/libertação do guard nativo,
   acrescenta o estado observado à auditoria. Só depois cria `receipt.json`
   exclusivamente. A finalização ocorre fora do guard; os hashes descrevem os
   inputs observados, sem congelar o sistema de ficheiros até/depois da gravação.
   Outra execução pode entretanto começar.
5. Falhas de inicialização, arranque do filho, limpeza do lock, auditoria ou
   gravação final devolvem erro operacional 2 e preservam evidência. Não há
   repetição, limpeza, reparação, rollback ou renovação de aprovação automáticos.
   Recibo final ausente significa execução incompleta; ficheiro parcial/inválido
   origina erro de integridade.

O estado da auditoria descreve checks/inputs observados, sem provar gravação do
recibo final. Uma falha de escrita após auditoria pode deixar evento sem recibo;
a saída 2 continua a ser falha. Falha de limpeza/auditoria nunca cria recibo final.
Terminação abrupta pode deixar intenção e marcador bloqueante; utiliza a
[recuperação independente do lock](LOCKING.md), com verificação humana.

| `status` da execução/inspeção | Saída CLI | Significado |
|---|---:|---|
| `passed` | 0 | Todos os checks ativados passaram e o contexto observado manteve-se igual |
| `failed` | 1 | Check registado falhou, com contexto observável igual |
| `timed-out` | 1 | Check registado excedeu timeout, com contexto observável igual |
| `changed-inputs` | 1 | Alguma ligação observada mudou, independentemente do resultado dos filhos |
| `incomplete` | 1 | Contexto após check indisponível, ou intenção válida sem recibo final na inspeção |
| Erro tratado de política/armazenamento/utilização/integridade | 2 | Sem resultado de sucesso; inspecionar evidência antes de decidir próximos passos |

Cada check registado contém apenas `check`, `status` (`passed`, `failed`,
`timed-out`) e `exit_code` inteiro. A ordem tem de ser um prefixo dos checks
ativados; um check que não passou termina a sequência. Timeout utiliza -1 e mantém
o limite 1–300 segundos por check. `changed-inputs` prevalece sobre timeout/falha;
contexto posterior indisponível prevalece sobre todos os resultados.

`run` mantém o output dos checks no resultado devolvido e acrescenta `run_id`,
`receipt_fingerprint` e `reasons` fixos. O envelope JSON mantém schema 1. Devolve
os últimos 12 000 caracteres de stdout/stderr de cada check; a captura pelo
subprocesso drena continuamente caudas limitadas a 65 536 bytes por stream. Os recibos nunca
persistem esse output, tarefa/conselho, motivos de aprovação, caminhos arbitrários
ou detalhes brutos do SO. O output devolvido pode continuar a ser sensível.

## Ligações e contrato de inspeção

As ligações iniciais `bindings` e finais `end_context` têm exatamente estas chaves:

| Chave | Observação registada |
|---|---|
| `plan_fingerprint` | Fingerprint do plano guardado |
| `plan_digest` | Hash canónico do registo completo do plano atual |
| `approval_digest` | Hash canónico da aprovação completa, incluindo o motivo sem o divulgar |
| `workspace_digest` | Snapshot limitado do conteúdo original |
| `config_digest` | Hash canónico da configuração schema 1/2 validada |
| `targets_digest` | Digest limitado dos ficheiros selecionados no schema 2; `null` no schema 1 |
| `execution_contract` | Versão instalada e contrato fixo de runner/lock/checks/ambiente/recibos |

O registo final contém schema/ID, fingerprint da intenção, fim UTC, estado,
contexto final (ou `null` se indisponível), resultados dos checks, motivos e
fingerprint próprio. Os fingerprints usam JSON canónico omitindo só o próprio
`fingerprint`. São registos locais, mutáveis e sem chave, não assinaturas.

Motivos fixos, por ordem: `plan-changed`, `approval-changed`, `source-changed`,
`configuration-changed`, `selected-targets-changed`, `execution-contract-changed`.
Contexto posterior indisponível utiliza `postcheck-context-unavailable`; recibo
final ausente na inspeção utiliza `completion-receipt-absent`.

`inspect-run` valida campos exatos, schema/tipos inteiros, hashes canónicos, IDs,
datas, nomes/ordem/resultados dos checks e coerência entre estado/motivos/contexto.
Relê ficheiros e identidades dos diretórios antes de devolver. Inclui versão
registada, `version_matches`, IDs/fingerprints, datas, ligações/metadados e
`source_context: "historical-binding-only"`. Um recibo histórico aprovado continua
inspecionável com saída 0 após atualização/alterações ou remoção dos ficheiros
atuais de plano/aprovação/configuração. Não renova aprovação nem afirma que o
original ainda corresponde agora. Evidência não suportada/inválida/insegura/
demasiado grande/ilegível/em alteração devolve erro de política fixo saneado,
com `data: null`.

## Limites e compatibilidade

Intenção/recibo têm limite individual de 16 000 bytes; cada ficheiro de controlo,
256 000 bytes. Leituras rejeitam chaves duplicadas, números não finitos,
UTF-8/JSON não suportado, ligações/reparse points, ficheiros não regulares e
hardlinks. Diretórios/ficheiros novos pedem modos 0700/0600, sujeitos a ACLs/umask.
Escritas exclusivas fazem flush/fsync e releitura; interrupções podem deixar
ficheiros parciais. A auditoria utiliza abertura estrita regular/não bloqueante,
rejeitando ligações, reparse points, hardlinks e FIFOs. Não acrescenta isolamento
contra um autor hostil.

As observações reutilizam os limites da [revisão do original](STAGE_REVIEW.md):
5 000 ficheiros, 12 MB por ficheiro, 64 MB total por leitura do original/alvos;
10 000 entradas/64 níveis no original e 5 000 entradas de metadados por check
selecionado. Ficheiros de ambiente do original são processados localmente para
hash, sem devolução de conteúdo; dados gerados selecionados continuam incluídos.
Diretórios gerados convencionais são excluídos apenas do digest normal do
original. Metadados e alterações de diretórios vazios não são ligados.

O protocolo **5** do runner liga schema 1 dos recibos e
`PYTHONDONTWRITEBYTECODE=1` em todos os filhos Python fixos. Suprime bytecode
automático dos imports, permitindo que testes normais de schema 2 preservem
os inputs selecionados. `compileall` explícito do schema 1 continua a escrever
bytecode gerado; testes também podem escrever ficheiros explicitamente.
Mantêm-se streams UTF-8, configuração 1/2, plano 1, aprovação 2, envelope 1 e
protocolo nativo do lock 3. Atualizar para 0.3.0a19 exige plano/aprovação novos e
revistos; o histórico é preservado.

Snapshots e observações duplas são evidência pontual: não detetam todas as
alterações transitórias/ABA, provam asserções, contêm descendentes que deliberadamente escapam ou
restringem acesso ao sistema de ficheiros pelo Python de confiança. Um autor
local malicioso pode reescrever todos os registos. `passed` só indica que os checks
ativados passaram com inputs observados iguais; configuração só com compile não
prova testes unitários. Este comando de recibos não aplica ao original. [Aplicação explícita/rollback](APPLICATION.md) estão implementados separadamente; operações Git, proveniência autenticada e sandbox pelo SO continuam por implementar. A alfa pública
GitHub/PyPI mantém-se em 0.3.0a8.

O código 0.3.0a16 acrescenta [supervisão dos processos próprios](SUPERVISION.md): launcher bloqueado à entrada, grupo/âncora PID POSIX ou job Windows com kill-on-close, confirmação nativa e caudas de output drenadas continuamente com limite. Timeout inclui descendentes normais próprios e pipes retidos; limpeza incerta mantém run.lock e intent incompleto sem recibo final. Runner 5/lock 3 exigem aprovação nova ligada à versão. Abrange descendentes cooperantes no grupo POSIX/membros do job, sem conter escapes deliberados de grupo/sessão, isolar código hostil ou decidir recuperação automática. O guia define conclusão, timeout, cancelamento e morte abrupta do principal.

O código 0.3.0a19 aguarda contagem final zero do job Windows no mesmo orçamento de limpeza de três segundos usado para saída do launcher, EOF e limpeza de falha. Contagem positiva transitória não transforma imediatamente um check falhado concluído em erro operacional; confirmação persistente/indisponível mantém recusa e estado retido. Diagnóstico por fases fixas exclui texto nativo de exceções. Mantêm-se runner 5/lock 3 e schemas; versão/política de limpeza atualizadas exigem planos/propostas/aprovações novos e revistos.
