# PLAN_RETROFIT.md — Plano de execução do retrofit de UI/UX

Versão 0.9 (rascunho para o gate R2) · 2026-11-15 · Deriva de `SPEC_RETROFIT.md` v1.0 (aprovado em R1)
Invariantes I1–I7 e testes A1–A12 do projeto vigente **permanecem válidos e são regressão obrigatória**.

---

## 1. Estratégia

Retrofit **incremental com paridade provada**: antes de tocar em qualquer pixel, congelo um
*golden snapshot* dos números do painel (séries dos 18 gráficos + CSV). A cada fatia, comparo o
snapshot. Se um número mudar, a fatia é reprovada — mesmo que o visual esteja melhor.

Ordem de ataque (fatias verticais, cada uma entregando valor visível):

| Fatia | Entrega visível | Dívidas que fecha |
|---|---|---|
| V1 | *nenhuma* (infra de verificação) | garante I1 |
| V2 | tipografia e foco legíveis | D2, D11 |
| V3 | header/filtros usáveis no celular, chips, link compartilhável | D1, D3, D6, D7, D13 |
| V4 | **camada de decisão** (veredito + 3 cards com tese, riscos e faixa) | D8, D9, D10 |
| V5 | tabela com busca e paginação, export completo | D5, D11 |
| V6 | **dossiê do nicho** (jornada "agir") | D8 |
| V7 | responsivo completo (tabela vira cartões) | D1 |
| V8 | performance (parse tardio + memoização) | D4 |
| V9 | impressão executiva + estados vazios | D12, D14 |
| V10 | regressão final e relatório | — |

Cada fatia é **revertível**: commit próprio (`retrofit(US-xx): ...`), build reproduzível.

## 2. Arquitetura de apresentação

### 2.1 Organização do gerador

Hoje: um único `src/nicho_bahia/panel_html.py` (1.233 linhas) com `CSS`, `BODY`, `JS` e `render()`.
Proposta: quebrar em 4 módulos, **mantendo `panel_html.render()` como fachada** (o `build.py`
continua importando o mesmo símbolo — zero mudança no pipeline).

```
src/nicho_bahia/panel/
  __init__.py     render() — junta CSS + BODY + dados + ECharts + JS
  tokens_css.py   design tokens + folha de estilo (base, layout, componentes, responsivo, print)
  body.py         esqueleto HTML: header, chips, 9 <section>, Dossiê, estados
  js_core.py      estado, cubos de recorte, filtros, URL, chips, tabela, helpers
  js_charts.py    18 render* + renderVeredito/renderCards + renderDossie
```

`panel_html.py` passa a ser um shim de 3 linhas (`from .panel import render`), para não quebrar
imports e permitir rollback imediato.

### 2.2 Design tokens (CSS custom properties)

```css
:root{
  /* cor — todos os pares texto/fundo ≥ 4.5:1 */
  --c-bg:#f6f7f9; --c-surface:#ffffff; --c-ink:#16202b; --c-ink-2:#4e5b68;
  --c-ink-3:#6b7885; --c-line:#d8dee5; --c-accent:#0a6c74; --c-accent-ink:#08545a;
  --c-ok:#0f766e; --c-warn:#9a4a06; --c-bad:#a31414; --c-focus:#0a6c74;
  /* tipografia */
  --f-base:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
  --t-xs:12px; --t-sm:13px; --t-md:14px; --t-lg:17px; --t-xl:22px; --t-2xl:30px; --t-hero:34px;
  --lh-tight:1.25; --lh:1.5;
  /* espaço — escala 4, no máximo 6 degraus */
  --s-1:4px; --s-2:8px; --s-3:12px; --s-4:16px; --s-5:24px; --s-6:32px;
  /* raio — 3 degraus */
  --r-1:6px; --r-2:10px; --r-3:14px;
  /* sombra — 2 degraus */
  --sh-1:0 1px 2px rgba(16,24,40,.06); --sh-2:0 2px 8px rgba(16,24,40,.10);
  /* alvo de toque e largura */
  --touch:44px; --w-max:1560px;
  /* cor de série categórica, segura para daltonismo (não depende de vermelho/verde) */
  --c-serie-1:#0a6c74; --c-serie-2:#c2410c; --c-serie-3:#7c3aed; --c-serie-4:#0369a1;
  --c-serie-5:#a16207; --c-serie-6:#0f766e; --c-serie-7:#9f1239; --c-serie-8:#4d7c0f;
}
@media (prefers-reduced-motion: reduce){ *{transition:none!important; animation:none!important} }
```

Regras: nenhuma cor/tamanho/raio/espaço literal no CSS fora de `:root` (AR-22).

### 2.3 Layout e breakpoints

| Faixa | Largura | Comportamento |
|---|---|---|
| mobile | < 600px | 1 coluna; **filtros em `<details>`**; nav com `scroll-snap`; tabela → cartões; gráficos 220px |
| tablet | 600–1023px | 1–2 colunas; filtros em linha com quebra; tabela com 5 colunas |
| desktop | ≥ 1024px | 2–3 colunas; header em 2 linhas; tabela completa |

