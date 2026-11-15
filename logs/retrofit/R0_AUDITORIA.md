# R0 — Auditoria de UI/UX do painel nicho-bahia

Data: 2026-11-15 · Branch: `retrofit-uiux` · Evidência bruta: `logs/retrofit/audit.json`
Screenshots: `logs/retrofit/r0/{mobile,tablet,desktop}_{topo,decisao}.png`

Método: Playwright (Chromium) em `docs/index.html` via `file://`, nos viewports
360×800, 768×1024 e 1440×900. Medições por DOM/`getComputedStyle`, axe-core 4.10.2
(tags wcag2a/2aa/21a/21aa), `performance.getEntries` e cronometragem de handlers.
Script: `tmp/audit_retrofit.py` (reprodutível).

---

## 1. Estado real vs SPEC

| Item do SPEC §9 | Declarado | Medido | Situação |
|---|---|---|---|
| Abas | 8 | 8 | ✅ |
| Gráficos ECharts | "22 gráficos" | **18** instâncias | ⚠️ divergência (ver §4) |
| Arquivo único | ≤ 15 MB | 2,69 MB | ✅ |
| JSON ≤ 8 MB | ≤ 8 MB | 1,65 MB | ✅ |
| Zero requests externos | sim | 0 | ✅ |
| Toggle nominal/real | sim | funciona | ✅ |
| Filtros ano/sec/região/família | sim | 4/4 funcionais | ✅ |
| "filtra ou declara" | sim | 6 gráficos com aviso âmbar | ✅ |
| Secretaria × região exclusivas | sim | sim | ✅ |
| Título-pergunta por gráfico | sim | sim | ✅ |
| Id do agregado no rodapé | sim | 18/18 | ✅ |

**Conclusão do item 1:** a camada *analítica* está íntegra. As dívidas são de
**apresentação e decisão**, não de dados.

## 2. Dívidas confirmadas (com evidência)

| # | Dívida | Evidência medida | Impacto no sócio |
|---|---|---|---|
| D1 | **Layout quebra em 360px** | `overflow_x=true`; **1.632 elementos** fora da tela (desktop: 0) | painel ilegível no celular |
| D2 | **Tipografia abaixo de 12px** | **389 elementos** < 12px (`sub` 11,5px; `label` 11px; eixos 10px) | esforço de leitura |
| D3 | **Alvos de toque pequenos** | **29** controles < 44px; `select` com 28px de altura | erro de toque no celular |
| D4 | **Troca de aba acima do budget** | 332ms (mobile) · **418ms (tablet)** · 207ms (desktop) vs ≤ 200ms | sensação de travamento |
| D5 | **Tabela sem busca/paginação** | 155 `<tr>` no DOM, `tem_busca=false`, `tem_paginacao=false` | achar um nicho é rolar |
| D6 | **Sem estado na URL** | `url_tem_estado=false` | não dá para mandar o recorte por link |
| D7 | **Sem chips de recorte** | `tem_chips_filtro=false` | filtro ativo só na barra do topo |
| D8 | **Sem camada executiva nem dossiê** | `tem_resumo_executivo=false`, `tem_dossie=false`, `card_tem_cta=false` | 5 min não bastam |
| D9 | **Faixa de incerteza ausente nos cards** | `card_tem_faixa_rank=false` (existe só no gráfico A13) | score parece exato |
| D10 | **Código da família compete com o score** | card mostra `89.55 · CAFE…` ao lado de `75.0`; razão tipográfica score/nome = **1,93** | "89.55" lê-se como nota |
| D11 | **Violação axe serious** | `scrollable-region-focusable` ×1 (tabela rolável sem foco) | teclado não alcança a tabela |
| D12 | **Sem CSS de impressão** | `tem_print_css=false` | não há brief em papel/PDF |
| D13 | **Tokens inconsistentes** | 7 `border-radius` e 8 `padding-top` distintos | ruído visual |
| D14 | **Estados vazio/carregando/erro ausentes** | `tem_estado_vazio=false` | tela vazia sem explicação |

## 3. Baseline de performance (para comparar no R4)

