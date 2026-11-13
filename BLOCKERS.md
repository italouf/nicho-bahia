# BLOCKERS.md — bloqueios e contornos

> Ferramenta ausente NÃO para o trabalho: registra-se aqui e usa-se o fallback.
> Exceção: terminal/Python são bloqueantes (presentes nesta sessão).

## B1 — DuckDB: extensão `excel` não carrega (RESOLVIDO com contorno)
- Sintoma: `INSTALL excel` conclui, mas `LOAD excel` falha com
  `IOException: Extension "...\excel.duckdb_extension" could not be loaded: Uma rotina de
  inicialização da biblioteca de vínculo dinâmico (DLL) falhou.`
- Ambiente: duckdb 2.0.0, Windows x86_64, Python 3.14.3.
- Contorno: leitura dos XLSX com `python-calamine` 0.9.1 (Rust) → parquet → DuckDB lê parquet.
- Impacto: nenhum no resultado; apenas uma etapa a mais no pipeline.

## B2 — Plugins MCP ausentes (RESOLVIDO com contornos)
Ausentes na sessão: `filesystem`, `duckdb`, `playwright`, `context7`, `sequential-thinking`.
- filesystem → `pwsh` + tools `read`/`write` do harness (escrita restrita ao workspace por convenção).
- duckdb MCP → `duckdb` via Python.
- playwright MCP → QA do painel via `playwright` Python + Chromium headless (F6). Se a instalação
  do navegador falhar, o QA será feito por parser de DOM (leitura do HTML/JSON embutido) + checagem
  estática de `console.error` por análise do script, e isso será declarado no Gate G5.
- context7 → `help()`/`dir()` das versões instaladas.
- sequential-thinking → `PLAN.md`/`TASKS.md`.

## B3 — Sem acesso a dados de pagamento/adimplência
- Limitação da base (declarada no painel). Não é bloqueio: o escopo do projeto é demanda e
  concorrência, não fluxo de caixa.

## B4 — Deflação com granularidade anual
- IPCA é aplicado por ano (não por mês) porque a premissa fornecida é anual. Declarado como
  limitação no painel e em ASSUMPTIONS.md. Se houver acesso a SIDRA em F2, refinar para mensal.

## B5 — Determinismo dos agregados (RESOLVIDO)
- Sintoma: o teste A1 falhou na primeira verificação — 9 agregados saíam com ordem de linha diferente
  entre execuções.
- Causa: (a) o parquet tratado era escrito sem `ORDER BY`, e o DuckDB não preserva ordem em
  agregações multi-thread; (b) vários `ORDER BY` da análise tinham empates (duas famílias com o
  mesmo valor) e a ordem entre empatados variava.
- Correção: `ORDER BY linha_id` ao materializar a tabela tratada; ordenação total por todas as
  colunas na escrita de cada agregado; desempate explícito em itens-âncora, órgãos-alvo,
  fornecedores, municípios e nos CSVs.
- Verificação: 30/30 hashes idênticos em duas execuções consecutivas de `--from treat`.

## B6 — Filtros do painel inertes (RESOLVIDO)
- Sintoma relatado pelo usuário: os filtros do painel não funcionavam.
- Diagnóstico (`logs/diagnostico_filtros.json`, comparação de opções do ECharts antes/depois):
  - **secretaria**: 0 de 18 gráficos reagiam — `state.sec` era lido e usado apenas para colorir uma
    barra; nunca filtrava;
  - **região**: 0 de 18 — a variável existia e nunca era consultada;
  - **ano**: 4 de 18;
  - **família**: 9 de 18.
- Causa raiz: a camada de filtros foi implementada como "highlight" em vez de recorte, e não havia
  dado de valor por `secretaria × família × ano` nem por `região × família × ano` no JSON do painel.
- Correção:
  1. `valor_nominal` incluído nos agregados A06/A07/A19 (o toggle precisava valer também no recorte);
  2. cubos `secretaria → família → ano` e `região → família → ano` montados no cliente;
  3. `c_orgaos` e `c_regiao` passam a fazer **drill** quando o filtro correspondente está ativo;
  4. regra "filtra ou declara": gráfico sem cruzamento mostra aviso âmbar e dessaturação;
  5. barra de recorte no topo listando os filtros ativos.
- **Bug secundário encontrado junto**: `c_prazo` estava **vazio desde a primeira versão** — o
  `panel_data.json` gravava `prazo` indexado por `familia_key` e o JS lia por índice.
- **Teste que faltava**: o A7b original verificava apenas `c_serie` com o filtro de família. Agora o
  QA exige que **cada um dos 4 filtros** altere ≥ 3 itens e ≥ 1 gráfico (A7b-ano/secretaria/região/
  família), que **nenhum gráfico fique sem dados** (A7c) e que os recortes de secretaria e região
  sejam **mutuamente exclusivos** (A7d). QA: 12/12.