Header (todas as faixas): linha 1 = título + veredito resumido + tempo de leitura; linha 2 =
filtros + chips + toggle + limpar. Em mobile a linha 2 vira `<details>` com um resumo de chips.

### 2.4 Componentes

| Componente | Marcadores de teste | Notas |
|---|---|---|
| **Veredito** | `[data-veredito]`, `[data-tempo-leitura]` | aparece antes de qualquer `<canvas>` |
| **Card de nicho** | `article.niche[data-codigo]`, `[data-nome]`, `[data-score]`, `[data-faixa-rank]`, `[data-estabilidade]`, `[data-tese]`, `[data-flag]`, `[data-cta]` | 3 cards de destaque |
| **Chips de recorte** | `[data-chips]`, `[data-chip]`, `[data-chip-remover]` | um por filtro ativo |
| **Tabela** | `#busca`, `#contador`, `#tabela thead` (sticky), `.paginacao`, `#btn_csv` | paginação de 25 |
| **Dossiê** | `#tab-dossie`, `[data-dossie-secao]` ×7, `[data-proximos-passos]` | deep-link `#dossie=<código>` |
| **Estado vazio** | `.estado-vazio` + ação "limpar filtros" | substitui canvas em branco |

### 2.5 Estratégia de renderização (lazy)

1. **Por aba** (já existe): só a aba ativa inicializa ECharts — hoje 1/18 na carga; manter.
2. **Dados em dois blocos**: `#dados-core` (~200 KB: famílias, score, dimensões, sensibilidade,
   evitar, meta) lido no boot; `#dados-detalhe` (~1,4 MB: séries, sazonalidade, preços, órgãos,
   regiões, fornecedores, concorrência, municípios) em `<script type="application/json">`
   `JSON.parse` **após o primeiro paint** (`requestIdleCallback`, fallback `setTimeout 0`).
   Enquanto não chega, os gráficos mostram *skeleton* e o veredito/cards funcionam.
3. **Memoização por estado**: `render*` guarda a chave `(aba, ano, sec, regiao, familia, real)` e
   não recalcula dados se a chave não mudou — alvo direto do budget de 200 ms.
4. **Gráficos pesados** (treemap, scatter, heatmap) só inicializam quando a aba fica visível e o
   card entra no viewport (`IntersectionObserver` com `rootMargin: 200px`).

### 2.6 Acessibilidade (WCAG 2.1 AA)

- `nav` como `role="tablist"` com `aria-selected`, `tabindex` móvel e setas ←/→; painéis `role="tabpanel"`.
- *Skip link* "Ir para o conteúdo".
- Foco visível `:focus-visible{outline:3px solid var(--c-focus); outline-offset:2px}`.
- Tabela rolável: `tabindex="0"` + `role="region"` + `aria-label` (fecha `scrollable-region-focusable`).
- Gráfico: container com `role="img"` + `aria-label` = título-pergunta + resumo numérico curto;
  `<canvas>` ganha `aria-hidden="true"`.
- Cor nunca é canal único: badges com ícone textual (▲ ▼ ⚠) + rótulo.
- `aria-live="polite"` no contador da tabela ("N de 155") e nos chips.
- Contraste alvo 4.5:1 para texto, 3:1 para bordas de foco (verificar com axe + cálculo manual).

### 2.7 Impressão

`@media print`: esconde header, nav, filtros, chips e botões; mostra apenas a aba ativa (padrão:
Dossiê); A4 com margem 12 mm; `break-inside: avoid` nos blocos; rodapé com data e id do agregado.

## 3. Orçamento de performance

| Métrica | Baseline R0 | Meta R4 | Como medir |
|---|---|---|---|
| FCP desktop | 516 ms | ≤ 2000 ms | `performance.getEntriesByName('first-contentful-paint')` |
| FCP mobile (CPU 4×) | 588 ms | ≤ 4000 ms | Playwright `cdp` throttling |
| Troca de aba p95 | **418 ms** | ≤ 200 ms | 3 trocas por aba, p95 |
| Aplicar filtro p95 | 150 ms | ≤ 200 ms | `performance.now()` no handler + layout |
| Linhas no DOM (tabela) | 155 | ≤ 40 (25/página) | `querySelectorAll('#tabela tbody tr').length` |
| HTML único | 2,69 MB | ≤ 15 MB | tamanho do arquivo |
| JSON | 1,65 MB | ≤ 8 MB | tamanho do `panel_data.json` |
| Heap JS | 14 MB | ≤ 60 MB | `performance.memory.usedJSHeapSize` |
| Requisições externas | 0 | 0 | listener de `request` no Playwright |

## 4. Riscos e mitigação

