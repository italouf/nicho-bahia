# STATE.md — checkpoint do projeto

> Atualizado a cada tarefa. Ao retomar sessão: ler este arquivo primeiro e continuar do checkpoint.

## Identificação
- Projeto: `nicho-bahia` — seleção de nicho em compras públicas da Bahia (2021–2025)
- Workspace (única área de escrita): `C:\Users\Micro\source\repos\PL\nicho-bahia`
- Dados brutos (somente leitura): `C:\Users\Micro\source\repos\PL\compras 2021-2025`
- Idioma dos artefatos: português do Brasil
- Sessão: 2026-11-12 (America/Sao_Paulo)

## Fase atual
**CONCLUÍDO** (com correção pós-entrega em 12/11: filtros do painel e gráfico de prazos).
F0 → F7 executadas; gates G1, G2, G3, G4 e QA (G5) verdes; A1 revalidado após a correção.

## Ferramentas da sessão (verificado em 2026-11-12)
| Ferramenta | Disponível | Fallback adotado |
|---|---|---|
| terminal/shell + Python | ✅ | — (bloqueante, presente) |
| filesystem MCP | ❌ | `pwsh` + tools `read`/`write` do harness |
| duckdb MCP | ❌ | `duckdb` 2.0.0 via Python |
| playwright MCP | ❌ | `playwright` Python 1.65.1 + Chromium 1254 (instalados no venv) |
| context7 MCP | ❌ | `help()`/`dir()` da versão instalada |
| sequential-thinking | ❌ | `PLAN.md` + `TASKS.md` |
| web_search / web_fetch | ✅ | — |

Ambiente: Python 3.14.3 (venv uv), pandas 3.1.1, duckdb 2.0.0, pyarrow 26.0.1, numpy 2.5.4,
pandera 0.36.0, pytest 9.2.0, openpyxl 3.1.5, python-calamine 0.9.1, pyyaml 6.0.3,
playwright 1.65.1, jinja2 3.1.6, rapidfuzz 3.14.6.

## Decisões tomadas
1. **Leitura dos XLSX via `python-calamine`** (Rust): 5 arquivos, 872.257 linhas, ~289 MB. A extensão
   `excel` do DuckDB falha ao carregar (DLL) — B1 em BLOCKERS.md, contornado.
2. **Mapeamento de colunas por alias + overrides posicionais explícitos.** 2021 não tem `FORNECEDOR`
   (colunas do índice 26 em diante deslocadas em −1) e tem 4 cabeçalhos em branco; 2022 tem 1 coluna
   extra em branco; 2023/2024/2025 são idênticos (77 colunas).
3. **Staging em parquet com esquema explícito** e rastreabilidade total
   (`_src_file`, `_src_sheet`, `_src_row`, `_src_year`).
4. **Eixo temporal = `data_geracao_afm_aps`** (0 divergências com ANO/MÊS GERAÇÃO).
5. **Escopo = `tipo_do_item = 'Material'`** (coerente com AFM em 99,999%).
6. **`valor_total` confiável para material** (0 incoerências em 560.934; = QTD×UNIT).
7. **`valor_estimado` é unitário** → desconto calculado por unidade.
8. **Deflação IPCA anual, convenção `inicio_ano`** (2025 = 1,0426; 2021 = 1,331350).
9. **Keywords de regulação restritas a família + nome básico** — aplicá-las à descrição livre
   marcava "VEÍCULO ... a combustível" e "REFRIGERADOR ... para carne" como regulados (auditoria).
10. **Escopo analítico = material ∧ ¬regulado ∧ ¬pandemia** (352.537 linhas, R$ 10,16 bi reais).
11. **Percentil com `method='max'`** para que o melhor da dimensão receba 100 (com `average`,
    famílias com 60/60 meses ficavam em 84,5 e a dimensão perdia peso).
12. **Rótulo `perfil_uso`** (consumo recorrente / bem durável / misto) exibido ao lado do score,
    mas **fora do score** — o score mede demanda, concorrência e canal, não pós-venda.
13. **Determinismo (A1)**: `ORDER BY linha_id` na tabela tratada + ordenação total na escrita de
    cada agregado + desempates em itens/órgãos/fornecedores/CSVs.

