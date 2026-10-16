# Ferramentas de manutenção revistas — 0.3.0a18

<!-- safeops-version: 0.3.0a18 -->

[English](../TOOLING.md)

A política do código 0.3.0a18 abrange ambientes dedicados **CPython 3.12,
Linux x86_64 e glibc >=2.34**. Mantém o runtime sem dependências externas e a
matriz Linux/Windows/macOS com Python 3.11–3.13.

| Perfil | Ferramentas diretas | Utilização |
|---|---|---|
| `ci` | setuptools 83.0.0, coverage 7.16.2 | Testes medidos em Linux/Python 3.12 |
| `release` | build 1.6.1, setuptools 83.0.0, twine 7.0.0, detect-secrets 1.5.0 | Validação manual de candidatos/releases |

Os [inputs CI](../../requirements/ci.in) e [release](../../requirements/release.in)
separam requisitos diretos dos conjuntos transitivos completos de
[CI](../../requirements-ci.txt) e [release](../../requirements-release.txt).
O [manifesto](../../requirements/tooling-locks.json) regista nome exato da wheel,
versão, SHA-256 e URL PyPI de cada ficheiro, incluindo dependências nativas.
O limite glibc inclui a wheel cryptography selecionada, além de coverage.

## Instalação e recusa

Criar um ambiente virtual novo com o intérprete suportado e executar:

```sh
python3.12 -m venv /tmp/safeops-tools
/tmp/safeops-tools/bin/python scripts/locked_tools.py ci
# Para ferramentas de release, criar outro venv novo e escolher release.
```

`--check` verifica plataforma e ligações input/lock/manifesto sem instalar.
O instalador recusa Python global e pacotes alheios no ambiente. Desativa
configuração/variáveis externas do pip, keyring, cache e interação. Exige versões
exatas e SHA-256 em todas as dependências, apenas wheels do índice PyPI explícito;
reinstala versões já presentes, executa `pip check` e confirma inventário final
exato num intérprete novo. Dependências em falta, bytes alterados, wheels ausentes,
perfil incompatível ou conflitos causam recusa, sem tentativa irrestrita.
Uma falha pode deixar instalação parcial no venv de ferramentas: descartar esse
ambiente descartável e investigar antes de o recriar.

Para um diretório local de wheels verificadas, acrescentar
`--wheelhouse /caminho/absoluto`. Usa `--no-index`, os mesmos hashes e verificação
de dependências; ser local não torna o conteúdo automaticamente fiável. Não
instalar a partir dos `.in` nem retirar a verificação de hashes na utilização normal.

Após instalar ferramentas CI, instalar o projeto local com esse intérprete:

```sh
/tmp/safeops-tools/bin/python -m pip --isolated install --no-index --no-deps --no-build-isolation -e .
```

O projeto é código revisto do repositório, não uma wheel externa fixada por hash.
O backend já está fixado; este comando não descarrega dependências de construção
ou runtime. Construir candidatos com `python -m build --no-isolation` no ambiente
release. O setuptools 83 não precisa de pacote wheel adicional.

## Limites dos workflows

O CI prepara `ci` antes de instalar o projeto para medição. Os outros oito jobs
testam deliberadamente a construção normal isolada. Os dois jobs Linux/Python 3.11
resolvem deliberadamente ferramentas build e setuptools mínimo/mais recente.
São testes de compatibilidade, **não ambientes de release fixados**. Mantêm-se as
suites das wheels e o quality-gate obrigatório de doze jobs. Esta exceção não
significa identidade de dependências em todos os ambientes de teste.

O workflow manual prepara `release` a partir do **código do workflow antes de
selecionar um tag histórico**. Tags antigos podem não conter estes ficheiros e
não escolhem a política de instalação atual. Mantêm-se ancestralidade/CI exatos,
verificação dos ficheiros originais, publish=false por omissão, autoridade
OIDC/ambiente e validação do registo. Esta alteração não publica, move tags ou
substitui anexos públicos 0.3.0a8.

Intérprete/ensurepip inicial, imagens dos runners, bibliotecas do SO, Actions e
dependências do contentor de publicação são limites separados. O pip inicial não é atualizado pelos perfis; a versão observada é preservada e confirmada no inventário final. Hashes estabelecem
identidade dos ficheiros aprovados, sem garantir ausência de vulnerabilidades,
builds reproduzíveis, aprovações SafeOps assinadas ou isolamento de código hostil.

## Atualização controlada

Usar ambiente suportado separado e descartável. Rever versões/avisos upstream
antes de alterar versões diretas `.in`. Resolver para diretório temporário vazio,
apenas pelo índice oficial:

```sh
python -m pip --isolated download --only-binary=:all: --index-url https://pypi.org/simple \
  --dest /tmp/safeops-reviewed-wheels -r requirements/ci.in -r requirements/release.in
python scripts/refresh_tool_locks.py --wheelhouse /tmp/safeops-reviewed-wheels
```

O helper usa packaging das ferramentas release existentes. Lê metadados sem
importar código das wheels, compara hashes com ficheiros PyPI exatos não retirados,
verifica dependências ativas do perfil e prepara os dois conjuntos e o manifesto.
A resolução seleciona versões transitivas novas de propósito: é uma etapa revista
pelo maintainer, nunca fallback automático do CI. Rever cada versão, nome de
ficheiro, dependência, licença e limite de plataforma. Outras origens/perfis exigem
alteração explícita da política.

Validar instalações novas online/offline, `pip check`, cobertura, build, Twine
estrito, scans e suite da wheel instalada. As regressões offline usam pip real
para recusar hash alterado mesmo com versão já instalada e dependência transitiva
sem pin. Atualizar EN/PT-PT, estado, roadmap/changelog e versão quando necessário;
usar branch/PR e exigir CI da PR/main aprovado. Atualizar locks não publica releases
nem concede novas permissões de publicação.

Referências primárias: [pip e hashes](https://pip.pypa.io/en/stable/topics/secure-installs/),
[configuração pip](https://pip.pypa.io/en/stable/topics/configuration/),
[API JSON PyPI](https://docs.pypi.org/api/json/).
