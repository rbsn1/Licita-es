# Documento de requisitos — Agente de Precificação

## 1. Visão geral
Agente que sugere uma faixa de preço competitivo (mínimo/ideal/máximo) para o cliente formular sua proposta em um certame, a partir do orçamento estimado do órgão (extraído pela Análise/triagem de edital), do histórico de contratos homologados no PNCP e dos preços praticados no Painel de Preços do governo federal. Roda automaticamente logo após a Análise/triagem de edital (RF-ANL-01) processar um edital do cliente.

## 2. Objetivos e métricas de sucesso
- Ajudar o cliente a formular uma proposta competitiva sem ficar nem "no prejuízo" nem fora da disputa por preço alto — métrica: % de propostas do cliente dentro da faixa sugerida que venceram o certame
- Reduzir o tempo que o cliente gasta pesquisando preço de referência manualmente — métrica: tempo entre edital analisado e faixa de preço disponível no dashboard

## 3. Stakeholders e personas
| Persona | Papel | Principal necessidade |
|---|---|---|
| Cliente final (empresa licitante) | Único usuário da plataforma; recebe a faixa de preço diretamente no dashboard, sem analista intermediário | Saber rapidamente em que faixa de preço formular a proposta, sem precisar garimpar histórico de preços manualmente |

Mesmo padrão de persona única do restante da plataforma (ver `requisitos-plataforma.md`) — não há analista revisando a faixa antes de chegar ao cliente.

## 4. Escopo
**Dentro do escopo:**
- Cálculo de faixa de preço (mínimo/ideal/máximo) a partir de três fontes: orçamento estimado do órgão (via RF-ANL-01), histórico de contratos/atas homologados no PNCP e preços praticados no Painel de Preços do governo federal
- Execução automática, encadeada logo após a Análise/triagem de edital (RF-ANL-01) concluir o processamento de um edital do cliente
- Resultado exposto no dashboard do cliente, junto ao card/resumo do edital já analisado
- Multi-tenant: isolamento lógico entre clientes, mesmo padrão dos demais agentes da plataforma

**Fora do escopo (nesta versão):**
- Histórico interno de propostas do próprio cliente como fonte de dado — fica para fase 2 (mesmo padrão do RF-05 da Prospecção), pois exige modelo de dados e fluxo de cadastro/upload ainda não definidos
- Alerta por e-mail/WhatsApp dedicado à faixa de preço — o resultado aparece só no dashboard nesta versão; não dispara um novo alerta separado do fluxo de RF-03
- Execução sob demanda pelo cliente — nesta versão o cálculo só roda automaticamente após a Análise/triagem; não há botão de "recalcular" no dashboard

**Gatilho automático (RF-PRE-02):** roda só para editais com match de score acima do limiar de alerta (mesmo limiar do RF-03, hoje 40) — mesmo critério do RF-ANL-02 da Análise/triagem, decisão explícita para não gastar Opus/consultas de histórico em editais pouco aderentes a nenhum cliente. Precificação sempre roda depois da Análise/triagem terminar para aquele edital (a faixa usa o `valor_estimado` extraído do PDF quando disponível, caindo para o valor estimado do PNCP se a extração não achou nada).

## 5. Requisitos funcionais
| ID | Descrição | Prioridade |
|---|---|---|
| RF-PRE-01 | Precificação deve calcular uma faixa de preço competitivo a partir do orçamento estimado do órgão (extraído pela Análise de edital), do histórico de contratos/atas homologados no PNCP e do Painel de Preços do governo federal, produzindo uma sugestão de faixa de preço (mínimo/ideal/máximo) | Must |
| RF-PRE-02 | Precificação deve disparar automaticamente a partir da conclusão da Análise/triagem de edital (RF-ANL-01) para um edital do cliente, produzindo a faixa de preço sem exigir acionamento manual | Must |
| RF-PRE-03 | Precificação deve expor a faixa de preço sugerida a partir da sessão autenticada do cliente, produzindo a exibição da faixa (mínimo/ideal/máximo) no card do edital no dashboard | Must |
| RF-PRE-04 | Precificação deve sinalizar de forma explícita quando não há dados históricos suficientes (PNCP e/ou Painel de Preços) para o objeto do edital, produzindo um aviso de "faixa não confiável" em vez de omitir ou apresentar uma faixa como se fosse confiável | Must |

## 6. Requisitos não funcionais
| ID | Atributo | Critério |
|---|---|---|
| RNF-01 | Isolamento de dados multi-tenant | Cálculo e faixa de preço de um cliente nunca acessíveis a outro, mesmo entre concorrentes no mesmo certame — mesmo critério do RNF-01/RNF-02 da Prospecção |
| RNF-02 | Latência de disparo | Faixa de preço deve ficar disponível no dashboard dentro do mesmo ciclo em que a Análise/triagem concluiu o edital (não é requisito de tempo real) |
| RNF-03 | Dependência de qualidade de extração | Faixa de preço depende do orçamento estimado extraído pela Análise/triagem (RF-ANL-01) — erro de extração se propaga; ver risco na seção 9 |
| RNF-04 | Retenção de dados (LGPD) | Histórico de faixas calculadas por cliente segue o mesmo prazo de retenção `[a definir]` já registrado como item em aberto na plataforma |
| RNF-05 | Disponibilidade | `[a definir]` — mesmo item em aberto da plataforma |

