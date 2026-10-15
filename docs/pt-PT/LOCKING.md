# Bloqueio local e recuperação — 0.3.0a8

<!-- safeops-version: 0.3.0a8 -->

[English](../LOCKING.md)

A execução combina uma guarda nativa persistente e um marcador com proprietário.
Não constitui isolamento nem bloqueio distribuído. A versão 0.3.0a8 usa protocolo
3 do runner e protocolo 1 do bloqueio no contrato ligado à versão. Mantêm-se os
schemas 1/2 de configuração, 1 de plano, 2 de aprovação e 1 da saída. Atualizar
exige plano/aprovação novos e revistos; não há migração dos registos.

## Guarda e marcador

- `.safeops/run.guard` é um ficheiro regular vazio e persistente. POSIX usa
  `fcntl.flock` sem espera; Windows usa `msvcrt.locking` sem espera no primeiro
  byte, incluindo além do fim do ficheiro. Bloqueio indisponível/não suportado
  falha; não existe execução alternativa sem proteção.
- O descritor não é herdável. Mantém-se aberto durante a validação de aprovação,
  configuração e snapshots e as verificações fixas. Nunca apagar/substituir este
  ficheiro: outro processo pode já ter um descritor associado.
- `.safeops/run.lock` é criado exclusivamente depois de obter a guarda. O JSON
  de schema 1 regista PID, ID do plano, token aleatório de propriedade e data UTC.
  A guarda mantém-se até ao fim da validação/verificações e limpeza do marcador.
- O fim/erro normal remove apenas o marcador próprio e inalterado, verificando
  identidade e conteúdo exato. Marcadores alterados, ausentes ou inseguros
  produzem erro. Uma falha de limpeza não gera uma auditoria de execução aprovada.
  Falhar a inicialização retém qualquer marcador parcial para inspeção.
- A morte abrupta do processo principal liberta o bloqueio nativo, mas deixa o
  marcador a bloquear execuções posteriores. Marcadores antigos só com PID,
  parciais ou desconhecidos também bloqueiam. Não há remoção automática nem
  classificação de obsolescência baseada no PID.

As operações rejeitam ligações simbólicas/quebradas, reparse points/junctions,
objetos não regulares e aliases por hard link nos ficheiros de bloqueio, assim
como diretórios de estado/recuperação com ligações. São lidos até 4 096 bytes do
marcador; estado maior ou inacessível exige investigação independente. As
verificações repetem-se nas etapas, sem atomicidade contra um proprietário local
que altere o sistema de ficheiros.

## Diagnóstico

```powershell
safeops --json --root examples/demo_project doctor
```

Usar um workspace inicializado. `data.run_lock` apresenta `guard` (`absent`,
`free` ou `busy`), presença, SHA-256 `marker_fingerprint`, formato (`record-v1`,
`legacy-pid`, `unrecognized`), PID/plano reconhecidos e aviso dos limites. Estado
inseguro ou operações não suportadas produzem um erro controlado.

O diagnóstico não cria/remove ficheiros nem mostra os bytes do marcador. Testa
brevemente uma guarda existente sem esperar e liberta-a. São observações do
momento: `busy` pode indicar uma operação nativa ativa; `free` ou um PID ausente,
morto ou reutilizado nunca demonstram que os processos filhos terminaram.

## Recuperação explícita

1. Inspecionar de forma independente os processos de verificação principais **e
   filhos**. Terminar/concluir e verificar que não restam verificações ativas.
   Nunca confirmar enquanto estiverem a correr; o comando não termina processos
   nem deduz o seu estado de execução.
2. Executar novamente `doctor` e rever formato e fingerprint exatos do marcador.
3. Só após a verificação, substituir `MARKER_SHA256` abaixo pelo fingerprint de
   64 caracteres, indicar uma razão concreta e confirmar a inspeção dos processos:

```powershell
safeops --json --root examples/demo_project recover-lock --confirm MARKER_SHA256 --reason "Verifiquei que as verificações principais e filhas terminaram" --confirm-no-running-checks
```

O comando exige todas as confirmações, fingerprint correspondente e guarda livre.
Volta a verificar identidade/conteúdo antes de mover os bytes originais para
`.safeops/recovered-locks/<id-aleatório>/run.lock`. O `receipt.json` guarda ação
pedida, fingerprint/formato, razão, confirmação e data UTC. Um evento de auditoria
liga o ID do diretório. Planos/aprovações não são alterados; não executa
verificações nem concede aprovação. Rever alterações interrompidas e preferir
plano/aprovação novos e revistos antes de executar.

O resultado inclui caminhos relativos do arquivo e recibo. Escrita do recibo,
arquivo e auditoria não constitui uma transação única: uma falha anterior ao
arquivo mantém o marcador; uma posterior pode devolver código 2 já com o
original arquivado. Recibo sem marcador arquivado regista uma tentativa. Rever
`doctor`, arquivo e auditoria antes de repetir; não apagar estado sem análise.

## Limites e validação

O bloqueio é cooperativo e local, testado nos sistemas de ficheiros do CI. Não
é um lease entre máquinas, garantia em sistemas de ficheiros de rede ou proteção
contra quem pode reescrever `.safeops`. Mantêm-se os digests e a exigência de
código de confiança. Os timeouts referem-se ao subprocesso direto; não estão
implementadas supervisão/terminação de toda a árvore de processos ou recuperação
automática. Versões antigas não conhecem a guarda; os seus marcadores continuam
a bloquear e exigem a mesma verificação independente antes da recuperação.

Os testes com processos reais cobrem duas execuções aprovadas concorrentes,
recuperação recusada com guarda ocupada, libertação normal e morte abrupta com
marcador retido. Cobrem também marcadores alterados/inseguros, hard links, falhas
de recibo/auditoria e preservação dos planos/aprovações. Windows testa uma
junction real no estado; POSIX testa um pipe com nome. Os workspaces são
temporários; não recuperam bloqueios reais do projeto nem contactam fornecedores.

Consultar [execução](EXECUTION.md), [saída](OUTPUT.md), [estado](STATUS.md),
[CI](CI.md) e as [referências primárias](../LOCKING.md#limits-and-validation).
