# Cópias locais de preparação — 0.3.0a17

<!-- safeops-version: 0.3.0a17 -->

[English](../STAGING.md)

`stage-proposal` materializa uma [proposta local](PROPOSALS.md) revista numa cópia
nova e separada. O texto proposto só é escrito nessa cópia. Preserva o código,
planos, aprovações e estado Git originais; acrescenta estado local de preparação
e um evento de auditoria sem conteúdo dos ficheiros. Não executa comandos
externos nem contacta fornecedores. É uma cópia de diretório, não uma worktree
Git, clone ou sandbox do sistema operativo.

## Procedimento e confirmação

Cria um plano e proposta novos na versão instalada e revê-os:

```powershell
safeops --root PROJETO --json review-proposal ID_DA_PROPOSTA
safeops --root PROJETO --json stage-proposal ID_DA_PROPOSTA --confirm FINGERPRINT_DA_PROPOSTA
safeops --root PROJETO --json inspect-stage ID_DA_COPIA
```

Usa o `fingerprint` exato de 64 caracteres devolvido por `review-proposal`, não
o ID nem o hash do candidato. Inspeciona primeiro os diffs. Fingerprint antigo/
alterado ou proposta desatualizada provocam rejeição. A confirmação autoriza
apenas a criação da cópia; não autoriza aplicação ao original nem execução.
A proposta e as ligações ao código/configuração/alvos/contrato são verificadas
antes e depois da cópia. Alterações posteriores não atualizam cópias existentes.

O resultado indica o caminho absoluto `workspace`. Inspeciona os ficheiros e o
recibo antes de inicializares a cópia para verificações de confiança:

```powershell
safeops --root CAMINHO_DA_COPIA init
safeops --root CAMINHO_DA_COPIA plan "Validar alterações revistas na cópia"
safeops --root CAMINHO_DA_COPIA review NOVO_ID_DO_PLANO
safeops --root CAMINHO_DA_COPIA approve NOVO_ID_DO_PLANO --confirm NOVO_ID_DO_PLANO --reason "Revisei o código da cópia e os testes"
safeops --root CAMINHO_DA_COPIA run NOVO_ID_DO_PLANO
```

Substitui caminhos e IDs pelos valores reais. `--json`, quando necessário, fica
antes do comando. A aprovação original não é copiada nem reutilizada. O novo
plano liga o conteúdo modificado da cópia. `run` mantém apenas as verificações
fixas de compilação/unittest; não há execução ou aplicação automática.
Os testes executam Python arbitrário e podem ler fora da cópia ou usar ambiente/
rede herdados. Usa apenas código e testes de confiança. Verificações aprovadas
não concedem autorização para aplicar alterações ao projeto original.

## Âmbito, limites e privacidade

A cópia usa a [enumeração do snapshot](EXECUTION.md): no máximo 5 000 ficheiros
regulares e 12 000 000 bytes por ficheiro de origem. Omite diretórios gerados/
internos (`.git`, `.safeops`, `.venv`, `venv`, caches, `.tox`, `node_modules`,
`dist`, `build`) e componentes internos equivalentes que sejam ficheiros, como
um `.git` de worktree. A enumeração omite ligações e objetos não regulares;
os caminhos dos candidatos continuam a rejeitar ligações. Cada caminho copiado
passa a validação portátil e o descritor aberto tem de ser regular e corresponder
à identidade inspecionada. Caminhos não suportados ou antecessores inseguros falham.

Omite todos os componentes `.env` e `.env.*`, incluindo `.env.example`, sem
distinguir maiúsculas/minúsculas em qualquer plataforma (inclui `.ENV.sample`).
Não prepara candidatos dirigidos a esses ficheiros. Outros ficheiros podem conter
credenciais ou texto sensível: estas exclusões não garantem ausência de segredos.
Não contacta fornecedores nem faz upload. Qualquer partilha posterior exige
inspeção pelo operador. Não há limpeza do ambiente herdado nem isolamento.

O conteúdo total materializado tem limite de 64 000 000 bytes. Mantêm-se os
limites do preview para o candidato. Conteúdo vazio cria um ficheiro existente
vazio. Os ficheiros são cópias novas independentes, sem hard links. Diretórios
novos pedem modo 0700 e ficheiros 0600; as ACL efetivas dependem da plataforma.
Não preserva permissões de execução, datas, proprietário ou outros metadados.
Dependências, resultados gerados e ficheiros de ambiente podem exigir preparação
local separada. Não é um build integralmente reproduzível nem checkout de
submódulos/LFS.

## Armazenamento e recibo de schema 1

O estado fica em `.safeops/stages/ID/`, excluído do snapshot original:

- `intent.json`: IDs da cópia/proposta, data/hora, versão instalada, fingerprint
  exato da proposta, hash do candidato e digest do projeto original.
- `workspace/`: bytes independentes com as substituições revistas.
- `receipt.json`: criado apenas após verificação da cópia e revisão final da
  proposta; contém os campos da intenção, `status: "staged"`, manifesto,
  total de bytes, digest da cópia e `fingerprint` do JSON canónico sem ele próprio.

Cada entrada do manifesto tem `path`, `source_sha256`, `staged_sha256`, `bytes`
e `replaced`. O recibo tem limite de 1 000 000 bytes incluindo newline final.
Não importa registos `.safeops` originais. Intenção e recibo não contêm texto
dos ficheiros; nomes e hashes podem revelar informação. Os registos são locais,
alteráveis e não assinados.

O comando devolve schema 1, estado, IDs, fingerprint da proposta, caminho da
cópia, fingerprint do recibo, contagens de ficheiros/bytes e aviso fixo.
Aplica-se o [envelope JSON](OUTPUT.md) e os códigos tratados 0/2.

