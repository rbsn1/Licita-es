# Documento de requisitos — Agente de Análise/triagem de edital

## 1. Visão geral
Agente que obtém automaticamente o PDF do edital publicado (via PNCP) para os editais que a Prospecção já considerou relevantes ao cliente, e extrai um resumo estruturado (prazo, valor estimado, requisitos de habilitação, cláusulas de risco). Esse resumo alimenta o dashboard do cliente e serve de entrada para a Precificação (RF-PRE-01).

## 2. Objetivos e métricas de sucesso
- Poupar o cliente de ler o edital inteiro para saber prazo, valor e exigências — métrica: tempo entre edital publicado e resumo disponível no dashboard

## 3. Stakeholders e personas
| Persona | Papel | Principal necessidade |
|---|---|---|
| Cliente final (empresa licitante) | Único usuário; recebe o resumo diretamente no dashboard, sem analista intermediário | Entender rapidamente do que se trata o edital e quais são os riscos, sem ler o PDF inteiro |

## 4. Escopo
**Dentro do escopo:**
- Extração via Claude (`claude-opus-4-8`) de: prazo limite de proposta, valor estimado, requisitos de habilitação, cláusulas de risco
- Obtenção automática do PDF do edital via PNCP (`buscar_arquivos_compra`/`baixar_arquivo`)
- Persistência do resumo por edital (não por cliente — o conteúdo do edital independe de quem está de olho nele; um mesmo edital compatível com dois clientes gera um único resumo, reaproveitado para os dois)
- Disparo automático, encadeado ao ciclo de varredura da Prospecção, só para editais com pelo menos um match de score acima do limiar de alerta (mesmo limiar do RF-03, hoje 40) — decisão explícita para não gastar chamadas de Opus em editais pouco aderentes a nenhum cliente

**Fora do escopo (nesta versão):**
- Extração de código CATMAT/CATSER do objeto do edital — não faz parte do `ESQUEMA_RESUMO_EDITAL` hoje; enquanto não existir, o sinal do Painel de Preços na Precificação (RF-PRE-01) fica inativo (ver `requisitos-precificacao.md`)
- Reprocessamento de edital já analisado (ex: se o PDF for retificado) — nesta versão a análise roda uma única vez por edital

## 5. Requisitos funcionais
| ID | Descrição | Prioridade |
|---|---|---|
| RF-ANL-01 | Análise de edital deve obter automaticamente o PDF do edital a partir do link produzido pelo agente de Prospecção, extraindo prazo, valor estimado, requisitos de habilitação e cláusulas de risco, produzindo um resumo estruturado do edital | Must |
| RF-ANL-02 | Análise de edital deve disparar automaticamente para editais com match de score acima do limiar de alerta (RF-03), produzindo o resumo persistido sem exigir acionamento manual | Must |
| RF-ANL-03 | Análise de edital deve expor o resumo estruturado a partir da sessão autenticada do cliente, produzindo a exibição do resumo no card do edital no dashboard | Must |

## 6. Requisitos não funcionais
| ID | Atributo | Critério |
|---|---|---|
| RNF-01 | Idempotência | Um edital já analisado (resumo já persistido) nunca é reanalisado automaticamente — evita gasto duplicado de API |
| RNF-02 | Resiliência por edital | Falha ao analisar um edital (PDF ilegível, erro de rede, erro do modelo) não pode interromper o processamento dos demais editais pendentes no mesmo ciclo |
| RNF-03 | Isolamento de dados multi-tenant | O resumo em si é do edital (não do cliente) e pode ser reaproveitado entre clientes que deram match no mesmo edital — não há dado de um cliente exposto a outro por causa disso |

## 7. Integrações e fontes de dado
- **PNCP** — download do PDF do edital via `PNCPClient.buscar_arquivos_compra`/`baixar_arquivo`
- **Anthropic API** — `claude-opus-4-8`, extração estruturada via JSON schema
- **Prospecção (RF-01/RF-02)** — fonte da lista de matches que decide quais editais entram na fila de análise

## 8. Restrições legais e de compliance
- Mesmas restrições gerais da plataforma (ver `requisitos-plataforma.md`) — nenhuma nova introduzida por este agente

## 9. Riscos
| Risco | Impacto | Mitigação |
|---|---|---|
| PDF escaneado (imagem, sem texto extraível por `pypdf`) | Resumo vazio ou incompleto | Não tratado nesta versão — falha do edital específico, não derruba o ciclo (RNF-02) |
| Custo de Opus por edital analisado | Gasto proporcional ao volume de matches relevantes | RF-ANL-02 já limita aos editais acima do limiar de alerta; revisar limiar/modelo se o volume do piloto (RNF-03 da plataforma) tornar o custo relevante |

## 10. Glossário
- Ver glossário consolidado em `requisitos-plataforma.md`

## 11. Itens em aberto
- Extração de código CATMAT/CATSER — necessária para ativar o Painel de Preços na Precificação
- Política de reprocessamento quando um edital é retificado pelo órgão
- Se/quando expor as cláusulas de risco de forma mais destacada no dashboard (ex: alerta separado), hoje é só texto no card
