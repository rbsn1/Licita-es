# Documento de requisitos — Plataforma de Agentes para Licitações Públicas

## 1. Visão geral
Plataforma de agentes de IA que cobre o ciclo de licitações públicas brasileiras — da prospecção de editais ao acompanhamento pós-contratação — entregando cada etapa diretamente ao cliente final (empresa licitante), remunerada por percentual de êxito sobre o valor do contrato.

## 2. Objetivos e métricas de sucesso
- Entregar apenas editais relevantes ao perfil do cliente — métrica: taxa de aderência das buscas (Prospecção)
- Aumentar a taxa de vitória do cliente nos certames em que a plataforma atuou — métrica: % de certames vencidos / certames disputados com apoio da plataforma
- Reduzir o tempo do cliente gasto organizando documentação de habilitação — métrica: tempo entre publicação do edital e checklist de pendências entregue
- Reduzir perda de prazo por falta de acompanhamento — métrica: nº de prazos perdidos (recurso, entrega, vigência) com a plataforma ativa

## 3. Stakeholders e personas
| Persona | Papel | Principal necessidade |
|---|---|---|
| Cliente final (empresa licitante) | Único usuário da plataforma; recebe a saída de todos os agentes diretamente, sem analista intermediário | Ser avisado e instrumentado em cada etapa do certame sem precisar acompanhar manualmente PNCP, prazos e documentação |

Não há persona de analista/operador interno revisando saídas antes de chegarem ao cliente — decisão explícita para manter o mesmo padrão do agente de Prospecção.

## 4. Modelo de negócio
Percentual de êxito (success fee) sobre o valor do contrato, cobrado no momento da homologação/assinatura do contrato — não depende do pagamento efetivo posterior pelo órgão.

## 5. Escopo — agentes da plataforma

**Dentro do escopo:**
1. **Prospecção de editais** — detalhado em [requisitos-prospeccao.md](requisitos-prospeccao.md) (RF-01 a RF-05)
2. **Análise/triagem de edital**
3. **Precificação**
4. **Documentação/habilitação**
5. **Acompanhamento** (sessão pública + pós-contratação)

**Fora do escopo:**
- **Recursos/impugnações** (minuta de recurso administrativo) — excluído por risco de exercício irregular da advocacia (redigir peças pode exigir habilitação OAB dependendo de como o serviço é comercializado)
- Esferas, modalidades e fonte primária (PNCP) seguem o mesmo recorte definido no documento de Prospecção para todos os agentes

## 6. Requisitos funcionais

### 6.1 Análise/triagem de edital
| ID | Descrição | Prioridade |
|---|---|---|
| RF-ANL-01 | Análise de edital deve obter automaticamente o PDF do edital a partir do link produzido pelo agente de Prospecção, extraindo prazo, valor estimado, requisitos de habilitação e cláusulas de risco, produzindo um resumo estruturado do edital | Must |

### 6.2 Precificação
| ID | Descrição | Prioridade |
|---|---|---|
| RF-PRE-01 | Precificação deve calcular uma faixa de preço competitivo a partir do orçamento estimado do órgão (extraído pela Análise de edital), do histórico de contratos/atas homologados no PNCP, do Painel de Preços do governo federal e do histórico interno de propostas do cliente, produzindo uma sugestão de faixa de preço (mínimo/ideal/máximo) | Must |

### 6.3 Documentação/habilitação
| ID | Descrição | Prioridade |
|---|---|---|
| RF-DOC-01 | Documentação/habilitação deve comparar os requisitos de habilitação exigidos no edital (extraídos pela Análise de edital) com o dossiê documental do cliente, produzindo um checklist de pendências documentais por edital | Must |

Não inclui monitoramento contínuo de validade de certidões (ex: CND, regularidade fiscal) — decisão explícita nesta fase; ver item em aberto na seção 11.

### 6.4 Acompanhamento
| ID | Descrição | Prioridade |
|---|---|---|
| RF-ACO-01 | Acompanhamento deve monitorar as fases da sessão pública (lances, negociação, prazo de recurso) a partir do cronograma do certame, produzindo alertas por e-mail e WhatsApp em ciclo intradiário | Must |
| RF-ACO-02 | Acompanhamento deve monitorar prazos pós-contratação (entrega, vigência, aditivo) a partir do contrato assinado e cronograma, produzindo alertas por e-mail e WhatsApp em ciclo intradiário | Must |

