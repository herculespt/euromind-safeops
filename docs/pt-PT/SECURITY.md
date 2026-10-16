# Política de segurança

<!-- safeops-version: 0.3.0a19 -->

[English](../../SECURITY.md)

## Âmbito e maturidade

O EuroMind SafeOps 0.3.0a19 é uma **ferramenta de desenvolvimento em versão alfa**.
Não implementa isolamento seguro, não garante a segurança do código testado e
não deve ser utilizado para autorizar operações de produção. A classificação
de risco e a pesquisa por padrões são heurísticas com limitações.

## Comunicar vulnerabilidades

**Não abrir Issues públicas com explorações, credenciais ou detalhes de
vulnerabilidades ainda sem correção.** Utiliza **Security → Advisories → Report
a vulnerability** para comunicar em privado. A comunicação privada foi ativada
e verificada em 15 de outubro de 2026, após autorização do maintainer.

Se esse canal deixar de estar disponível, abre uma Issue pública apenas a
pedir a disponibilização de um canal privado, sem revelar os detalhes da
vulnerabilidade. Não existe prazo de resposta garantido nem programa de
recompensas.

## Limitações e cuidados

- Executar verificações apenas sobre código de confiança: a descoberta de testes Python executa código.
- Os ficheiros locais de aprovação e auditoria não têm assinaturas nem proteção contra adulteração.
- Não existe isolamento geral por sistema operativo, contentor ou segmentação de rede.
- Um fornecedor remoto recebe a descrição da tarefa quando a utilização é autorizada expressamente; nunca incluir segredos.
- Manter `.safeops/`, variáveis de ambiente, tokens e ficheiros `.env` fora do controlo de versões.
- Uma pesquisa sem resultados não prova a ausência de segredos no código.
- Os planos guardam localmente a tarefa e o aconselhamento; evitar informação sensível.
- Os snapshots excluem diretórios gerados e ligações simbólicas. Os caminhos declarados rejeitam componentes com ligações/reparse points antes do fornecedor, aprovação e execução; isto não controla todos os descendentes nem isola testes de confiança. Consulta a [política de âmbito](SCOPE.md).
- Suites vazias ou totalmente ignoradas falham; isto não demonstra a qualidade das asserções nem impede que testes de confiança terminem ou manipulem o interpretador.
- As respostas dos fornecedores usam JSON UTF-8 estrito e leitura limitada. Os erros HTTP/URL/timeout apresentam apenas o tipo na CLI, sem imprimir o corpo da resposta nem os detalhes da exceção por esse caminho. Os testes com respostas fixas não validam a segurança de modelos reais nem a compatibilidade da conta; consulta a [validação dos fornecedores](PROVIDER_TESTING.md).
- O schema 1 da configuração mantém-se. O schema 2 das aprovações liga a versão e o contrato fixo de execução; as aprovações antigas exigem novo plano e aprovação, sem migração silenciosa. Consulta a [política de execução](EXECUTION.md).

O grafo de dependências, os alertas e as atualizações de segurança do Dependabot
foram também ativados após autorização. As atualizações são propostas através
de PR e continuam sujeitas ao `quality-gate` e às regras da `main`.

A [saída do preview](PREVIEW.md) contém texto dos ficheiros locais; não a publiques sem revisão. Hashes de candidatos verificam integridade, sem assinatura ou aprovação.

Os [registos de propostas locais](PROPOSALS.md) contêm todo o texto proposto. Mantém-nos privados e fora do Git. Hashes locais recalculáveis não autenticam um escritor malicioso; uma revisão com sucesso não concede autoridade para aplicar nem executar.

As [cópias locais](STAGING.md) omitem ficheiros convencionais de ambiente e estado Git/SafeOps, mas outros ficheiros podem conter segredos. Não limpam o ambiente/rede herdados nem isolam os testes. As cópias parciais ficam retidas; não as publiques nem elimines automaticamente.