## 7. Integrações e fontes de dado
- **PNCP** — `GET /v1/contratos` (mesmo `PNCPClient` de Prospecção/Análise, método `buscar_contratos`/`buscar_todos_contratos`), filtrado por `cnpjOrgao` (o órgão do próprio edital) e janela de datas. A API não aceita busca textual por objeto — a semelhança com o objeto do edital em análise é calculada no cliente, por sobreposição de palavras significativas (`filtrar_contratos_por_objeto`), não pela API.
- **Painel de Preços / Compras.gov.br (SIASG)** — API pública de dados abertos, REST, documentada via Swagger em `dadosabertos.compras.gov.br` (ver [Swagger UI](https://dadosabertos.compras.gov.br/swagger-ui/index.html)). Endpoints `1_consultarMaterial`/`3_consultarServico` exigem `codigoItemCatalogo` (código CATMAT/CATSER) como parâmetro obrigatório — não há busca por texto livre. Como a Análise/triagem (RF-ANL-01) não extrai esse código hoje, esta fonte fica inativa na prática até isso existir (ver item em aberto).
- **Análise/triagem de edital (RF-ANL-01)** — fonte do orçamento estimado do órgão; Precificação é acionada em sequência a esse agente, não roda de forma independente

## 8. Restrições legais e de compliance
- Isolamento lógico de dados entre clientes (multi-tenant), mesmo padrão já aplicado aos demais agentes
- A faixa sugerida é referência de mercado, não orientação jurídica nem contato com o órgão — mantém a plataforma no campo de inteligência de mercado (mesma restrição geral da plataforma)
- Nenhum dado pessoal novo introduzido por este agente (fontes são bases públicas de preços); dado sensível do cliente que já circula (perfil, e-mail) segue as mesmas regras de LGPD já registradas

## 9. Riscos
| Risco | Impacto | Mitigação |
|---|---|---|
| Erro de extração do orçamento estimado pela Análise/triagem se propaga para a faixa de preço | Cliente recebe faixa de preço calculada sobre uma base incorreta | RNF-03; validar qualidade de extração da Análise/triagem antes de liberar Precificação em produção (risco já registrado em `requisitos-plataforma.md`) |
| Objeto do edital muito específico/pouco recorrente, sem histórico suficiente no PNCP nem no Painel de Preços | Faixa de preço pouco confiável, cliente pode se basear nela e errar a proposta | RF-PRE-04 — sinalizar explicitamente "faixa não confiável" em vez de apresentar um número sem lastro |
| Indisponibilidade ou mudança da API do Painel de Preços (fora do controle da plataforma) | Cálculo da faixa fica só com dados do PNCP, reduzindo a base de comparação | Tratar a chamada ao Painel de Preços como best-effort — se falhar, seguir com PNCP isoladamente e sinalizar fonte parcial (mesmo espírito do RF-PRE-04) |

## 10. Glossário
- **PNCP**: Portal Nacional de Contratações Públicas
- **Painel de Preços**: painel público do governo federal com preços praticados em compras homologadas no Compras.gov.br/SIASG
- **SIASG**: Sistema Integrado de Administração de Serviços Gerais — base de compras federais por trás do Painel de Preços/Compras.gov.br
- **Faixa de preço**: sugestão de valores mínimo, ideal e máximo para a proposta do cliente
- **RF / RNF**: requisito funcional / requisito não funcional

## 11. Itens em aberto
- **Sinal do Painel de Preços inativo na prática**: exige `codigoItemCatalogo` (CATMAT/CATSER), que a Análise/triagem não extrai do edital hoje. Até essa extração existir (mudança em RF-ANL-01) ou surgir outra fonte para o código, a faixa de preço se apoia só no histórico de contratos do PNCP.
- Algoritmo de cálculo da faixa implementado: mínimo/máximo da amostra de contratos semelhantes do mesmo órgão, ideal = mediana, teto sempre limitado ao orçamento estimado do edital quando conhecido (`calcular_faixa_preco`). Sujeito a revisão após validação com dados reais.
- Quantidade mínima de registros para considerar a faixa "confiável" (RF-PRE-04): implementado como 3 (`amostra_minima`), valor de partida sem validação empírica ainda
- Histórico interno de propostas do cliente como fonte adicional — fase 2, formato de captura ainda não definido (upload livre vs. campos estruturados, mesmo tipo de decisão em aberto no dossiê documental de `requisitos-plataforma.md`)
- Se/quando adicionar um botão de recálculo sob demanda no dashboard, além do disparo automático pós Análise/triagem
