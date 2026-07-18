---
name: analise-requisitos-licitacao
description: 'Conduz o levantamento e a análise de requisitos para o projeto de agentes de IA voltados a licitações públicas (prospecção de editais, análise de edital, precificação, documentação/habilitação, acompanhamento pós-contratação). Use esta skill sempre que o usuário pedir para levantar requisitos, definir escopo, montar um documento de requisitos (PRD/BRD), criar backlog inicial, mapear personas/stakeholders, priorizar funcionalidades, ou detalhar requisitos funcionais e não funcionais deste projeto — mesmo que ele não use literalmente a palavra "requisitos" (exemplos: "o que precisamos definir antes de começar a construir", "vamos estruturar o escopo do MVP", "documenta o que cada agente precisa fazer").'
---

# Análise de requisitos — plataforma de agentes para licitações

Esta skill guia a condução de um levantamento de requisitos estruturado para o projeto de agentes de IA que prospectam, analisam, precificam e acompanham licitações públicas brasileiras, geralmente sob um modelo de remuneração por percentual de êxito.

Antes de qualquer coisa, leia `references/dominio-licitacao.md` — ele contém o conhecimento de domínio (ciclo da licitação, pontos de automação por agente, e restrições de compliance) que deve orientar as perguntas e os requisitos levantados. Não repita esse conteúdo de memória; consulte o arquivo.

## Fluxo de trabalho

### 1. Confirme o recorte do levantamento
Não presuma que o usuário quer o documento completo de uma vez. Pergunte (ou infira do contexto da conversa) qual recorte está em jogo:
- Requisitos de **um agente específico** (ex: só o agente de prospecção)
- Requisitos do **MVP** (fluxo mínimo ponta a ponta)
- Requisitos da **plataforma completa** (todos os agentes + modelo de negócio)

Se o usuário já dá pistas suficientes na conversa (ex: já decidiu focar em prospecção), não pergunte de novo — assuma esse recorte e siga.

### 2. Elicite por categoria
Percorra estas categorias, uma pergunta por vez quando possível, usando `ask_user_input_v0` para perguntas de múltipla escolha sempre que fizer sentido (evita o usuário ter que digitar em mobile):

1. **Stakeholders e personas** — quem usa o sistema? (ex: analista de licitações da empresa cliente, dono da consultoria, o próprio cliente final que contrata o serviço)
2. **Escopo (dentro/fora)** — quais órgãos/esferas (federal, estadual, municipal)? Quais modalidades (pregão, concorrência, etc.)? Alguma exclusão explícita (ex: não cobrir leilão)?
3. **Requisitos funcionais por agente** — para cada agente em escopo, o que ele precisa fazer, com que entrada e que saída (ver `references/dominio-licitacao.md` para a lista de agentes candidatos)
4. **Integrações e fontes de dado** — PNCP, portais estaduais/municipais, ERP do cliente, WhatsApp/e-mail para alertas
5. **Requisitos não funcionais** — volume esperado (quantos editais/dia), latência aceitável para alertas, disponibilidade, retenção de dados
6. **Restrições legais e de compliance** — LGPD, isolamento de dados entre clientes concorrentes no mesmo certame, limites entre consultoria e atuação jurídica (ver seção de compliance no arquivo de domínio)
7. **Métricas de sucesso** — taxa de aderência das buscas, taxa de vitória, tempo economizado, etc.
8. **Modelo de dados e formato de saída** — o que precisa ser persistido, e em que formato o requisito final deve ser entregue (ver passo 4)

Não avance para a próxima categoria sem fechar minimamente a anterior, mas também não trave o levantamento inteiro esperando respostas perfeitas — registre suposições explícitas quando o usuário for vago e siga.

### 3. Estruture os requisitos
Escreva cada requisito funcional como `RF-XX: [agente] deve [ação] a partir de [entrada], produzindo [saída]`.
Escreva cada requisito não funcional como `RNF-XX: [atributo] deve atender [critério mensurável]`.
Isso facilita rastreabilidade depois, quando o usuário for para desenho técnico ou backlog.

### 4. Gere o documento de requisitos
Use `assets/template-requisitos.md` como esqueleto. Preencha as seções com o que foi levantado. Pergunte ao usuário (se ainda não estiver claro) se o entregável final deve ser:
- Um arquivo Markdown simples (rápido, editável)
- Um documento Word formal (`.docx`) — nesse caso, consulte a skill `docx` antes de gerar o arquivo

Nunca invente requisitos que o usuário não validou — se uma seção ficou sem informação suficiente, deixe marcado como `[a definir]` em vez de preencher com suposições não confirmadas.

### 5. Feche com próximos passos
Ao final, aponte explicitamente o que ainda está em aberto (`[a definir]`) e sugira a ordem lógica de continuidade (ex: "com os RF-01 a RF-05 fechados, o próximo passo natural é desenhar a arquitetura técnica do agente de prospecção").
