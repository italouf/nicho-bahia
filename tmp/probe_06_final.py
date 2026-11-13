"""F1 — probes finais: coerência no escopo material, tipo_calculo, PCE, COVID, ticket vs teto."""
from __future__ import annotations

import sys

import duckdb
import pandas as pd

FILES = [
    rf"C:\Users\Micro\source\repos\PL\nicho-bahia\data\_meta\staging\raw_{y}.parquet"
    for y in (2021, 2022, 2023, 2024, 2025)
]


def con() -> duckdb.DuckDBPyConnection:
    c = duckdb.connect()
    c.execute("SET threads TO 4")
    lista = "[" + ", ".join(f"'{f}'" for f in FILES) + "]"
    c.execute(f"CREATE VIEW raw AS SELECT * FROM read_parquet({lista}, union_by_name=true)")
    c.execute(
        "CREATE VIEW mat AS SELECT * FROM raw "
        "WHERE tipo_do_item='Material' AND afm_aps IS NOT NULL"
    )
    return c


def show(t: str, df: pd.DataFrame) -> None:
    print(f"\n=== {t} ===")
    with pd.option_context("display.width", 220, "display.max_columns", 30, "display.max_colwidth", 55):
        print(df.to_string(index=False))


def main() -> None:
    c = con()

    show("1 coerência por tipo_calculo (toda a base)",
         c.execute("""
         SELECT coalesce(tipo_calculo,'(nulo)') AS tipo_calculo, count(*) AS linhas,
                count(*) FILTER (WHERE abs(qtd_contratada*valor_unitario - valor_total)
                                   > greatest(0.05, 0.01*abs(valor_total))) AS incoerentes,
                count(*) FILTER (WHERE abs(valor_total - valor_unitario) <= 0.005*abs(valor_unitario)) AS total_igual_unit,
                round(sum(valor_total),2) AS valor
         FROM raw WHERE qtd_contratada IS NOT NULL AND valor_unitario IS NOT NULL AND valor_total IS NOT NULL
         GROUP BY 1 ORDER BY linhas DESC""").fetch_df())

    show("2 ratio total/(qtd*unit) em faixas (incoerentes)",
         c.execute("""
         SELECT CASE
                  WHEN r BETWEEN 0.99 AND 1.01 THEN '1 ~1'
                  WHEN r BETWEEN 11.5 AND 12.5 THEN '12 (meses)'
                  WHEN r BETWEEN 59 AND 61 THEN '60 (meses)'
                  WHEN r BETWEEN 23.5 AND 24.5 THEN '24'
                  WHEN r BETWEEN 35.5 AND 36.5 THEN '36'
                  WHEN r < 1 THEN '<1'
                  ELSE 'outros'
                END AS faixa, count(*) AS linhas, round(sum(valor_total),2) AS valor
         FROM (SELECT valor_total/nullif(qtd_contratada*valor_unitario,0) AS r, valor_total
               FROM raw WHERE qtd_contratada>0 AND valor_unitario>0 AND valor_total IS NOT NULL) x
         GROUP BY 1 ORDER BY linhas DESC""").fetch_df())

    show("3 MATERIAL: coerência (qtd x unit vs total)",
         c.execute("""
         SELECT count(*) AS linhas,
                count(*) FILTER (WHERE abs(qtd_contratada*valor_unitario - valor_total)
                                   > greatest(0.05, 0.01*abs(valor_total))) AS incoerentes,
                round(100.0*count(*) FILTER (WHERE abs(qtd_contratada*valor_unitario - valor_total)
                                   > greatest(0.05, 0.01*abs(valor_total)))/count(*),3) AS pct,
                round(sum(valor_total),2) AS soma_total,
                round(sum(qtd_contratada*valor_unitario),2) AS soma_qtd_x_unit
         FROM mat WHERE qtd_contratada IS NOT NULL AND valor_unitario IS NOT NULL AND valor_total IS NOT NULL""").fetch_df())

    show("4 MATERIAL: incoerentes por tipo_calculo",
         c.execute("""
         SELECT coalesce(tipo_calculo,'(nulo)') AS tipo_calculo, count(*) AS linhas,
                count(*) FILTER (WHERE abs(qtd_contratada*valor_unitario - valor_total)
                                   > greatest(0.05, 0.01*abs(valor_total))) AS incoerentes,
                count(*) FILTER (WHERE abs(valor_total-valor_unitario) <= 0.005*abs(valor_unitario)) AS total_igual_unit
         FROM mat WHERE qtd_contratada IS NOT NULL AND valor_unitario IS NOT NULL AND valor_total IS NOT NULL
         GROUP BY 1 ORDER BY linhas DESC""").fetch_df())

    show("5 MATERIAL: ticket por linha vs teto dispensa",
         c.execute("""
         SELECT _src_year AS ano, count(*) AS linhas,
                round(quantile_cont(valor_total,0.25),2) AS p25,
                round(median(valor_total),2) AS p50,
                round(quantile_cont(valor_total,0.75),2) AS p75,
                round(quantile_cont(valor_total,0.95),2) AS p95,
                count(*) FILTER (WHERE valor_total <= 65492.11) AS ate_teto,
                round(100.0*count(*) FILTER (WHERE valor_total <= 65492.11)/count(*),2) AS pct_ate_teto
         FROM mat WHERE valor_total > 0 GROUP BY 1 ORDER BY 1""").fetch_df())

    show("6 MATERIAL: ticket por AFM/APS (proxy do teto legal)",
         c.execute("""
         WITH a AS (SELECT afm_aps, sum(valor_total) AS v FROM mat
                    WHERE valor_total>0 GROUP BY 1)
         SELECT count(*) AS afms, round(median(v),2) AS p50, round(quantile_cont(v,0.75),2) AS p75,
                count(*) FILTER (WHERE v<=65492.11) AS afms_ate_teto,
                round(100.0*count(*) FILTER (WHERE v<=65492.11)/count(*),2) AS pct_afms_ate_teto
         FROM a""").fetch_df())

    show("7 MATERIAL por forma de contratação",
         c.execute("""
         SELECT forma_contratacao, count(*) AS linhas, round(sum(valor_total),2) AS valor,
                round(median(valor_total),2) AS ticket_mediano,
                count(DISTINCT cnpj) AS cnpjs
         FROM mat WHERE valor_total IS NOT NULL GROUP BY 1 ORDER BY valor DESC""").fetch_df())

    show("8 PCE por ano (toda a base e material)",
         c.execute("""
         SELECT _src_year AS ano,
                count(*) FILTER (WHERE pce_pedido_cotacao IS NOT NULL) AS linhas_pce_total,
                round(sum(valor_total) FILTER (WHERE pce_pedido_cotacao IS NOT NULL),2) AS valor_pce_total,
                count(*) FILTER (WHERE pce_pedido_cotacao IS NOT NULL AND tipo_do_item='Material') AS linhas_pce_mat
         FROM raw GROUP BY 1 ORDER BY 1""").fetch_df())

    show("9 COVID por ano",
         c.execute("""
         SELECT _src_year AS ano, count(*) AS linhas,
                count(*) FILTER (WHERE marcacao_covid='Sim') AS covid_sim,
                count(*) FILTER (WHERE marcacao_vacina_covid='Sim') AS vacina_sim,
                count(*) FILTER (WHERE contrato_emergencial_cgst='Sim') AS emergencial_sim,
                round(sum(valor_total) FILTER (WHERE marcacao_covid='Sim'),2) AS valor_covid
         FROM raw GROUP BY 1 ORDER BY 1""").fetch_df())

    show("10 MATERIAL: distribuição de famílias por nº de linhas",
         c.execute("""
         WITH f AS (SELECT familia_catalogo, count(*) AS linhas FROM mat GROUP BY 1)
         SELECT CASE WHEN linhas>=10000 THEN '>=10k' WHEN linhas>=1000 THEN '1k-10k'
                     WHEN linhas>=100 THEN '100-1k' WHEN linhas>=10 THEN '10-100' ELSE '<10' END AS faixa,
                count(*) AS familias, sum(linhas) AS linhas
         FROM f GROUP BY 1 ORDER BY 1""").fetch_df())

    show("11 MATERIAL: tipo_item_especifico_comum x UM (top)",
         c.execute("""
         SELECT tipo_item_especifico_comum, count(*) AS linhas, round(sum(valor_total),2) AS valor
         FROM mat GROUP BY 1 ORDER BY linhas DESC""").fetch_df())

    show("12 uf_local_entrega e regiao_local_entrega",
         c.execute("""
         SELECT uf_local_entrega, count(*) AS linhas FROM raw GROUP BY 1 ORDER BY linhas DESC LIMIT 5""").fetch_df())
    show("12b regioes",
         c.execute("""
         SELECT regiao_local_entrega, count(*) AS linhas, round(sum(valor_total),2) AS valor
         FROM raw GROUP BY 1 ORDER BY linhas DESC LIMIT 20""").fetch_df())

    show("13 fornecedores UF!=BA (material)",
         c.execute("""
         SELECT CASE WHEN uf_fornecedor='BA' THEN 'BA' WHEN uf_fornecedor IS NULL THEN '(nulo)' ELSE 'outra UF' END AS grupo,
                count(*) AS linhas, count(DISTINCT cnpj) AS cnpjs, round(sum(valor_total),2) AS valor
         FROM mat GROUP BY 1 ORDER BY valor DESC""").fetch_df())

    show("14 fornecedores com CNPJ de 10 dígitos (exemplos mascarados)",
         c.execute("""
         SELECT count(*) AS linhas, count(DISTINCT cnpj) AS cnpjs, min(cnpj) AS exemplo
         FROM raw WHERE length(regexp_replace(cnpj,'[^0-9]','','g'))=10""").fetch_df())

    show("15 material: nº de fornecedores por família (top volume)",
         c.execute("""
         SELECT familia_catalogo, count(DISTINCT cnpj) AS cnpjs, count(*) AS linhas,
                round(sum(valor_total),2) AS valor
         FROM mat WHERE valor_total IS NOT NULL
         GROUP BY 1 HAVING count(*)>=200 ORDER BY valor DESC LIMIT 25""").fetch_df())

    show("16 nome_basico repetido em familias diferentes?",
         c.execute("""
         SELECT count(*) AS nomes_em_varias_familias FROM (
           SELECT nome_basico FROM mat GROUP BY 1 HAVING count(DISTINCT familia_catalogo)>1)""").fetch_df())

    show("17 item (descrição) nulo ou vazio na base",
         c.execute("""
         SELECT count(*) AS linhas,
                count(*) FILTER (WHERE item IS NULL) AS item_nulo,
                count(*) FILTER (WHERE nome_basico IS NULL) AS nome_nulo,
                count(*) FILTER (WHERE um IS NULL) AS um_nulo,
                count(*) FILTER (WHERE familia_catalogo IS NULL) AS familia_nula
         FROM raw""").fetch_df())


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