| Risco | P | Impacto | Mitigação |
|---|---|---|---|
| Quebrar número ao refatorar | M | **Alto** | golden snapshot + AR-25 em toda fatia; se divergir, fatia revertida |
| Split do JSON deixar gráfico sem dado | M | Alto | `estado-dados-pendentes` + teste que força `detalhe` ausente e valida skeleton |
| Inserir aba Dossiê quebrar testes por índice | A | Médio | testes passam a clicar por rótulo (`get_by_role("tab", name=...)`) |
| Paginação quebrar export CSV | M | Alto | export lê o *array* do recorte, nunca o DOM (AR-11) |
| Acessibilidade regredir com canvas | A | Médio | `role="img"`+`aria-label` + axe por viewport |
| Ganhar a11y perdendo densidade | M | Baixo | 12px só em texto de leitura; eixos a 11px (Q12 aprovada) |
| Performance piorar com 9 abas | B | Médio | lazy por aba + memoização + parse tardio; medir a cada fatia |
| Escopo crescer (14 US) | A | Médio | Musts primeiro (V1–V8); Should/Could em V9 |
| `docs/index.html` divergir do `output/` | B | Baixo | `build` grava os dois na mesma execução (já implementado) |

## 5. Matriz de rastreabilidade (US ↔ AR ↔ arquivo ↔ teste)

| US | AR | Arquivo(s) | Teste | Evidência |
|---|---|---|---|---|
| US-01 | AR-01, AR-02 | `panel/body.py`, `panel/js_charts.py` (`renderVeredito`, `renderCards`) | `tests/retrofit/test_decisao.py` | `logs/retrofit/r4/*_decisao.png` |
| US-02 | AR-03, AR-04 | `panel/tokens_css.py`, `js_charts.py` | `test_decisao.py::test_hierarquia` | screenshot + DOM |
| US-03 | AR-05, AR-06 | `js_charts.py` (cards), `js_core.py` (badges) | `test_decisao.py::test_incerteza` | screenshot |
| US-04 | AR-07 | `js_charts.py::tese` | `test_decisao.py::test_tese_riscos` | DOM |
| US-05 | AR-08, AR-09 | `panel/body.py` (`#tab-dossie`), `js_charts.py::renderDossie`, `js_core.py` (URL) | `tests/retrofit/test_dossie.py` | `r4/dossie.png`, `print.pdf` |
| US-06 | AR-10…12 | `js_core.py` (busca, paginação, sticky, export) | `tests/retrofit/test_tabela.py` | log + `nicho_score.csv` |
| US-07 | AR-13, AR-14 | `js_core.py` (chips, URL), `body.py` | `tests/retrofit/test_filtros.py` | screenshot + URL |
| US-08 | AR-15, AR-16 | `tokens_css.py` (`@media`), `js_core.py` (tabela→cards) | `tests/retrofit/test_responsivo.py` | 3 screenshots |
| US-09 | AR-17, AR-18 | `tokens_css.py`, `body.py`, `js_core.py` (tabs ARIA) | `tests/retrofit/test_a11y.py` | `logs/retrofit/axe.json` |
| US-10 | AR-19, AR-20 | `js_core.py` (lazy/memo), `body.py` | `tests/retrofit/test_perf.py` | `logs/retrofit/perf.json` |
| US-11 | AR-21, AR-22 | `tokens_css.py` | `tests/retrofit/test_tipografia.py` | `audit.json` pós |
| US-12 | AR-23 | `tokens_css.py` (`@media print`) | `tests/retrofit/test_print.py` | PDF |
| US-13 | AR-24 | `js_charts.py`, `js_core.py` | `tests/retrofit/test_estados.py` | screenshot |
| US-14 | AR-25 | — (golden) | `tests/retrofit/test_paridade.py` | `logs/retrofit/paridade.json` |

Cobertura: **14/14 US com pelo menos um teste automatizado**; 25/25 AR mapeados.

## 6. Testes novos

`tests/retrofit/` com fixture de página Playwright única (sessão) e marcador `@pytest.mark.retrofit`:

- `conftest.py` — abre `docs/index.html` uma vez, expõe `page`, `viewports`, injeta axe.
- `golden_series.json` — **congelado antes da primeira mudança** (séries + CSV + hash).
- `test_paridade.py` — AR-25 (roda em toda fatia).
- demais testes por US, com asserções sobre seletores `data-*` definidos no §2.4.

Regra: teste novo **não substitui** A1–A12; eles continuam rodando em `qa.py` e `pytest` raiz.

## 7. Definition of Done do retrofit

1. 10 US Must com AR verdes; Should/Could com status declarado.
2. A1–A12 verdes (G3, G4, QA) e **A7b/A7c/A7d/A7e** mantidos.
3. I1–I7 intactos, inclusive AR-25 (paridade de números 100%).
4. Budgets do §3 atendidos; axe 0 critical/serious.
5. Rubrica ≥ 4/5 nos 3 viewports (nenhum critério < 3).
6. `docs/index.html` republicado e idêntico ao `output/`.
7. `STATE.md`, `TASKS_RETROFIT.md` e `RELATORIO_RETROFIT.md` atualizados.

## 8. O que este plano não faz

Não altera `panel_data.json` em conteúdo (só a forma de embutir/parsear); não toca em
`analyze.py`/`score.py`; não muda pesos, limiares ou a lista de regulados; não cria dependências
novas em runtime (ECharts segue embutido; axe é ferramenta de teste, não do painel).
