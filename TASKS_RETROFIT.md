# TASKS_RETROFIT.md — fatias verticais de execução

Deriva de `PLAN_RETROFIT.md` (aprovado em R2). Estado final da execução (R4).
Legenda: `[x]` pronto e verificado · **PR** = critério de pronto.

---

## V1 · Invariantes (fatia sem visual)
- [x] **T1.1** Golden snapshot congelado antes de qualquer mudança.
  **PR:** `tests/retrofit/golden_series.json` (18 gráficos, 155 linhas, hashes).
- [x] **T1.2** Teste de paridade (AR-25) — `tests/retrofit/test_paridade.py`, 3 testes.
- [x] **T1.3** Baseline pré-retrofit registrado em `logs/retrofit/audit.json`.

## V2 · Tokens, tipografia e base acessível
- [x] **T2.1** `panel/tokens_css.py` com tokens; 2 raios e 2 fontes (AR-22).
- [x] **T2.2** Interface ≥ 12px; eixos a 11px (Q12). **PR:** 389 → **0** textos pequenos (AR-21).
- [x] **T2.3** Skip link, `:focus-visible`, `prefers-reduced-motion`, `nav role=tablist` com setas,
  regiões roláveis focáveis. **PR:** axe 1 → **0** serious (AR-17, AR-18).

## V3 · Header, filtros, chips e URL
- [x] **T3.1** Header em 2 linhas; ≤599px filtros em painel colapsável. **PR:** AR-15 (0 overflow).
- [x] **T3.2** Chips removíveis + limpar tudo, `aria-live`. **PR:** AR-13.
- [x] **T3.3** Estado na URL (`ano/sec/regiao/familia/aba/dossie`), hidratado no boot. **PR:** AR-14.

## V4 · Camada de decisão
- [x] **T4.1** `config.yaml → negocio.recomendados` (Q11a) + `meta.recomendados` no JSON.
- [x] **T4.2** `[data-veredito]` antes de qualquer `<canvas>`. **PR:** AR-01/AR-02.
- [x] **T4.3** Card: código 12px, score 36px, faixa e estabilidade. **PR:** AR-03/04/05.
- [x] **T4.4** Tese ≤140 caracteres iniciando por verbo + 2 riscos. **PR:** AR-07.
- [x] **T4.5** Badges com ícone + texto. **PR:** AR-06.

## V5 · Tabela utilizável
- [x] **T5.1** Busca por nome/código + contador. **PR:** AR-10.
- [x] **T5.2** Paginação de 25, `thead` sticky, região focável. **PR:** AR-12 (155 → 25 no DOM).
- [x] **T5.3** CSV do recorte completo. **PR:** AR-11 (155 linhas com busca vazia; N com busca).

## V6 · Dossiê do nicho
- [x] **T6.1** Aba `#tab-dossie` com 7 seções. **PR:** AR-08.
- [x] **T6.2** Deep-link `?dossie=<código>`. **PR:** AR-09.
- [x] **T6.3** Próximos passos derivados de calendário/órgãos + critérios de abandono.

## V7 · Responsivo completo
- [x] **T7.1** Tabela → cartões abaixo de 600px. **PR:** AR-16.
- [x] **T7.2** Gráficos com altura reduzida no mobile. **PR:** nenhum estouro (AR-15).

## V8 · Performance
- [x] **T8.1** JSON em `<script type="application/json">` (não bloqueia o 1º paint).
  **PR:** FCP 516 → 252 ms desktop; 588 → 264 ms mobile (AR-19).
- [x] **T8.2** Abas aquecidas + render só da aba ativa. **PR:** troca de aba p95 418 → 85–96 ms (AR-20).

## V9 · Polimento
- [x] **T9.1** `@media print` verificado por emulação de mídia. **PR:** AR-23.
- [x] **T9.2** Estado vazio central no `draw()` (canvas oculto + aviso). **PR:** AR-24.

## V10 · Fechamento
- [x] **T10.1** Regressão completa: 67 testes verdes + QA 13/13 + G3/G4 verdes.
- [x] **T10.2** Rubrica 4,9 (nenhum critério < 3).
- [x] **T10.3** `RELATORIO_RETROFIT.md` + `STATE.md` + `docs/` republicado.

---

## Fora desta lista (Won't do spec)
Framework JS, backend, novas fontes, mudança de pesos/thresholds, i18n.

---

## Correção pós-R4 (16/11) — filtros inertes
- [x] **T11.1** Diagnóstico por aba (`tools/retrofit/diag_filtros_por_aba.py`): Dossiê e Método inertes.
- [x] **T11.2** Dossiê honra família e ano; secretaria/região declaradas com aviso âmbar.
- [x] **T11.3** Nicho padrão do dossiê usa ranking global (não contradiz o aviso).
- [x] **T11.4** Método com declaração permanente de que filtros não se aplicam.
- [x] **T11.5** `marca()` reaproveita o elemento de aviso do HTML (sem duplicar).
- [x] **T11.6** QA por aba com escopo no painel visível: A7f/A7g/A7h — 15/15.