`inspect-stage` só lê e devolve identificadores históricos, caminhos relativos,
contagens e digests, sem texto dos ficheiros. Esses dados podem ser sensíveis.
Evidência sem chave igual não autentica autoria, não revalida o original atual,
não demonstra testes aprovados nem concede aprovação de execução/aplicação.

`review-stage` revalida separadamente o contexto original atual com observações limitadas sem escrita, exigindo cópia correspondente. Pode ler bytes de ambiente/alvos selecionados para hash local, sem os devolver. `current` não concede aprovação, autenticação ou autoridade de aplicação. Consulta [âmbito e limites de concorrência](STAGE_REVIEW.md).

Intenções/recibos de execução só guardam metadados limitados, hashes e resultados fixos, sem output/tarefa/conselho/motivos de aprovação. `inspect-run` é apenas histórico e nunca autentica proveniência nem renova aprovação. Observações posteriores param sequências com inputs alterados/indisponíveis; a auditoria rejeita hardlinks/reparse/ficheiros não regulares sem bloquear em FIFOs. Testes de confiança mantêm acesso ao sistema de ficheiros/processos e registos sem chave são mutáveis. Consulta [os limites](RUN_RECEIPTS.md).

O código 0.3.0a15 acrescenta [aplicação revista e rollback conservador](APPLICATION.md). Ambos os checks fixos da cópia têm de passar com ligações atuais inalteradas e configuração igual à do original; confirmação humana exata e guards nativos precedem backups/journal privados e escrita. Marcador pendente bloqueia checks aprovados/aplicações novos. Inspeção sem escrita e rollback confirmado separadamente preservam evidência e recusam edições humanas observadas. Sem transação de vários ficheiros, garantia de energia/armazenamento, operações Git, pedidos a fornecedores ou isolamento pelo SO. Nesse marco, runner 4/lock 2; aprovação de execução nova ligada à versão obrigatória. Backups e propostas contêm texto local: manter `.safeops` privado e fora de artefactos públicos. Hashes/identidades locais não impedem proprietário malicioso nem todas as corridas entre verificar/substituir.

O código 0.3.0a16 acrescenta [supervisão dos processos próprios](SUPERVISION.md): launcher bloqueado à entrada, grupo/âncora PID POSIX ou job Windows com kill-on-close, confirmação nativa e caudas de output drenadas continuamente com limite. Timeout inclui descendentes normais próprios e pipes retidos; limpeza incerta mantém run.lock e intent incompleto sem recibo final. Runner 5/lock 3 exigem aprovação nova ligada à versão. Abrange descendentes cooperantes no grupo POSIX/membros do job, sem conter escapes deliberados de grupo/sessão, isolar código hostil ou decidir recuperação automática. O guia define conclusão, timeout, cancelamento e morte abrupta do principal.

O código 0.3.0a19 aguarda contagem final zero do job Windows no mesmo orçamento de limpeza de três segundos usado para saída do launcher, EOF e limpeza de falha. Contagem positiva transitória não transforma imediatamente um check falhado concluído em erro operacional; confirmação persistente/indisponível mantém recusa e estado retido. Diagnóstico por fases fixas exclui texto nativo de exceções. Mantêm-se runner 5/lock 3 e schemas; versão/política de limpeza atualizadas exigem planos/propostas/aprovações novos e revistos.

Ferramentas de cobertura/release usam conjuntos transitivos de wheels/hashes revistos em perfis Linux/CPython 3.12 dedicados. A [política](TOOLING.md) define instalação/recusa, atualização e exceções dos jobs de compatibilidade. Não fixa o bootstrap do runner/intérprete nem certifica segurança das dependências.

A [geração IA revista](GENERATION.md) envia ficheiros selecionados apenas após consentimento/fingerprint próprios. A revisão mostra texto completo; padrões não detetam toda a informação privada. Candidatos continuam não aprovados e podem conter Python inseguro que os checks só executam após revisão/aprovação explícitas. A origem é metadado mutável, não atestação.
