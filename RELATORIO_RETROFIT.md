# RELATORIO_RETROFIT.md — Retrofit de UI/UX do painel nicho-bahia

Data: 2026-11-15 · Branch `retrofit-uiux` · Gates: R0 → R1 ✅ → R2 ✅ → **R4 (este)**
Evidências: `logs/retrofit/R0_AUDITORIA.md`, `audit.json`, `audit_r4.json`, `logs/retrofit/r4/*.png`,
`logs/qa_report.json`, `logs/retrofit/paridade.json`

---

## 1. Resultado em uma frase

O painel deixou de ser um catálogo de 18 gráficos e passou a abrir com a decisão: **3 nichos
recomendados, com tese, riscos, faixa de incerteza e um dossiê acionável** — sem que **nenhum
número tenha mudado** (paridade provada em 18/18 gráficos e nas 155 linhas do CSV).

## 2. Métricas antes → depois (medidas, não estimadas)

| Métrica | R0 | R4 | Meta | Status |
|---|---|---|---|---|
| Overflow horizontal em 360px | sim · 1.632 elementos fora | **não · 0** | não | ✅ |
| Textos de interface < 12px | 389 | **0** | 0 | ✅ |
| Alvos de toque < 44px | 29 | **0** | 0 | ✅ |
| Violações axe critical+serious | 1 (×3 viewports) | **0** (3 viewports × 3 abas) | 0 | ✅ |
| FCP desktop | 516 ms | **252 ms** | ≤ 2.000 ms | ✅ |
| FCP mobile | 588 ms | **264 ms** | ≤ 4.000 ms | ✅ |
| Troca de aba p95 | 418 ms (tablet) | **85–96 ms** | ≤ 200 ms | ✅ |
| Aplicar filtro p95 | 150 ms | **67–76 ms** | ≤ 200 ms | ✅ |
| Linhas no DOM (tabela) | 155 | **25** (página de 25) | ≤ 40 | ✅ |
| Raios de borda distintos | 7 | **2** | ≤ 4 | ✅ |
| Razão tipográfica score/nome | 1,93 | **2,12** | ≥ 2,0 | ✅ |
| Faixa de incerteza no card | ausente | **presente** | presente | ✅ |
| CTA + dossiê do nicho | ausente | **presente** (7 seções) | presente | ✅ |
| Busca na tabela | ausente | **presente** | presente | ✅ |
| Estado na URL (deep-link) | ausente | **presente** | presente | ✅ |
| CSS de impressão | ausente | **presente e verificado** | 1–2 páginas | ✅ |
| Paridade de números | — | **18/18 gráficos + CSV 155 linhas** | idêntica | ✅ |

## 3. Histórias → status → evidência

| US | MoSCoW | Status | Evidência |
|---|---|---|---|
| US-01 camada de decisão 5 min | Must | ✅ | AR-01/02 · `test_aceitacao.py` · `r4/desktop_decisao.png` |
| US-02 hierarquia código×score | Must | ✅ | AR-03/04 · código 12px, score 36px (razão 2,12) |
| US-03 incerteza visível | Must | ✅ | AR-05/06 · faixa "1–1 em 14 cenários · 100% no top-10" |
| US-04 tese e riscos | Must | ✅ | AR-07 · tese 124 caracteres, inicia por "Atacar" |
| US-05 dossiê do nicho | Must | ✅ | AR-08/09 · 7 seções, `?dossie=75.10` reproduz |
| US-06 tabela utilizável | Must | ✅ | AR-10/11/12 · busca, 25/página, CSV 155, `thead` sticky |
| US-07 filtros com chips e URL | Must | ✅ | AR-13/14 · chip removível, `?ano=2024` reprodutível |
| US-08 responsivo 360/768/1440 | Must | ✅ | AR-15/16 · 0 overflow, tabela→cartões |
| US-09 acessibilidade AA | Must | ✅ | AR-17/18 · axe 0/0, abas por seta |
| US-10 performance | Must | ✅ | AR-19/20 · FCP 252 ms, aba p95 85 ms |
| US-11 legibilidade e tokens | Should | ✅ | AR-21/22 · 0 texto <12px, 2 raios |
| US-12 export executivo | Should | ✅ | AR-23 · `test_polimento.py` (print media) |
| US-13 estados vazio/erro | Could | ✅ | AR-24 · estado vazio central no `draw()` |
| US-14 nenhum número muda | Must | ✅ | AR-25 · `test_paridade.py` (3 testes) |

