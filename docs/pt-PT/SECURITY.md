# Política de segurança

[English](../../SECURITY.md)

## Âmbito e maturidade

O EuroMind SafeOps v0.2.0 é uma **ferramenta de desenvolvimento em versão alfa**.
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
- Os snapshots excluem diretórios gerados e ligações simbólicas; rever essas limitações antes de confiar nas aprovações.

O grafo de dependências, os alertas e as atualizações de segurança do Dependabot
foram também ativados após autorização. As atualizações são propostas através
de PR e continuam sujeitas ao `quality-gate` e às regras da `main`.
