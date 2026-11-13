# PLAN.md — plano de execução

Versão 1.0 · 2026-11-12 · aprovado no Gate G2 antes de iniciar F3

## 1. Onde estamos

| Fase | Entrega | Status |
|---|---|---|
| F0 Inventário & ambiente | `inventory.json`, `logs/inventory.md`, `STATE.md` | ✅ |
| F1 Perfilamento | `DATA_PROFILE.md`, `data_dictionary.md`, `QUESTIONS.md` | ✅ |
| **G1** | aprovação humana (Q1–Q6) | ✅ **APROVADO** |
| F2 Especificação | `SPEC.md`, `PLAN.md`, `TASKS.md`, `config.yaml v1.0` | ✅ |
| **G2** | aprovação humana deste plano | ⏳ **AGUARDANDO** |
| F3 Tratamento + testes | `data/treated/compras_tratadas.parquet`, `tests/`, `logs/` | — |
| **G3** | automático (testes verdes) | — |
| F4 Análise + score | `data/aggregates/A01..A22`, `nicho_score.csv`, `top_itens.csv`, `orgaos_alvo.csv` | — |
| **G4** | automático (score reproduzível e reconciliado) | — |
| F5 Painel | `output/painel_decisao.html` + `panel_data.json` | — |
| F6 QA | `logs/qa_*.json`, screenshots de DOM | — |
| **G5** | automático (A1–A11) | — |
| F7 Relatório | `RELATORIO_EXECUTIVO.md`, teses por nicho | — |

## 2. Estratégia

1. **Tratamento primeiro, análise depois, painel por último.** O painel nunca vê parquet: só
   `panel_data.json`. Isso é verificado por teste (o HTML não contém `fetch`/`XMLHttpRequest`).
2. **Cada número tem dono.** Toda métrica nasce em um agregado com id (`A01`…`A22`) e esse id aparece
   no rodapé do gráfico e no JSON (`meta.ids`).
3. **Conservação antes de elegância.** O pipeline de exclusão (E0–E4) roda com log em
   `logs/conservacao.log` e reconciliação de valor antes de qualquer agregação.
4. **Reexecutável do zero.** `run.py --stage all` refaz tudo; hashes comparados no teste A1.
5. **Falha em teste**: até 3 tentativas de correção; persistindo, `BLOCKERS.md` + pergunta objetiva.

## 3. Sequência de execução e critérios de aceite por fase

### F3 — Tratamento (T01–T08)
- Entrada: 5 parquet de staging (872.257 linhas).
- Saída: `data/treated/compras_tratadas.parquet` com 560.934 linhas de material + colunas derivadas
  do `SPEC.md §3`, mais `logs/conservacao.log` e `logs/reconciliacao.json`.
- Critério de saída (G3): `pytest` verde com ≥ 15 asserções (pandera + testes de regra), reconciliação
  ≤ 0,1%, `DATA_PROFILE.md`/`data_dictionary.md` atualizados com as contagens da camada tratada.

### F4 — Análise e score (T09–T18)
- Entrada: parquet tratado.
- Saída: `A01`–`A22` em `data/aggregates/`, `panel_data.json`, os 3 CSVs e as teses.
- Critério de saída (G4): score recalculável a partir dos agregados com desvio zero; top-10 estável
  sob ±20% dos pesos reportado; reconciliação dos agregados com o tratado ≤ 0,1%.

### F5 — Painel (T19–T30)
- Entrada: **somente** `panel_data.json`.
- Saída: `output/painel_decisao.html` único, ≤ 15 MB, 8 abas, ≥ 12 gráficos, toggle nominal/real,
  4 filtros globais, export CSV.
- Critério de saída: abre em `file://` sem console error (verificado em F6).

### F6 — QA (T31–T34)
- Playwright headless: A6 (console), A7 (≥12 gráficos + filtros), A8 (toggle), A10 (≤15 MB e zero
  requests externos). Evidências em `logs/qa_*.json`.
- Critério de saída (G5): A1–A11 verdes; no máximo 2 ciclos de QA antes de escalar.

### F7 — Relatório (T35–T37)
- `RELATORIO_EXECUTIVO.md` ≤ 2 páginas: recomendação (1–3 nichos), alternativas, itens-âncora,
  órgãos, regiões, calendário, riscos e **critérios de abandono**.

## 4. Decisões técnicas

| Tema | Decisão | Motivo |
|---|---|---|
| Motor de agregação | DuckDB sobre parquet | 872 mil linhas, SQL auditável, reprodutível |
| Camada tratada | parquet único (não particionado) | 560 mil linhas cabem; simplifica hashes e testes |
| Deflação | fator por ano, convenção `inicio_ano` | aderente à premissa do IPCA 2025; selecionável |
| Percentis | `quantile_cont` do DuckDB | determinístico, sem dependência de amostragem |
| Score | percentil entre famílias elegíveis | robusto a outliers e a escalas diferentes |
| Sensibilidade | 14 cenários (±20% por peso) | cobre o requisito A11 sem explosão combinatória |
| Gráficos | ECharts embutido (baixado uma vez e inlined) | offline, `file://`, sem CDN |
| Fallback de gráficos | camada SVG própria (120 linhas) | se o download do ECharts falhar |
| Testes | pytest + pandera | exigência do projeto (A4) |
| QA | playwright Python + Chromium | MCP ausente (B2) |

## 5. Riscos e mitigação

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| Download do ECharts falhar/estar bloqueado | baixa | alto | fallback SVG próprio; registrar em BLOCKERS |
| `panel_data.json` estourar 8 MB | média | médio | formato colunar + top-N por família; teste de tamanho em T19 |
| Filtros globais exigirem cubo grande | média | médio | agregados (secretaria × família × ano) e (região × família × ano) pré-computados |
| Regiões com rótulos truncados/imprecisos | alta | baixo | normalização + bucket `indefinida`, declarado no painel |
| 35% de nulos em UO/UG FIPLAN | alta | médio | fallback para `secretaria`/`unidade` na aba de compradores |
| Score instável sob perturbação | média | alto | A11 obrigatório; se top-10 mudar muito, reportar e reduzir confiança na recomendação |
| Pandera incompatível com pandas 3.1 | baixa | médio | testes de regra em Python puro como contingência |

## 6. Orçamento de contexto

- Nunca colar a base no chat. Amostras ≤ 50 linhas.
- Cada fase entrega **arquivos**, não saída de console: os resumos no chat têm ≤ 30 linhas.
- `logs/` guarda a evidência completa; o chat recebe o ponteiro.

## 7. Definição de pronto (projeto)

1. A1–A12 verdes com evidência em `logs/`.
2. `output/painel_decisao.html` abre offline, sem erro de console, com ≥ 12 gráficos reagindo a filtros.
3. `RELATORIO_EXECUTIVO.md` com 1–3 nichos recomendados, itens-âncora, órgãos, regiões, calendário,
   riscos e critérios de abandono.
4. `STATE.md` no estado final e `BLOCKERS.md` sem item aberto.
