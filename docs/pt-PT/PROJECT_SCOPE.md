# Âmbito e origem do projeto

<!-- safeops-version: 0.3.0a20 -->

[English](../PROJECT_SCOPE.md)

O EuroMind SafeOps 0.3.0a20 é um projeto open source original e autónomo: uma
ferramenta genérica de linha de comandos para políticas e verificações em fluxos
de desenvolvimento. O [estado de implementação](STATUS.md) distingue as
capacidades existentes, o trabalho futuro e as publicações efetivas.

## Componentes públicos

- Algoritmos genéricos de planeamento e auditoria.
- Políticas conservadoras, sugestões de especialidade e verificações predefinidas.
- Aconselhamento opcional através de APIs compatíveis com OpenAI, com consentimento expresso.
- Adaptadores nativos OpenAI e Anthropic, configuração estrita e aprovações ligadas à versão.
- Documentação, exemplos públicos e testes.

## Exclusões

- Chaves criptográficas, configurações privadas de infraestrutura e segredos de publicação.
- Código proprietário, dados de clientes ou credenciais de fornecedores.
- Alegações não verificáveis de certificação, garantias de segurança, downloads,
  base instalada, adoção pela comunidade ou elegibilidade para programas OSS.

## Revisão dos direitos antes da publicação

O responsável pelo projeto deve confirmar os direitos de cada contribuição e
verificar eventuais obrigações contratuais perante empregadores ou terceiros.
Código, exemplos, artefactos gerados e licenciamento devem ser revistos antes
da publicação. O caráter público do repositório não autoriza a divulgação de
software proprietário nem de informação confidencial.

As [propostas locais persistentes](PROPOSALS.md) ligam substituições escritas manualmente a um plano explícito inalterado e permitem revisão sem escrita. Aplicação explícita tem [contrato separado](APPLICATION.md); a geração IA limitada está implementada com consentimento exato e [contrato separado](GENERATION.md); edição autónoma continua planeada.

As [cópias locais separadas](STAGING.md) permitem inspecionar/testar substituições revistas com confirmação exata do fingerprint. Não aplicam ao original, não inicializam/aprovam testes automaticamente nem implementam isolamento pelo SO. [Preparação Git opcional](GIT_STAGING.md) tem revisão/consentimento próprios e partilha metadados Git.

O código 0.3.0a15 acrescenta [aplicação revista e rollback conservador](APPLICATION.md). Ambos os checks fixos da cópia têm de passar com ligações atuais inalteradas e configuração igual à do original; confirmação humana exata e guards nativos precedem backups/journal privados e escrita. Marcador pendente bloqueia checks aprovados/aplicações novos. Inspeção sem escrita e rollback confirmado separadamente preservam evidência e recusam edições humanas observadas. Sem transação de vários ficheiros, garantia de energia/armazenamento, operações Git, pedidos a fornecedores ou isolamento pelo SO. Nesse marco, runner 4/lock 2; aprovação de execução nova ligada à versão obrigatória.

O código 0.3.0a16 acrescenta [supervisão dos processos próprios](SUPERVISION.md): launcher bloqueado à entrada, grupo/âncora PID POSIX ou job Windows com kill-on-close, confirmação nativa e caudas de output drenadas continuamente com limite. Timeout inclui descendentes normais próprios e pipes retidos; limpeza incerta mantém run.lock e intent incompleto sem recibo final. Runner 5/lock 3 exigem aprovação nova ligada à versão. Abrange descendentes cooperantes no grupo POSIX/membros do job, sem conter escapes deliberados de grupo/sessão, isolar código hostil ou decidir recuperação automática. O guia define conclusão, timeout, cancelamento e morte abrupta do principal.

A [geração IA revista](GENERATION.md) é uma operação separada de partilha de código: revisão offline do pedido completo, fingerprint e consentimento de upload, depois proposta schema 2 não aprovada. Schema 1 manual e gates explícitos de revisão/staging/checks/aplicação mantêm-se. A revisão contém código e não deve ser publicada sem inspeção; `plan` continua a enviar só a tarefa.
