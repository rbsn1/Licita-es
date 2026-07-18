# CLAUDE.md

## Prática: spec-driven development

Este projeto segue requisitos-primeiro (spec-driven). As especificações são a fonte da verdade, não o código:

- `requisitos-plataforma.md` — requisitos consolidados da plataforma (5 agentes, modelo de negócio, RNFs transversais)
- `requisitos-prospeccao.md` — requisitos detalhados do agente de Prospecção (único já implementado)

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

Os demais 3 agentes da plataforma (Precificação, Documentação/habilitação, Acompanhamento) têm requisitos fechados em `requisitos-plataforma.md` mas ainda nenhum código — ao implementá-los, seguir a mesma prática de rastreabilidade acima.
