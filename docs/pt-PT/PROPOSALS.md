# Propostas locais ligadas ao plano — 0.3.0a17

<!-- safeops-version: 0.3.0a17 -->

[English](../PROPOSALS.md)

`propose` guarda localmente um [candidato de schema 1](PREVIEW.md), escrito
manualmente e ligado a um plano existente e ao seu contexto inalterado.
`review-proposal` volta a validar o registo e apresenta os diffs exatos sem
escrita. Nenhum destes comandos aplica alterações ao código, concede aprovação,
executa verificações, contacta fornecedores ou altera o Git. Uma revisão com
sucesso verifica a integridade naquele momento; não autoriza a aplicação.

## Procedimento

Inicializa o projeto de confiança uma única vez. Usa o exemplo de geração do
[guia de preview](PREVIEW.md) com `PROJECT/hello.txt` existente. Guarda
`candidate.json` fora de `PROJECT`: acrescentá-lo dentro depois do plano altera
o snapshot. Os caminhos dos ficheiros candidatos são relativos ao projeto;
o nome do JSON é relativo à diretoria atual da shell, ou absoluto.

```powershell
safeops --root PROJECT init
safeops --root PROJECT plan "Melhorar a documentação da saudação" --path hello.txt
safeops --root PROJECT review ID_DO_PLANO
safeops --root PROJECT --json propose ID_DO_PLANO candidate.json
safeops --root PROJECT --json review-proposal ID_DA_PROPOSTA
```

Substitui os IDs pelos valores reais de 12 caracteres hexadecimais minúsculos.
Cada ficheiro proposto tem de corresponder **exatamente** a um `--path` explícito
do plano. Nomear um diretório não permite implicitamente os seus descendentes.
É permitido um subconjunto dos ficheiros declarados; âmbito vazio e planos de
risco crítico são rejeitados. Estas restrições não criam isolamento do sistema
de ficheiros nem limitam os alvos das verificações fixas.

A criação guarda uma cópia do candidato. Alterar/apagar o JSON externo depois
não altera a proposta. Para modificar o conteúdo proposto, cria outra proposta.
Se o código mudou, cria um plano novo e recalcula os hashes de base. Preserva
planos, propostas e aprovações anteriores; não existe renovação automática.

## Registo de schema 1 e ligações

O registo fica em `.safeops/proposals/ID_DA_PROPOSTA.json`, excluído dos snapshots
normais. As chaves de topo são exatamente `schema` (inteiro 1), `id`, `created_at`
(data/hora UTC), `safeops_version`, `bindings`, `candidate`, `candidate_sha256`
e `fingerprint`. O candidato conserva o schema estrito do preview e o conteúdo.
O JSON canónico do candidato tem no máximo 256 000 bytes; a leitura do registo
completo fica limitada a 260 096 bytes. Mantêm-se todos os limites do preview
para ficheiros, texto, caminhos, hashes de base e total de conteúdo.

`bindings` contém exatamente:

| Campo | Valor ligado |
|---|---|
| `plan_id` | ID do plano existente |
| `plan_fingerprint` | Fingerprint do plano cuja integridade foi validada |
| `workspace_digest` | Snapshot atual, igual ao do plano |
| `config_digest` | Hash da configuração validada |
| `targets_digest` | Digest dos ficheiros selecionados no schema 2; `null` no schema 1 |
| `execution_contract` | Versão instalada e contrato fixo de execução/bloqueio/verificações |

O fingerprint usa JSON canónico sem o próprio campo `fingerprint`;
`candidate_sha256` usa o JSON canónico do candidato. Formatação e ordem das
chaves não alteram os hashes; a ordem dos ficheiros conta. A revisão verifica
novamente versão, ligações e hashes. Qualquer alteração ao snapshot normal,
mesmo num ficheiro sem relação com a proposta, invalida-a. O schema 2 liga também
os ficheiros gerados selecionados. Alterar configuração ou versão invalida-a.

O contexto é validado antes e depois do candidato; o preview volta a verificar
caminhos e bytes originais. São rejeitados diretórios de armazenamento inseguros,
ligações/reparse points e registos não regulares. Os diretórios novos pedem modo
0700 e os ficheiros modo 0600; as permissões efetivas dependem da plataforma,
sobretudo em Windows. Não existe isolamento, snapshot atómico ou proteção contra
trocas concorrentes maliciosas dos diretórios.

## Saída, auditoria e falhas

Ambos suportam o [envelope JSON](OUTPUT.md) opcional e devolvem 0 em caso de
sucesso ou 2 nos erros tratados. A criação devolve `schema`,
`status: "proposal-recorded"`, `proposal_id`, `plan_id`, hashes do candidato/registo
e um aviso fixo; não apresenta o conteúdo. A revisão devolve
`status: "proposal-reviewed"`, os mesmos identificadores/hashes, os diffs exatos
em `files` e o aviso. A revisão não escreve, incluindo no log de auditoria.

A criação acrescenta `action: "propose"`, ID do plano e `status: "recorded"` à
auditoria local, sem texto original/proposto. A gravação do registo e o acréscimo
à auditoria são separados: uma falha nesta última pode devolver erro com a
proposta já guardada. Inspeciona o estado antes de repetir. IDs existentes não
são substituídos deliberadamente; não há transação garantida entre escritores.

Os registos contêm todo o texto proposto; os diffs incluem também texto original.
Trata ambos como sensíveis, mantém `.safeops` fora do Git e revê localmente antes
de partilhar. Não existe redação automática, upload ou garantia de ausência de
segredos. Quem pode reescrever os registos pode recalcular os hashes sem chave:
não são assinaturas, prova autenticada de autoria ou auditoria inviolável.

## Compatibilidade e trabalho seguinte

Mantêm-se configuração 1/2, plano 1, aprovação 2, envelope 1 e protocolos runner 5/
bloqueio 3. O schema separado da proposta não concede aprovação de execução.
Atualizar para 0.3.0a17 exige plano novo revisto e aprovação expressa segundo o
contrato ligado à versão. `approve` e `run` não recebem propostas; continuam
limitados às verificações fixas existentes.

Geração com IA, criação/eliminação/mudança de nome de
ficheiros, edições CRLF/binárias, worktrees isoladas e proveniência assinada
continuam planeados. A versão do código não publica uma release; consulta o
[estado atual](STATUS.md).

Uma proposta revista pode agora ser materializada com [stage-proposal](STAGING.md): exige o fingerprint exato e escreve substituições apenas numa cópia local separada. [Aplicação explícita ao original e rollback conservador](APPLICATION.md) estão implementados separadamente; worktrees Git continuam planeadas.
