"""F1 — investigação dirigida das anomalias detectadas no perfil.

Responde, com números pequenos:
A) valor_total vs qtd*unit: quem está errado? (ratio, top desvios)
B) forma_contratacao por ano (mudança de esquema?)
C) CNPJ sem 14 dígitos (pessoa física?)
D) duplicatas reais (chave repetida)
E) datas sujas (assinatura, fim contrato, prazo)
F) material: valor por ano, e efeito dos outliers
G) rodapé / linhas não-dado
"""
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
    return c


def show(t: str, df: pd.DataFrame) -> None:
    print(f"\n=== {t} ===")
    with pd.option_context("display.width", 200, "display.max_columns", 30, "display.max_colwidth", 60):
        print(df.to_string(index=False))


def main() -> None:
    c = con()

    # A) ratio total/(qtd*unit)
    show(
        "A1 distribuição do ratio total/(qtd*unit)",
        c.execute(
            """
            SELECT
              count(*) AS n,
              count(*) FILTER (WHERE abs(r-1) <= 0.01) AS perto_1,
              count(*) FILTER (WHERE r < 0.99) AS menor,
              count(*) FILTER (WHERE r > 1.01) AS maior,
              count(*) FILTER (WHERE abs(r - 1/qtd) <= 0.01*abs(1/qtd)) AS total_igual_unit
            FROM (
              SELECT qtd_contratada AS qtd, valor_total/nullif(qtd_contratada*valor_unitario,0) AS r
              FROM raw WHERE valor_total IS NOT NULL AND qtd_contratada > 0 AND valor_unitario > 0
            )
            """
        ).fetch_df(),
    )
    show(
        "A2 top 12 desvios absolutos",
        c.execute(
            """
            SELECT _src_year AS ano, afm_aps, nome_basico, tipo_do_item,
                   round(qtd_contratada,3) AS qtd, round(valor_unitario,2) AS unit,
                   round(valor_total,2) AS total,
                   round(qtd_contratada*valor_unitario,2) AS qtd_x_unit
            FROM raw
            WHERE qtd_contratada > 0 AND valor_unitario > 0 AND valor_total IS NOT NULL
            ORDER BY abs(qtd_contratada*valor_unitario - valor_total) DESC LIMIT 12
            """
        ).fetch_df(),
    )
    show(
        "A3 desvio por ano (soma abs e % linhas incoerentes)",
        c.execute(
            """
            SELECT _src_year AS ano, count(*) AS linhas,
                   count(*) FILTER (WHERE abs(qtd_contratada*valor_unitario - valor_total)
                                      > greatest(0.05, 0.01*abs(valor_total))) AS incoerentes,
                   round(100.0*count(*) FILTER (WHERE abs(qtd_contratada*valor_unitario - valor_total)
                                      > greatest(0.05, 0.01*abs(valor_total)))/count(*),2) AS pct,
                   round(sum(abs(qtd_contratada*valor_unitario - valor_total)),2) AS soma_desvio
            FROM raw WHERE qtd_contratada IS NOT NULL AND valor_unitario IS NOT NULL AND valor_total IS NOT NULL
            GROUP BY 1 ORDER BY 1
            """
        ).fetch_df(),
    )

    # B) forma de contratação por ano
    show(
        "B forma_contratacao x ano",
        c.execute(
            """
            SELECT forma_contratacao, _src_year AS ano, count(*) AS linhas,
                   round(sum(valor_total),2) AS valor
            FROM raw WHERE valor_total IS NOT NULL
            GROUP BY 1,2 ORDER BY forma_contratacao, ano
            """
        ).fetch_df(),
    )

    # C) CNPJ
    show(
        "C1 CNPJ: formatos",
        c.execute(
            """
            SELECT length(regexp_replace(cnpj,'[^0-9]','','g')) AS n_digitos,
                   count(*) AS linhas, count(DISTINCT cnpj) AS distintos,
                   min(cnpj) AS exemplo
            FROM raw WHERE cnpj IS NOT NULL GROUP BY 1 ORDER BY 1
            """
        ).fetch_df(),
    )
    show(
        "C2 categoria (porte) x tipo_do_item",
        c.execute(
            """
            SELECT categoria, count(*) AS linhas, count(DISTINCT cnpj) AS cnpjs,
                   round(sum(valor_total),2) AS valor
            FROM raw WHERE categoria IS NOT NULL GROUP BY 1 ORDER BY linhas DESC
            """
        ).fetch_df(),
    )

    # D) duplicatas
    show(
        "D duplicatas de (afm_aps,codigo,item)",
        c.execute(
            """
            WITH d AS (
              SELECT afm_aps, codigo, item, count(*) AS n,
                     sum(valor_total) AS soma, min(valor_total) AS vmin, max(valor_total) AS vmax,
                     min(_src_year) AS ano
              FROM raw GROUP BY 1,2,3 HAVING count(*)>1
            )
            SELECT ano, count(*) AS chaves_dup, sum(n) AS linhas_envolvidas,
                   sum(n-1) AS excedente,
                   round(sum(soma - vmax*n),2) AS valor_duplicado_estimado,
                   count(*) FILTER (WHERE vmin<>vmax) AS com_valores_diferentes
            FROM d GROUP BY 1 ORDER BY 1
            """
        ).fetch_df(),
    )

    # E) datas sujas
    show(
        "E1 assinatura_afm_aps por ano (faixas suspeitas)",
        c.execute(
            """
            SELECT _src_year AS ano, count(*) AS preenchidas,
                   count(*) FILTER (WHERE assinatura_afm_aps < date '2019-01-01') AS antes_2019,
                   count(*) FILTER (WHERE assinatura_afm_aps > date '2026-12-31') AS depois_2026,
                   count(*) FILTER (WHERE assinatura_afm_aps < data_geracao_afm_aps) AS antes_da_geracao,
                   min(assinatura_afm_aps) AS vmin, max(assinatura_afm_aps) AS vmax
            FROM raw WHERE assinatura_afm_aps IS NOT NULL GROUP BY 1 ORDER BY 1
            """
        ).fetch_df(),
    )
    show(
        "E2 prazo_entrega distribuição",
        c.execute(
            """
            SELECT _src_year AS ano,
                   round(median(try_cast(prazo_entrega AS DOUBLE)),1) AS mediana,
                   round(quantile_cont(try_cast(prazo_entrega AS DOUBLE),0.9),1) AS p90,
                   max(try_cast(prazo_entrega AS DOUBLE)) AS vmax,
                   count(*) FILTER (WHERE try_cast(prazo_entrega AS DOUBLE) > 365) AS acima_365d
            FROM raw GROUP BY 1 ORDER BY 1
            """
        ).fetch_df(),
    )

    # F) material: valor por ano
    show(
        "F1 material (AFM/Material) por ano",
        c.execute(
            """
            SELECT _src_year AS ano, count(*) AS linhas, count(DISTINCT afm_aps) AS afms,
                   round(sum(valor_total),2) AS valor, round(median(valor_total),2) AS ticket_mediano
            FROM raw
            WHERE tipo_fornecimento='AFM' AND tipo_do_item='Material' AND valor_total IS NOT NULL
            GROUP BY 1 ORDER BY 1
            """
        ).fetch_df(),
    )
    show(
        "F2 material: concentração do valor (top N linhas)",
        c.execute(
            """
            WITH m AS (SELECT valor_total FROM raw WHERE tipo_fornecimento='AFM' AND tipo_do_item='Material' AND valor_total IS NOT NULL),
            s AS (SELECT sum(valor_total) AS tot FROM m)
            SELECT round((SELECT tot FROM s),2) AS total,
                   round(sum(valor_total) FILTER (WHERE rn<=10),2) AS top10,
                   round(sum(valor_total) FILTER (WHERE rn<=100),2) AS top100,
                   round(sum(valor_total) FILTER (WHERE rn<=1000),2) AS top1000,
                   count(*) AS linhas
            FROM (SELECT valor_total, row_number() OVER (ORDER BY valor_total DESC) AS rn FROM m)
            """
        ).fetch_df(),
    )
    show(
        "F3 material por familia: top 15 por valor",
        c.execute(
            """
            SELECT familia_catalogo, count(*) AS linhas, count(DISTINCT nome_basico) AS nomes,
                   count(DISTINCT cnpj) AS cnpjs, round(sum(valor_total),2) AS valor,
                   round(median(valor_total),2) AS ticket_mediano
            FROM raw WHERE tipo_fornecimento='AFM' AND tipo_do_item='Material' AND valor_total IS NOT NULL
            GROUP BY 1 ORDER BY valor DESC LIMIT 15
            """
        ).fetch_df(),
    )

    # G) rodapé
    show(
        "G linhas sem afm_aps",
        c.execute(
            """
            SELECT _src_file, _src_row, secretaria, familia_catalogo, valor_total
            FROM raw WHERE afm_aps IS NULL
            """
        ).fetch_df(),
    )
    show(
        "H classificacao_familia e tipo_calculo",
        c.execute(
            """
            SELECT classificacao_familia, tipo_calculo, count(*) AS linhas, round(sum(valor_total),2) AS valor
            FROM raw GROUP BY 1,2 ORDER BY linhas DESC
            """
        ).fetch_df(),
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
