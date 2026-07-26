# CLAUDE.md

## Prática: spec-driven development

Este projeto segue requisitos-primeiro (spec-driven). As especificações são a fonte da verdade, não o código:

- `requisitos-plataforma.md` — requisitos consolidados da plataforma (5 agentes, modelo de negócio, RNFs transversais)
- `requisitos-prospeccao.md` — requisitos detalhados do agente de Prospecção (já implementado)
- `requisitos-analise-edital.md` — requisitos detalhados do agente de Análise/triagem de edital (já implementado)
- `requisitos-precificacao.md` — requisitos detalhados do agente de Precificação (já implementado)

### Regras

1. **Spec antes de código.** Qualquer mudança de comportamento num agente começa atualizando o RF-XX/RNF-XX correspondente antes de tocar em `src/`. Para levantar ou revisar requisitos, use a skill `analise-requisitos-licitacao`.
2. **Rastreabilidade de volta ao código.** Toda função/módulo que implementa um requisito funcional referencia o ID (`RF-XX`) num comentário curto no ponto de implementação — permite `grep -rn "RF-01"` e achar exatamente onde está implementado. Ver mapa abaixo.
3. **Requisito sem código não é bug.** Um RF/RNF documentado mas ainda não implementado (ex: RF-05, fase 2) é esperado — não "corrija" a lacuna sem antes confirmar com o usuário se é hora de implementá-la.

### Mapa requisito → implementação (agente de Prospecção)

| Requisito | Onde |
|---|---|
| RF-01 (busca editais no PNCP) | `src/webapp/clients/pncp.py` (`PNCPClient`), `ProspeccaoAgent.buscar_editais_publicados` em `src/agents/prospeccao/agent.py` |
| RF-02 (score de aderência) | `ProspeccaoAgent.calcular_score` / `filtrar_compativeis` em `src/agents/prospeccao/agent.py` |
| RF-03 (alerta e-mail/WhatsApp) | `enviar_alertas_pendentes` em `src/agents/prospeccao/agent.py` + `src/webapp/clients/resend_client.py` — só e-mail implementado; canal WhatsApp segue em aberto |
| RF-04 (dashboard consultável) | `src/webapp/routes/dashboard.py` + `src/webapp/templates/dashboard.html` |
| RF-05 (portais legados) | não implementado — fase 2 |
| RNF-01 (varredura intradiária) | `executar_varredura` em `src/agents/prospeccao/agent.py`, chamada por `scripts/prospectar.py` (CLI/lock local) e por `src/webapp/routes/cron.py` (`GET /cron/prospectar`, agendado a cada 3h em `vercel.json` via Vercel Cron) |

### Mapa requisito → implementação (agente de Análise/triagem de edital)

| Requisito | Onde |
|---|---|
| RF-ANL-01 (obtém PDF do edital via PNCP e extrai resumo estruturado) | `src/agents/analise_edital/agent.py` — usa `claude-opus-4-8` via Anthropic API (`ANTHROPIC_API_KEY` obrigatória); `src/webapp/clients/pncp.py` (`buscar_arquivos_compra`, `baixar_arquivo`, `parse_numero_controle`, `selecionar_documento_edital`) para localizar e baixar o PDF |
| RF-ANL-02 (disparo automático para matches acima do limiar de alerta) | `analisar_editais_pendentes` em `src/agents/pipeline.py`, chamada por `src/webapp/routes/cron.py` (`GET /cron/analisar`, agendado em `vercel.json` via Vercel Cron, 10min após `/cron/prospectar`) |
| RF-ANL-03 (exibição do resumo no dashboard) | `src/webapp/routes/dashboard.py` (outerjoin de `ResumoEdital`) + `src/webapp/templates/dashboard.html` (coluna "Prazo proposta") |
| RNF-01 (idempotência — edital já resumido não é reanalisado) | filtro `ResumoEdital.id.is_(None)` em `analisar_editais_pendentes`, `src/agents/pipeline.py` |
| RNF-02 (falha num edital não interrompe os demais) | `try/except` por edital em `analisar_editais_pendentes`/`precificar_editais_pendentes`, `src/agents/pipeline.py` |
| Modelo de dados | `ResumoEdital`/`FaixaPreco` em `src/data/models.py` (um registro por `Edital`, não por cliente — conteúdo do edital independe de quem deu match), migração `alembic/versions/c1a0f5d9b2e4_*.py` |

### Mapa requisito → implementação (autenticação)

| Requisito | Onde |
|---|---|
| RF-AUTH-01 (login do cliente final, substitui o link mágico) | `src/webapp/routes/auth.py` (`/login`), `src/webapp/routes/dashboard.py` (`/dashboard` agora exige `request.session["cliente_id"]`) |
| RF-AUTH-02 (login do operador) | `src/webapp/routes/auth.py` (`/admin/login`) |
| RF-AUTH-03 (painel admin lista clientes, só leitura) | `src/webapp/routes/admin.py` (`/admin`) |
| RNF-06 (senha com hash) | `src/data/auth.py` (`hash_senha`/`verificar_senha`, bcrypt) |

Sessão via `SessionMiddleware` (cookie assinado por `SESSION_SECRET_KEY`, ver `.env.example`). Cadastro de cliente/operador continua via `scripts/cadastrar_cliente.py` / `scripts/cadastrar_operador.py` — não há formulário de cadastro na UI ainda.

### Mapa requisito → implementação (agente de Precificação)

| Requisito | Onde |
|---|---|
| RF-PRE-01 (faixa de preço a partir de orçamento + histórico PNCP + Painel de Preços) | `src/agents/precificacao/agent.py` (`PrecificacaoAgent.calcular_para_edital`, `calcular_faixa_preco`, `filtrar_contratos_por_objeto`); `src/webapp/clients/pncp.py` (`buscar_contratos`/`buscar_todos_contratos`, endpoint `/v1/contratos`); `src/webapp/clients/painel_precos.py` (`PainelPrecosClient`) |
| RF-PRE-04 (sinaliza faixa não confiável com pouca amostra) | `calcular_faixa_preco` em `src/agents/precificacao/agent.py` |
| RF-PRE-02 (disparo automático após Análise/triagem, mesmo limiar do RF-03) | `precificar_editais_pendentes`/`processar_editais_pendentes` em `src/agents/pipeline.py`, chamada pela mesma rota `GET /cron/analisar` |
| RF-PRE-03 (exibição no dashboard) | `src/webapp/routes/dashboard.py` (outerjoin de `FaixaPreco`) + `src/webapp/templates/dashboard.html` (coluna "Faixa de preço sugerida") |

Sinal do Painel de Preços exige `codigoItemCatalogo` (CATMAT/CATSER), que a Análise/triagem ainda não extrai do edital — na prática só o histórico do PNCP alimenta a faixa hoje (ver `requisitos-precificacao.md`).

Os demais 2 agentes da plataforma (Documentação/habilitação, Acompanhamento) têm requisitos fechados em `requisitos-plataforma.md` mas ainda nenhum código — ao implementá-los, seguir a mesma prática de rastreabilidade acima.
