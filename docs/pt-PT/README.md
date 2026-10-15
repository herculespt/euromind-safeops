# EuroMind SafeOps — Português (Portugal)

**Ferramenta open source de orquestração de engenharia com aprovação humana e execução controlada de verificações.**

## O que já funciona na versão 0.2.0 (alfa)

- CLI Python 3.11+ sem dependências externas obrigatórias em tempo de execução.
- Planeamento local de tarefas com classificação de risco e especialidade sugerida.
- Registo de aprovação humana ligado ao conteúdo do plano e do código-fonte.
- Execução de duas verificações predefinidas: compilação Python e testes `unittest`.
- Registo de auditoria local e pesquisa limitada de padrões típicos de credenciais.
- Aconselhamento opcional através de OpenAI Responses API, Anthropic Messages API (Claude) ou modelos locais compatíveis com Chat Completions.
- Comando `safeops providers`, que informa se existem chaves configuradas sem mostrar o seu valor.

**Não implementa** agentes autónomos que editem código, isolamento seguro, execução arbitrária, pipelines de produção, proteção garantida contra ataques. O código dos testes executa com os privilégios do utilizador: não utilizes repositórios não confiáveis.

## Instalar e testar

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
safeops --root examples/demo_project init
safeops --root examples/demo_project plan "Melhorar a documentação do exemplo"
```

Copia o ID apresentado em `plan` e executa, substituindo `ID_DO_PLANO`:

```powershell
safeops --root examples/demo_project review ID_DO_PLANO
safeops --root examples/demo_project approve ID_DO_PLANO --confirm ID_DO_PLANO --reason "Revisei o código e os testes"
safeops --root examples/demo_project run ID_DO_PLANO
```

O plano **não modifica código**. A execução necessita de aprovação explícita e é bloqueada quando o projeto muda desde o planeamento.

Para utilizar OpenAI ou Claude, configura `OPENAI_API_KEY` ou `ANTHROPIC_API_KEY` no ambiente e fornece o modelo pretendido e `--allow-remote`. Vê [as instruções completas dos fornecedores](../PROVIDERS.md). Uma subscrição de chat não inclui necessariamente créditos de API.

Consulta a [documentação principal](../../README.md), [arquitetura](../ARCHITECTURE.md), [modelo de confiança](../TRUST_MODEL.md) e [regras de segurança](../../SECURITY.md).

Licença: Apache 2.0. Projeto independente, sem código privado do SEND.