## 7. Requisitos não funcionais
| ID | Atributo | Critério |
|---|---|---|
| RNF-01 | Isolamento de dados multi-tenant | Válido para todos os agentes (não só Prospecção): dados e dossiês de um cliente nunca acessíveis a outro, mesmo entre clientes do mesmo setor disputando o mesmo certame |
| RNF-02 | Latência de alerta — sessão pública e pós-contratação | Ciclo intradiário, mesmo padrão da Prospecção — não é requisito de tempo real (decisão explícita apesar da dinâmica ao vivo da fase de lances; ver risco na seção 9) |
| RNF-03 | Volume inicial | Piloto pequeno: 1 a 10 clientes simultâneos |
| RNF-04 | Retenção de dados (LGPD) | Válido para dossiê documental e histórico de preços do cliente, além do histórico de editais já previsto na Prospecção; prazo exato `[a definir]` |
| RNF-05 | Disponibilidade | `[a definir]` |

## 8. Integrações e fontes de dado
- **PNCP** — editais (Prospecção/Análise) e histórico de contratos/atas homologados (Precificação)
- **Painel de Preços** (governo federal) — histórico de preços praticados em compras públicas (Precificação)
- **Dossiê documental do cliente** — repositório de certidões/documentos cadastrados na plataforma (Documentação/habilitação)
- **Histórico interno de propostas do cliente** — propostas e custos de licitações anteriores cadastradas na plataforma (Precificação)
- **E-mail / WhatsApp Business API** — canais de alerta, reaproveitados de Prospecção para Acompanhamento

## 9. Restrições legais e de compliance
- Isolamento lógico de dados entre clientes (multi-tenant), inclusive entre concorrentes no mesmo certame — vale para todos os agentes, não só Prospecção
- Recursos/impugnações fora de escopo justamente para evitar exercício irregular da advocacia (ver seção 5)
- A plataforma deve permanecer no campo de inteligência de mercado e organização documental — nunca sugerir contato ou influência dentro do órgão público
- Dossiê documental e histórico de preços do cliente sujeitos a LGPD, com os mesmos cuidados já previstos para dados de perfil na Prospecção

## 10. Riscos
| Risco | Impacto | Mitigação |
|---|---|---|
| Alerta de sessão pública em ciclo intradiário (não tempo real) | Cliente pode perder janela de lance/negociação por não ser avisado durante a disputa ao vivo | Revisitar RNF-02 antes de operar em certames com sessão pública disputada ativamente; reavaliar se piloto (RNF-03) expuser esse gap |
| Checklist de habilitação sem monitoramento de validade de certidões | Cliente pode ser inabilitado por certidão vencida não sinalizada com antecedência | Reavaliar escopo de RF-DOC-01 após piloto, se inabilitações por certidão vencida forem recorrentes |
| Dependência de dados extraídos pela Análise de edital para alimentar Precificação e Documentação/habilitação | Erro de extração se propaga para dois agentes downstream | Validar qualidade de extração da Análise de edital antes de liberar Precificação/Documentação em produção |

## 11. Glossário
- **PNCP**: Portal Nacional de Contratações Públicas
- **Painel de Preços**: base oficial do governo federal com preços praticados em compras públicas
- **Dossiê documental**: conjunto de certidões e documentos de habilitação do cliente cadastrados na plataforma
- **Success fee**: percentual cobrado sobre o valor do contrato apenas em caso de vitória
- **RF / RNF**: requisito funcional / requisito não funcional

## 12. Itens em aberto
- Se o checklist de Documentação/habilitação deve evoluir para monitoramento contínuo de validade de certidões (RF-DOC-01)
- Percentual exato do success fee e regras de rateio quando há mais de um agente envolvido no resultado
- Prazo de retenção de dados do dossiê e histórico de preços (RNF-04)
- SLA de disponibilidade (RNF-05)
- Formato e estrutura do dossiê documental do cliente (upload livre vs. campos estruturados por tipo de certidão)
- Se/quando reavaliar Recursos/impugnações (ex: via parceria com escritório de advocacia em vez de geração direta)