## Falhas e autoridade

Os IDs são criados exclusivamente, sem substituição deliberada de cópias
existentes. Após a criação do diretório, erros devolvem mensagem controlada com
ID do estado retido. Não há limpeza/eliminação automática. Sem recibo, a
preparação está incompleta. Inspeciona antes de repetir; repetir cria outro ID.
Recibo e auditoria são gravações separadas: a auditoria pode falhar depois de
a cópia/recibo ficarem prontos. Confirma sempre a evidência local efetiva.

As verificações detetam alterações concorrentes comuns, não todas as corridas
do sistema de ficheiros. Um escritor local malicioso pode substituir ficheiros
ou recalcular hashes sem chave. O recibo descreve um momento; edições ou testes
posteriores podem alterar a cópia. `inspect-stage` faz a comparação limitada
descrita abaixo; não há prova autenticada de autoria, isolamento de escrita ou
transação garantida.

Mantêm-se configuração 1/2, plano 1, aprovação 2, envelope 1 e protocolos runner
5/bloqueio 3. Atualizar para 0.3.0a17 exige propostas e aprovação de execução
novas ligadas à versão. Preserva o histórico sem migração. [Aplicação revista ao original e rollback conservador](APPLICATION.md) estão implementados separadamente. Worktrees Git isoladas e sandboxing continuam planeados.
Consulta o [estado](STATUS.md) e o [roadmap](../../ROADMAP.md).

## Inspeção histórica sem escrita — introduzida no código 0.3.0a12

Executar `safeops --json --root PROJETO_ORIGINAL inspect-stage ID_DA_COPIA`, no
projeto original inicializado e com o ID exato de 12 caracteres hexadecimais
minúsculos. Não grava ficheiros/eventos de auditoria, não importa código do
projeto e não contacta fornecedores nem executa verificações. Não exige
aprovação de execução.

A inspeção analisa intenção/recibo de schema 1, identidade, fingerprint canónico
do recibo, contagens/tipos/caminhos do manifesto e ligação à proposta/candidato/
digest histórico de origem. Hashes e tamanhos das substituições têm de
corresponder ao candidato guardado. A proposta retida é obrigatória; não renova
nem revalida as ligações ao código/configuração atuais. Um manifesto igual exige
digest coerente com o recibo. Duas leituras limitadas da cópia têm de coincidir;
a evidência de controlo volta a ser lida antes do resultado.

| Resultado `status` | Código | Significado |
|---|---:|---|
| `matching` | 0 | Caminhos regulares incluídos, hashes, tamanhos e digest iguais ao recibo |
| `changed` | 1 | Evidência válida; `missing`, `extra` e/ou `changed` contêm caminhos relativos ordenados |
| `incomplete` | 1 | Intenção/proposta válidas e recibo ausente; a cópia parcial é preservada e não analisada |
| Erro tratado de integridade/acesso/limite | 2 | Mensagem genérica sem detalhes sensíveis e sem dados de resultado; todo o estado preservado |

Os resultados matching/changed incluem fingerprint do recibo, contagens de
ficheiros/bytes e digests registados/observados. Todos incluem identidade da
cópia/proposta, versão registada, `version_matches`, digest histórico original
e `source_context: "historical-binding-only"`. Não incluem texto nem diffs;
caminhos e hashes podem ser sensíveis. É possível inspecionar schema 1 após
atualizar a versão ou alterar o original/configuração. `matching` descreve apenas
a cópia filtrada, sem comprovar equivalência com o original atual, autoria,
testes aprovados, aprovação de execução ou autorização para aplicar alterações.

Cada leitura permite 5 000 ficheiros, 12 000 000 bytes por ficheiro, 64 000 000
bytes no total, 10 000 entradas encontradas e 64 níveis de diretórios abaixo da
raiz da cópia. Intenção/recibo têm limites de 4 096/1 000 000 bytes; a proposta
mantém 260 096 bytes. Chaves JSON repetidas, schemas/campos não suportados,
UTF-8 inválido, números não finitos e caminhos ambíguos falham. Ligações/reparse
points incluídos, ficheiros não regulares, ficheiros/evidência com múltiplas
ligações físicas, árvores ilegíveis e caminhos com colisão de maiúsculas falham.

Componentes exatos `SKIP_DIRS` e `.env`/`.env.*` sem distinção de maiúsculas são
omitidos sem travessia, incluindo ligações nesses nomes excluídos. Assim, caches
geradas e estado `.safeops` inicializado separadamente na cópia ficam fora da
comparação. Dados excluídos, bits de execução, datas, proprietário e alterações
de diretórios vazios não são comparados. Não acrescenta bloqueio do sistema de
ficheiros nem isolamento; duas leituras não eliminam todas as corridas.
Um escritor local malicioso pode reescrever evidência e hashes sem chave.

## Revisão do contexto original atual

O código 0.3.0a13 acrescenta `review-stage ID_DA_COPIA` na raiz original. Exige cópia histórica correspondente e compara original atual, bases da candidata, plano, configuração, alvos, versão instalada e contrato de execução. Consulta [resultados, limites e compatibilidade](STAGE_REVIEW.md). Nunca aplica alterações nem renova aprovação; `inspect-stage` mantém apenas o significado histórico.

Os checks aprovados na cópia criam agora [recibos de execução](RUN_RECEIPTS.md) independentes, ligados aos inputs observados nessa cópia e à sua aprovação nova. A inspeção histórica não certifica compatibilidade atual com o original nem autoriza aplicar a candidata.
