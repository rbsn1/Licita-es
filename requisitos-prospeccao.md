# Documento de requisitos — Agente de Prospecção de Editais

## 1. Visão geral
Agente que monitora publicações de editais em licitações públicas brasileiras (PNCP e, futuramente, portais legados) e entrega ao cliente final apenas os editais compatíveis com o seu perfil, com pontuação de aderência, alertas automáticos e um painel consultável.

## 2. Objetivos e métricas de sucesso
- Entregar ao cliente apenas editais relevantes ao seu perfil — métrica: taxa de aderência das buscas (% dos editais entregues que o cliente confirma como relevantes)

## 3. Stakeholders e personas
| Persona | Papel | Principal necessidade |
|---|---|---|
| Cliente final (empresa licitante) | Recebe os editais prospectados diretamente, sem analista intermediário | Ser avisado rapidamente de editais aderentes ao seu perfil, sem precisar garimpar o PNCP manualmente |

## 4. Escopo
**Dentro do escopo:**
- Esferas: federal, estadual e municipal
- Todas as modalidades previstas na Lei 14.133/2021 (pregão, concorrência, dispensa/inexigibilidade, etc.) — sem filtro por modalidade nesta fase
- Fonte primária: API pública do PNCP
- Matching por CNAE/ramo de atividade, região geográfica, faixa de valor estimado e palavras-chave específicas de produto/serviço cadastradas pelo cliente
- Saída: lista com link para o edital, score de aderência (0–100), alertas automáticos (e-mail e WhatsApp) e dashboard consultável
- Multi-tenant: múltiplos clientes, potencialmente de setores distintos, com isolamento lógico de dados entre contas

**Fora do escopo:**
- Análise/triagem de conteúdo do edital (PDF do edital/TR), precificação, checklist de habilitação, acompanhamento de sessão pública e pós-contratação — são agentes separados no roadmap da plataforma, não fazem parte deste documento
- Varredura de portais estaduais/municipais legados (Comprasnet, BEC-SP, BLL, TCEs) nesta primeira versão — ver item em aberto na seção 11

## 5. Requisitos funcionais
| ID | Descrição | Prioridade |
|---|---|---|
| RF-01 | Prospecção deve buscar editais publicados no PNCP a partir do perfil do cliente (CNAE, região, faixa de valor, palavras-chave), produzindo uma lista de editais candidatos | Must |
| RF-02 | Prospecção deve calcular um score de aderência (0–100) para cada edital candidato a partir do perfil do cliente e dos atributos do edital (objeto, valor, órgão, local), produzindo uma lista ordenada por score | Must |
| RF-03 | Prospecção deve notificar o cliente por e-mail e WhatsApp a partir de um edital com score acima de um limiar configurável, produzindo um alerta com link direto para o edital no PNCP | Must |
| RF-04 | Prospecção deve expor um dashboard consultável a partir do histórico de editais encontrados por cliente, produzindo uma visão filtrável por score, órgão, esfera, modalidade e data | Must |
| RF-05 | Prospecção deve varrer portais estaduais/municipais legados a partir da lista de portais priorizados (`[a definir]`), complementando a cobertura do PNCP | Should (fase 2) |

## 6. Requisitos não funcionais
| ID | Atributo | Critério |
|---|---|---|
| RNF-01 | Frequência de varredura | Intradiária — várias vezes ao dia; intervalo exato `[a definir]` |
| RNF-02 | Isolamento de dados multi-tenant | Dados e configurações de busca de um cliente nunca devem ser acessíveis ou vazar, mesmo indiretamente, para outro cliente — vale mesmo entre clientes de setores distintos |
| RNF-03 | Retenção de dados (LGPD) | Dados de perfil do cliente e histórico de editais devem ter prazo de retenção definido e mecanismo de exclusão; prazo exato `[a definir]` |
| RNF-04 | Disponibilidade | `[a definir]` |
| RNF-05 | Latência do alerta | Alerta deve ser disparado dentro do mesmo ciclo de varredura intradiária em que o edital foi capturado (não é requisito de tempo real) |

## 7. Integrações e fontes de dado
- **PNCP** — API pública de dados abertos; fonte primária nesta versão
- **Portais estaduais/municipais legados** (Comprasnet, BEC-SP, BLL, TCEs) — complementares, previstos para fase 2 (RF-05)
- **E-mail** — canal de alerta; provedor transacional `[a definir]`
- **WhatsApp Business API** — canal de alerta; provedor/integração `[a definir]`

## 8. Restrições legais e de compliance
- Isolamento lógico de dados entre clientes (multi-tenant), mesmo quando de setores distintos, para reduzir risco de conluio caso dois clientes futuramente disputem o mesmo certame
- O agente deve permanecer estritamente no campo de inteligência de mercado — nunca sugerir contato ou influência dentro do órgão público (risco de tráfico de influência)
- Tratamento de dados do perfil do cliente (CNAE, região, histórico de buscas) conforme LGPD

## 9. Riscos
| Risco | Impacto | Mitigação |
|---|---|---|
| Cobertura incompleta por depender só do PNCP nesta fase | Cliente perde editais publicados apenas em portais legados | RF-05 planejado para fase 2 |
| Falso positivo no score de aderência | Cliente perde confiança no agente e passa a ignorar alertas | Usar a taxa de aderência (seção 2) como ciclo de feedback para recalibrar o score |
| Falha no isolamento multi-tenant | Exposição de estratégia de um cliente a outro; risco reputacional e de conluio | RNF-02 como requisito arquitetural desde o início, não como retrofit |

## 10. Glossário
- **PNCP**: Portal Nacional de Contratações Públicas — hub oficial de publicação de editais
- **CNAE**: Classificação Nacional de Atividades Econômicas
- **Score de aderência**: pontuação 0–100 que indica o quão compatível um edital é com o perfil do cliente
- **RF / RNF**: requisito funcional / requisito não funcional

## 11. Itens em aberto
- Intervalo exato da varredura intradiária (RNF-01)
- Threshold de score que dispara alerta automático (RF-03)
- Provedor de e-mail e de WhatsApp Business a integrar
- Lista e prioridade dos portais legados a cobrir na fase 2 (RF-05)
- Prazo de retenção de dados (RNF-03)
- SLA de disponibilidade (RNF-04)
