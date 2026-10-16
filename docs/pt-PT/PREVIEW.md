# Preview local de candidatos — 0.3.0a18

<!-- safeops-version: 0.3.0a18 -->

[English](../PREVIEW.md)

`safeops --root PROJETO --json preview CANDIDATO.json` valida substituições
fornecidas num ficheiro local e devolve diffs unificados. O caminho do candidato
é relativo ao diretório da shell, independentemente de `--root`; também pode
ser absoluto. Não é necessário inicializar `.safeops`. O comando não escreve
ficheiros, aprovações, auditoria ou estado Git, nem chama fornecedores, testes
ou comandos externos. A saída predefinida também é JSON; `--json` acrescenta o
[envelope comum de schema 1](OUTPUT.md).

## Schema 1 do candidato

O objeto contém exatamente `schema` (inteiro 1, nunca booleano) e `files`
(uma a vinte entradas). Cada entrada contém exatamente:

| Campo | Contrato |
|---|---|
| `path` | Caminho relativo canónico e portátil para um ficheiro regular existente |
| `base_sha256` | 64 dígitos hexadecimais minúsculos: SHA-256 dos bytes originais exatos |
| `content` | Texto completo de substituição, sem comandos ou fragmentos de patch |

Exemplo para um ficheiro de confiança: executar numa pasta com `PROJETO/` e
`PROJETO/hello.txt` existente. Rever o novo texto antes do preview. Este script
de exemplo escreve apenas o candidato explicitamente escolhido, fora do projeto.

```python
import hashlib
import json
from pathlib import Path

original = Path("PROJETO/hello.txt").read_bytes()
candidate = {"schema": 1, "files": [{
    "path": "hello.txt",
    "base_sha256": hashlib.sha256(original).hexdigest(),
    "content": "Olá do EuroMind SafeOps!\n",
}]}
Path("candidato.json").write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
```

```bash
safeops --root PROJETO --json preview candidato.json
```

JSON estrito rejeita chaves repetidas, números não finitos, UTF-8 inválido,
documentos que não sejam objetos, campos adicionais e schemas não suportados.
O candidato e cada original/substituição têm limite de 256 000 bytes. A soma dos
bytes originais e novos não pode exceder 1 000 000. Cada texto aceita até
5000 linhas, UTF-8 sem BOM, apenas LF e mudança de linha final quando não vazio.
São permitidos tabs; os restantes controlos C0/C1/DEL são rejeitados. Conteúdo
vazio representa um ficheiro vazio, não a sua eliminação.

Caminhos têm de estar normalizados em NFC, sem componentes vazios ou ponto,
repetições ou colisões sem distinção de maiúsculas/minúsculas. A
[política de âmbito](SCOPE.md) rejeita ainda caminhos absolutos, travessia, nomes
reservados, componentes internos/gerados, ligações e reparse points. Ficheiros
futuros, diretórios e objetos não regulares não são alvos válidos. Componentes
finais e descritores abertos têm de ser regulares; os antecessores dos alvos são
validados. Leituras limitadas usam no-follow/nonblocking quando disponível.
O hash da base tem de corresponder e substituições sem alteração são rejeitadas.
Antes de devolver resultados, os caminhos e os bytes originais são verificados
novamente; alterações concorrentes detetadas fazem falhar todo o preview.

## Saída e autoridade

Em caso de sucesso, `data` contém `schema: 1`, `status: "preview-only"`,
`candidate_sha256`, `files` e um aviso fixo. Cada ficheiro inclui `path`,
`before_sha256`, `after_sha256` e `diff` unificado com três linhas de contexto e
rótulos `a/` e `b/`. Os diffs são strings JSON; descodificar para mostrar as
mudanças de linha. O hash do candidato usa JSON canónico: chaves ordenadas,
separadores compactos e UTF-8. Espaçamento e ordem das chaves não alteram a
identidade; a ordem dos ficheiros conta. Os hashes dos ficheiros usam os bytes
exatos. São registos de integridade, sem autenticação do autor ou assinatura.
Sucesso devolve 0; erros tratados de política, ficheiros ou argumentos devolvem 2.

A saída inclui texto local e proposto, potencialmente sensível. Não é expurgada,
enviada nem acrescentada automaticamente a auditoria/relatórios CI. Rever
localmente antes de partilhar. O scanner separado é heurístico e não garante
segurança. Um diff válido não prova correção, testes aprovados, aprovação de
execução ou autorização para aplicar alterações.

Trata-se de uma verificação local pontual, sem snapshot atómico ou isolamento
pelo SO. Não impede alterações posteriores, hard links ou corridas hostis no
sistema de ficheiros. Importação de patches genéricos, criação/eliminação,
renomeação, binários/CRLF/ausência de newline final, geração automática por IA e
sandboxing continuam planeados. [Aplicação revista/rollback](APPLICATION.md) estão implementados separadamente. As [aprovações de execução](EXECUTION.md) são independentes;
a atualização de versão continua a exigir plano novo revisto e aprovação explícita.

As [propostas locais ligadas ao plano](PROPOSALS.md) já estão disponíveis num fluxo separado. O comando `preview` continua sem estado e não inicializa nem escreve `.safeops`.
