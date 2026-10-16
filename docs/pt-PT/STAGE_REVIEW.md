# Revisão do contexto original atual — 0.3.0a13

<!-- safeops-version: 0.3.0a13 -->

[English](../STAGE_REVIEW.md)

```bash
safeops --json --root PROJETO_ORIGINAL review-stage ID_DA_COPIA
```

Usa o ID exato de 12 caracteres hexadecimais minúsculos em `.safeops/stages` do
original. A revisão sem escrita exige a proposta, intenção, recibo, plano ligado
e configuração atual. Começa pela [inspeção histórica estrita](STAGING.md).
Só revê o original se a cópia corresponder ao recibo. Não exige nem cria
aprovação de execução.

| Resultado `status` | Saída | Significado |
|---|---:|---|
| `current` | 0 | Cópia correspondente e todas as ligações do contexto original revistas correspondem |
| `stale` | 1 | Cópia correspondente e evidência válida/legível, mas alguma ligação do original difere |
| `incompatible` | 1 | Inspeção histórica válida indica cópia alterada/incompleta; o original não é revisto |
| Erro tratado de política/acesso/integridade/limites/concorrência | 2 | Mensagem fixa saneada, `data: null`; todo o estado existente é preservado |

`current` e `stale` incluem `source_context: "revalidated"`, IDs da cópia/proposta,
fingerprints da proposta/recibo, versão registada, `version_matches`, digests
registado/observado do original e verificações booleanas em `checks`:

- `plan`: plano não crítico, com integridade válida, ainda corresponde ao
  fingerprint, snapshot registado e conjunto exato de caminhos da candidata.
- `source`: snapshot atual do original corresponde ao digest da proposta.
- `candidate_bases`: cada caminho original exato mantém o respetivo hash base.
- `configuration`: configuração validada de schema 1/2 corresponde ao digest.
- `selected_targets`: digest dos ficheiros selecionados no schema 2 corresponde;
  no schema 1 utiliza `null`.
- `version` e `execution_contract`: ligações correspondem à versão instalada e
  contrato fixo de execução, incluindo protocolos do runner/bloqueio.

`reasons` contém códigos fixos das verificações falsas, pela ordem acima:
`plan-changed`, `source-changed`, `candidate-bases-changed`,
`configuration-changed`, `selected-targets-changed`, `version-changed`,
`execution-contract-changed`. Uma cópia alterada/incompleta devolve
`source_context: "not-reviewed"`, `stage_status` e `stage-not-matching`, sem
declarar revalidação do original. Configuração, alvos ou plano inválidos/inseguros
originam erro, em vez de uma observação válida de desatualização. O resultado não
inclui texto/diffs dos ficheiros, tarefa/conselho, motivos de aprovação ou detalhes
brutos do SO. Hashes e IDs podem continuar a ser sensíveis.

Duas observações completas do original têm de coincidir. Cada uma valida os
ficheiros de controlo, confirma a seleção de alvos antes/depois da leitura,
calcula o hash do original e relê a evidência/identidades dos diretórios de
controlo. A inspeção histórica final tem de coincidir com a inicial. A revisão
não escreve ficheiros, auditoria, aprovação ou recibos; não invoca fornecedores,
subprocessos ou código do projeto; não persiste, limpa, reverte, opera o Git ou
aplica alterações a qualquer espaço de trabalho.

## Âmbito do snapshot e limites

O hash original mantém a ordem de `tree_digest` (ficheiros regulares ordenados
antes da recursão nos diretórios ordenados) e exclusões exatas dos diretórios
gerados. Ao contrário da cópia filtrada, **inclui ficheiros de ambiente** e
ficheiros normais chamados `.git`, `build`, etc.; os bytes são processados
localmente para o hash e nunca devolvidos. Só diretórios reais com nomes exatos
de `SKIP_DIRS` são omitidos. Ligações/reparse points, ficheiros não regulares ou
com várias ligações, nomes Unicode/de controlo ambíguos e colisões de caminhos
sem distinguir maiúsculas falham. Não lê conteúdo de diretórios excluídos;
também rejeita ligações nesses nomes. Entradas ilegíveis não desaparecem em
silêncio.

Cada leitura do original admite 5 000 ficheiros regulares, 12 000 000 bytes por
ficheiro, 64 000 000 bytes no total, 10 000 entradas encontradas e 64 níveis de
diretórios abaixo da raiz. Os nomes exigem UTF-8 NFC sem caracteres de controlo.
Diretórios vazios e metadados não entram no digest. Plano/configuração têm
limite individual de 256 000 bytes; intenção/recibo/proposta mantêm os limites
4 096/1 000 000/260 096 bytes e parsing JSON estrito.

A validação de metadados dos alvos de schema 2 mantém 5 000 entradas por check.
Todos os ficheiros regulares selecionados, incluindo gerados/de ambiente
selecionados na configuração, são lidos para hash com limites independentes de
5 000 ficheiros/12 MB por ficheiro/64 MB total e validação segura dos ascendentes.
Corresponde ao digest de alvos da aprovação existente, rejeitando entradas
inseguras/ilegíveis/demasiado grandes. Não importa nem executa código dos alvos.
Os limites do original e dos alvos são independentes.

## Significado e compatibilidade

É uma observação pontual de compatibilidade de registos locais mutáveis e sem
chave. Não autentica proveniência, prova testes aprovados, congela o sistema de
ficheiros ou elimina todas as corridas concorrentes. Não acrescenta bloqueio nem
isolamento pelo SO. O original pode mudar logo após a revisão. Um autor local
hostil pode reescrever todos os registos e fingerprints. `current` não concede
autoridade de execução/aplicação nem renova aprovações existentes.

Cópias históricas de schema 1 continuam inspecionáveis após atualização.
Rever uma cópia antiga com versão instalada mais recente indica ligações de
versão e/ou contrato desatualizadas se a restante evidência continuar válida.
Preserva o histórico; cria plano/proposta revistos e uma cópia separada novos
quando precisares de ligações atuais. Executar testes de confiança na cópia
continua a exigir inicialização, plano novo e aprovação explícita nessa cópia.
Aplicação ao original, rollback, worktrees Git, isolamento pelo SO e proveniência
SafeOps autenticada continuam planeados. A alfa pública GitHub/PyPI mantém-se
em 0.3.0a8.
