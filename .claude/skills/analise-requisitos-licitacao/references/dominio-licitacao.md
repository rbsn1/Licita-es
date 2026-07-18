# Domínio: licitações públicas brasileiras

Referência de contexto para orientar o levantamento de requisitos. Baseado na Lei 14.133/2021 (Nova Lei de Licitações).

## Ciclo fim a fim da licitação

1. **Fase interna** — órgão faz Estudo Técnico Preliminar (ETP), Termo de Referência/Projeto Básico, pesquisa de preços, matriz de risco, define modalidade e critério de julgamento, elabora e aprova o edital.
2. **Publicação** — edital publicado no PNCP (Portal Nacional de Contratações Públicas, hoje o hub obrigatório), Diário Oficial e sistemas próprios (Comprasnet/gov.br, BEC-SP, BLL, Licitações-e). Abre prazo para impugnações e esclarecimentos.
3. **Propostas** — empresas leem o edital, verificam requisitos de habilitação (jurídica, fiscal, técnica, econômico-financeira) e enviam proposta pelo sistema eletrônico.
4. **Sessão pública / disputa** — abertura de propostas, fase de lances (decrescentes, no pregão), negociação com o primeiro colocado.
5. **Julgamento e habilitação** — verificação de proposta mais vantajosa e conformidade documental; diligências quando necessário.
6. **Recursos** — prazo para recurso administrativo, contrarrazões, julgamento.
7. **Homologação e adjudicação** — autoridade competente homologa; objeto adjudicado ao vencedor.
8. **Contratação** — assinatura de contrato/Ata de Registro de Preços, emissão de empenho.
9. **Execução e fiscalização** — entrega, fiscal de contrato acompanha, pagamentos.
10. **Encerramento** — recebimento definitivo, eventuais aditivos/sanções.

## Agentes candidatos e onde cada um atua no ciclo

| Agente | Atua na etapa | Entrada típica | Saída típica |
|---|---|---|---|
| Prospecção/monitoramento | Publicação | Perfil do cliente (CNAE, região, faixa de valor) + feed do PNCP/portais | Lista de editais compatíveis, com score de aderência |
| Análise/triagem de edital | Publicação → Propostas | PDF do edital/TR | Prazo, valor estimado, requisitos de habilitação, cláusulas de risco extraídos |
| Precificação | Propostas | Orçamento estimado do órgão + histórico de preços | Sugestão de faixa de preço competitivo |
| Documentação/habilitação | Propostas → Julgamento | Requisitos de habilitação do edital + dossiê do cliente | Checklist de pendências documentais |
| Acompanhamento da sessão | Sessão pública | Prazos e fases do certame | Alertas de fase de lances/prazo de recurso |
| Recursos/impugnações | Recursos | Motivo do questionamento | Minuta inicial (revisão jurídica humana obrigatória) |
| Pós-contratação | Execução | Contrato assinado, cronograma | Alertas de prazo de entrega/vigência/aditivo |

## Fontes de dados

- **PNCP** — API pública de dados abertos, cobre a maior parte dos órgãos federais/estaduais/municipais desde 2023. Fonte primária recomendada.
- Portais legados que ainda não centralizaram tudo no PNCP: Comprasnet, BEC-SP, BLL, alguns TCEs estaduais — complementares, não substitutos.

## Restrições de compliance a sempre considerar no levantamento

- **Consultoria vs. advocacia**: redigir peças de recurso/impugnação de forma profissional pode exigir habilitação de advogado (OAB), dependendo de como o serviço é comercializado.
- **Anticartel/conluio**: se o mesmo sistema assessora dois concorrentes no mesmo certame, há risco de conluio — exige isolamento de dados por cliente (ex: "muralhas chinesas" lógicas).
- **Tráfico de influência**: o serviço deve ficar estritamente no campo de inteligência de mercado e organização documental — nunca sugerir contato ou influência dentro do órgão público.
- **LGPD**: dados de empresas clientes (documentos fiscais, técnicos, financeiros) exigem tratamento e retenção cuidadosos.

Estas restrições devem virar requisitos não funcionais explícitos (ex: RNF de isolamento de dados por cliente) sempre que o levantamento tocar em multi-tenant ou remuneração por êxito.