## Artefatos produzidos
| Artefato | Status |
|---|---|
| `SPEC.md`, `PLAN.md`, `TASKS.md`, `config.yaml` (v1.0) | ✅ |
| `DATA_PROFILE.md`, `data_dictionary.md`, `QUESTIONS.md`, `ASSUMPTIONS.md`, `BLOCKERS.md` | ✅ |
| `RELATORIO_EXECUTIVO.md` | ✅ |
| `src/nicho_bahia/{paths,columns,io_raw,textops,config,logging_utils,cli,panel_data,panel_html}.py` | ✅ |
| `src/nicho_bahia/stages/{inventory,ingest,profile,treat,validate,analyze,score,build,qa}.py` | ✅ |
| `run.py` (raiz), `tests/` (42 testes), `assets/echarts.min.js` | ✅ |
| `data/_meta/{inventory,staging_manifest,profile,tratamento,analise,score}.json` | ✅ |
| `data/_meta/staging/raw_{2021..2025}.parquet` | ✅ |
| `data/treated/compras_tratadas.parquet` (560.934 linhas, 68,6 MB) | ✅ |
| `data/aggregates/*.parquet` (25) + `panel_data.json` (1,28 MB) + `teses/*.md` (10) | ✅ |
| `output/painel_decisao.html` (2,31 MB, 8 abas, 18 gráficos) | ✅ |
| `nicho_score.csv`, `top_itens.csv`, `orgaos_alvo.csv` | ✅ |
| `logs/`: run, conservacao, reconciliacao, pytest_f3, gate_g3, gate_g4, painel_manifest, qa_report | ✅ |

## Resultado
| Gate | Status | Evidência |
|---|---|---|
| G1 (humano) | ✅ APROVADO | Q1–Q6 |
| G2 (humano) | ✅ APROVADO | S1–S3 |
| G3 (automático) | ✅ VERDE | 12/12 checks; pytest 42 passed |
| G4 (automático) | ✅ VERDE | 9/9 checks |
| QA/G5 (automático) | ✅ VERDE | 12/12: 0 erro de console, 18 gráficos com dados, 0 request externo, 4/4 filtros funcionais, recortes exclusivos |
| A1 (reprodutibilidade) | ✅ | 30/30 hashes idênticos em 2 execuções |

**Recomendação:** 89.55 Café/chá/chocolate (score 75,0) · 75.10 Artigos de escritório (72,7) ·
85.40 Papel para higiene (66,7).

## Como reexecutar
```
uv run python run.py --stage all        # pipeline completo (~11 min)
uv run python run.py --from treat       # a partir do tratamento (~5 min)
uv run pytest -q                        # 42 testes
```
O painel é aberto direto no navegador: `output/painel_decisao.html` (não precisa de servidor).

## Desvios conscientes do contrato original
- `run.py` está na **raiz** do workspace (a árvore da missão sugeria `src/`), para que
  `uv run python run.py` funcione sem ajuste de `sys.path`. A lógica vive em `src/nicho_bahia/`.
- O painel tem **18 gráficos** (a missão pedia ≥ 12) e **8 abas**, como especificado.
- A lista EVITAR no painel omite famílias com valor irrelevante (< R$ 1 mi e < 0,01%), com nota
  explícita da omissão — o CSV/agregado mantém todas as 20.

## Log de execução
- 11:38–11:52 — F0: inventário, ambiente, ferramentas, workspace.
- 11:54–11:58 — ingestão: 872.257 linhas em 5 parquet.
- 12:00–12:10 — perfilamento + investigação de anomalias.
- 12:20 — **Gate G1 APROVADO**.
- 12:30 — F2: SPEC/PLAN/TASKS/config v1.0; mapas de canal e região validados.
- 14:10 — **Gate G2 APROVADO** (S1–S3).
- 16:55–17:00 — F3: tratamento (560.934 linhas), reconciliação 0,000000%.
- 17:06 — **Gate G3 VERDE** (12/12, 42 testes).
- 17:12 — F4: 25 agregados, score, 14 cenários de sensibilidade.
- 17:14 — **Gate G4 VERDE** (9/9).
- 17:20 — F5: painel 2,23 MB.
- 17:28 — F6: **QA VERDE** (7/7).
- 17:38–17:49 — execução completa `--stage all` (677 s).
- 17:54 — A1: correção do determinismo; 30/30 hashes idênticos em 2 execuções.
- 18:00 — F7: relatório executivo e fechamento.
- 19:30 — **correção pós-entrega (filtros)**: diagnóstico instrumentado mostrou secretaria e região
  inertes (0/18) e ano com 4/18. Refeita a camada de filtros (cubos secretaria/região → família → ano,
  drill em órgãos e regiões, regra "filtra ou declara", barra de recorte). Corrigido junto o gráfico
  de prazos, que estava vazio por chave errada no JSON. QA endurecido de 7 para 11 verificações.
  A1 mantido: 30/30 hashes idênticos.
