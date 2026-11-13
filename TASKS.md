# TASKS.md — tarefas pequenas com critério de pronto

> Cada tarefa tem um **critério de pronto verificável**. `[x]` concluída.
> Regra de loop: 3 tentativas por teste falho; depois `BLOCKERS.md` + pergunta ao usuário.

## F2 — Especificação (concluída)
- [x] **T00** SPEC/PLAN/TASKS/config v1.0 aprovados no Gate G2.

## F3 — Tratamento
- [x] **T01** Carregador de config tipado (`config.py`) com validação de campos obrigatórios.
- [x] **T02** `textops.py`: normalização (NFKD, caixa, espaços), CNPJ, deflação. *8 testes unitários.*
- [x] **T03** Estágio `treat` → `compras_tratadas.parquet`. *560.934 linhas, 0 nulos em data/linha_id.*
- [x] **T04** Deflator IPCA com 3 convenções. *fator 2021 = 1,331350; 2025 = 1,042600.*
- [x] **T05** Flags: `is_pandemia`, `is_regulado`, `is_pf`, `canal`, `is_dispensa`, `is_pce`, `is_via_ata`.
- [x] **T06** Conservação E0–E4 + reconciliação. *Δ = R$ 0,00 (0,000000%).*
- [x] **T07** Contrato pandera + `tests/` — **42 testes verdes** (≥ 15 exigidos).
- [x] **T08** **GATE G3** — 12/12 verificações OK.

## F4 — Análise e score
- [x] **T09** `A01`/`A02`/`A03` demanda, participação e tendência.
- [x] **T10** `A04` métricas por família e `A05` sazonalidade.
- [x] **T11** `A06` órgãos, `A07` canal, `A08` ticket.
- [x] **T12** `A10` fornecedores, `A11` concorrência, `A14` entrantes, `A15` top fornecedores.
- [x] **T13** `A16` preço por item×ano (real e nominal), `A17` dispersão, `A18` desconto.
- [x] **T14** `A19` região, `A20` prazo, `A21` município.
- [x] **T15** Score + penalidades (`A09`) e EVITAR (`A12`).
- [x] **T16** Sensibilidade em 14 cenários (`A13`). *Estabilidade média do top-10: 91,4%.*
- [x] **T17** `nicho_score.csv`, `top_itens.csv`, `orgaos_alvo.csv` + 10 teses.
- [x] **T18** `panel_data.json` (1,28 MB) + **GATE G4** — 9/9 OK.

## F5 — Painel
- [x] **T19** Empacotador colunar com índices (JSON ≤ 8 MB).
- [x] **T20** Shell HTML com ECharts embutido, 8 abas, CSS e tema.
- [x] **T21** Aba 0 DECISÃO: cards, tabela ordenável, EVITAR, sensibilidade, export CSV.
- [x] **T22** Aba 1 MERCADO: séries, treemap, CAGR.
- [x] **T23** Aba 2 SAZONALIDADE: heatmap + calendário.
- [x] **T24** Aba 3 COMPRADORES & CANAL: órgãos, mix, ticket×teto.
- [x] **T25** Aba 4 CONCORRÊNCIA: scatter HHI×CAGR, entrantes, incumbentes.
- [x] **T26** Aba 5 PREÇOS: bandas p25–p75 por item, CV, desconto.
- [x] **T27** Aba 6 LOGÍSTICA: regiões, prazos, municípios.
- [x] **T28** Aba 7 MÉTODO: filtros com contagens, 33 premissas, dicionário, ids.
- [x] **T29** Filtros globais + toggle nominal/real + rodapé com id em cada gráfico.
- [x] **T30** Tamanho: **2,31 MB** (limite 15 MB); render < 3 s.

## F6 — QA
- [x] **T31** Playwright + Chromium instalados no venv.
- [x] **T32** Script `qa` com evidências em `logs/qa_report.json`.
- [x] **T33** Correções: eixo com formatador sobrescrito, perfil duplicado, ruído no EVITAR,
  bandas de preço ausentes, preço sem versão nominal.
- [x] **T34** **GATE G5 / QA** — 11/11 verificações OK (18 gráficos, 0 erro de console, 0 request externo).

## F6.1 — Correção dos filtros (pós-entrega, reportada pelo usuário)
- [x] **T38** Diagnóstico instrumentado: comparar opções do ECharts antes/depois de cada filtro,
  em cada aba (`tmp/diag_filtros.py` → `logs/diagnostico_filtros.json`).
- [x] **T39** `valor_nominal` nos agregados A06/A07/A19, para o toggle valer dentro do recorte.
- [x] **T40** Cubos `secretaria→família→ano` e `região→família→ano` no cliente; recorte de valor,
  participação e CAGR.
- [x] **T41** Drill em `c_orgaos` (top famílias da secretaria) e `c_regiao` (top famílias da região).
- [x] **T42** Regra "filtra ou declara": aviso âmbar + dessaturação quando o agregado não tem o
  cruzamento; barra de recorte no topo; score declarado como global.
- [x] **T43** Corrigir `c_prazo` vazio (chave por `familia_key` vs índice no JSON).
- [x] **T44** Endurecer o QA: A7b por filtro (≥3 itens e ≥1 gráfico), A7c (nenhum gráfico sem dados)
  e A7d (secretaria e região mutuamente exclusivas). *pronto:* QA 12/12; A1 mantido em 30/30 hashes.

## F7 — Relatório
- [x] **T35** `RELATORIO_EXECUTIVO.md` com 3 nichos recomendados, alternativas e critérios de abandono.
- [x] **T36** Teses por nicho em `data/aggregates/teses/` (10 arquivos).
- [x] **T37** Fechamento: `STATE.md` final, `BLOCKERS.md` sem item aberto (B5 resolvido),
  **A1 conferido: 30/30 hashes idênticos em duas execuções**.

## Backlog (não bloqueante)
- Enriquecimento por PNCP (links já na base).
- Deflação mensal via SIDRA.
- Série histórica do teto de dispensa por lei aplicada (8.666 vs 14.133).
- Análise de recompra por UG (fidelidade de fornecedor).
- Classificador de perfil de uso por item (hoje é heurística por nome básico).