| Métrica | mobile | tablet | desktop | Budget |
|---|---|---|---|---|
| FCP | 588ms | 468ms | 516ms | ≤ 2000ms / ≤ 4000ms |
| DOMContentLoaded | 1.613ms | 797ms | 808ms | — |
| Troca de aba | 332ms | **418ms** | 207ms | ≤ 200ms |
| Filtro | 150ms | 95ms | 144ms | ≤ 200ms |
| Heap JS | 14 MB | 14 MB | 14 MB | — |
| Gráficos inicializados na carga | 1/18 | 1/18 | 1/18 | lazy por aba (bom) |

## 4. Divergências entre o prompt de retrofit e o repositório

Protocolo §8: **o repositório vence**; delta registrado.

| # | Prompt diz | Repositório tem | Decisão |
|---|---|---|---|
| Δ1 | "8 abas, 22 gráficos" | 8 abas, **18** gráficos ECharts | adotar **18** como número de gráficos; as 22 linhas do SPEC §9 incluem 4 componentes HTML (cards, tabela, EVITAR, método) |
| Δ2 | S4: "CAIXA ALTA → sentence case (rótulos)" | **0** rótulos de UI em caixa alta; o caixa-alta vem dos **nomes de catálogo** (dado de origem) | escopo corrigido: aplicar sentence case **na exibição** dos nomes, mantendo o original no `title`/tooltip |
| Δ3 | Gates R1, R2, R4 humanos | gates G1–G5 (G1/G2 humanos; G3/G4/QA automáticos) | R1/R2/R4 passam a ser os gates do retrofit; G3/G4/QA seguem como regressão obrigatória |
| Δ4 | Branch `retrofit-uiux` | repositório em `main` | branch criada; merge só após R4 |
| Δ5 | "22 gráficos" como restrição de layout | — | sem restrição; os gráficos existentes são preservados |

## 5. Mapa template → seções (gerador `src/nicho_bahia/panel_html.py`, 1.233 linhas)

| Bloco | Linhas | Conteúdo |
|---|---|---|
| `CSS` | 12–99 | tokens em `:root`, layout de `header`/`nav`/`.card`/`.grid`, tabela, `.marca` (aviso âmbar) |
| `BODY` | 100–329 | header + filtros + `#escopo` + 8 `<section class="panel">` |
| `BODY` — aba 0 Decisão | 138–174 | 4 cards: top-5, sensibilidade (A13), tabela (A09), EVITAR (A12) |
| `BODY` — aba 1 Mercado | 175–196 | série (A01), treemap (A02), CAGR (A03) |
| `BODY` — aba 2 Sazonalidade | 197–212 | heatmap (A05), calendário (A05) |
| `BODY` — aba 3 Compradores | 213–234 | órgãos (A06), canal (A07), ticket×teto (A08) |
| `BODY` — aba 4 Concorrência | 235–256 | HHI×CAGR (A11), entrantes (A14), incumbentes (A15) |
| `BODY` — aba 5 Preços | 257–278 | bandas (A16), CV (A17), desconto (A18) |
| `BODY` — aba 6 Logística | 279–300 | regiões (A19), prazos (A20), municípios (A21) |
| `BODY` — aba 7 Método | 301–329 | filtros (A22), premissas, limitações, dicionário |
| `JS` | 330–1.220 | cubos de recorte, `render*` por gráfico, `marca()` (filtra ou declara), `renderTab()` |
| `render()` | 1.221+ | injeta DATA/ECharts/JS e escreve o HTML único |

Pontos de extensão naturais: `BODY` (nova aba/dossiê), `CSS` (tokens, responsivo, print),
`JS` (busca/virtualização, URL, chips).

## 6. O que o painel faz bem (não regredir)

1. Rastreabilidade: todo gráfico carrega o id do agregado.
2. "Filtra ou declara": nenhum número de escopo trocado sem aviso.
3. Honestidade de incerteza já existe no dado (A13) — só não está na cara.
4. Performance de primeira carga boa (FCP 468–588ms) com lazy init por aba.
5. Zero dependências externas e arquivo único (publicável no Pages).