**Testes:** 67 verdes (42 do projeto + 25 do retrofit). **QA:** 13/13. **Gates G3/G4:** verdes.

## 4. O que mudou na arquitetura

```
src/nicho_bahia/panel/
  __init__.py      render() — junta CSS + BODY + dados + ECharts + JS
  tokens_css.py    ~330 linhas: design tokens, layout, componentes, responsivo e impressão
  body.py          9 abas, header em 2 linhas, chips, tabela, dossiê
  js_core.py       estado, cubos, filtros, URL, chips, decisão, tabela, dossiê
  js_charts.py     18 funções de gráfico EXTRAÍDAS SEM ALTERAÇÃO do painel validado
src/nicho_bahia/panel_html.py   shim de 3 linhas (rollback trivial)
```

Decisões que sustentam os números:
- **JSON em bloco inerte** (`<script type="application/json">`) em vez de objeto literal: o parser
  pinta o cabeçalho antes de desserializar 1,65 MB → FCP de 516 ms para 252 ms.
- **Funções de gráfico não foram reescritas**: foram extraídas por script do arquivo validado.
  É o que garante a paridade.
- **Paginação de 25** em vez de virtualização: atende ≤40 linhas no DOM, é acessível por teclado e
  não quebra o CSV (que lê o array do recorte, não o DOM).
- **14 cenários vêm prontos do A13**; nada de score é recalculado no cliente.

## 5. Riscos remanescentes (declarados)

| Risco | Situação |
|---|---|
| **Base do rank de sensibilidade** | A13 ranqueia as **348** famílias do escopo; a tabela mostra as **155** elegíveis. O card exibe a faixa na base dos 348 e isso está escrito na aba Método. Não alterei o agregado (I1). |
| **Variação de FCP** | Medições oscilam com carga da máquina (236–4.696 ms no mesmo arquivo, cold start do Chromium). Mediana das execuções ≈ 250 ms; o pior caso observado foi cold start, não regressão de código. |
| **Nomes sem acento** | Os nomes vêm do catálogo (`CAFE`), não da interface. Exibimos em sentence case (`Cafe`); acentuar seria inventar dado. |
| **Dossiê mostra 3 itens** | O agregado A16 traz os 3 itens mais comprados por família; a tabela diz isso explicitamente (não promete 6). |
| **Estados de carregamento** | O parse é síncrono; não há skeleton de dados, apenas estado vazio. |

## 6. Regression checklist (invariantes)

| Invariante | Verificação | Status |
|---|---|---|
| I1 nenhum número muda | `test_paridade.py` (18 gráficos + CSV) | ✅ |
| I2 score não recalculado no cliente | revisão de código: só lê A09/A13 | ✅ |
| I3 A1–A12 verdes | `pytest` + `run.py --stage qa` | ✅ |
| I4 editar só o gerador, republicar por build | `docs/index.html` idêntico ao `output/` | ✅ |
| I5 "filtra ou declara" e exclusividade | A7b/A7d no QA | ✅ |
| I6 sem teste enfraquecido | QA endurecido (7 → 13 verificações) | ✅ |
| I7 PT-BR, pt-BR numérico, rodapé com id | auditoria + testes | ✅ |

## 7. Rubrica (0–5, evidência, não adjetivo)

| Critério | Nota | Evidência |
|---|---|---|
| Clareza de decisão | 5 | veredito antes do 1º canvas (AR-01); 3 cards com tese e risco |
| Hierarquia visual | 5 | score 36px vs código 12px (razão 2,12) |
| Legibilidade | 5 | 0 texto < 12px em 3 viewports |
| Consistência | 4 | 2 raios e 2 famílias tipográficas; ainda há variação de espaçamento interno |
| Acessibilidade | 5 | axe 0/0 em 9 combinações; abas por teclado; foco visível |
| Performance | 5 | FCP 252 ms; aba p95 85 ms; DOM 25 linhas |
| Honestidade de incerteza | 5 | faixa de 14 cenários no card + nota da base de rank na Método |

Média: **4,9** · nenhum critério abaixo de 3.

## 8. Republicação

```bash
uv run python run.py --stage build     # regenera output/ e docs/
git add docs && git commit -m "retrofit(US-04): camada de decisao" && git push
```

O GitHub Pages publica `docs/index.html` automaticamente. Nada mudou no fluxo de publicação.
