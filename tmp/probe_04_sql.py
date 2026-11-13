"""Valida as construções SQL usadas no perfilamento contra o staging já gravado."""
from __future__ import annotations

import sys

import duckdb

P = r"C:\Users\Micro\source\repos\PL\nicho-bahia\data\_meta\staging\raw_2021.parquet"


def t(con: duckdb.DuckDBPyConnection, label: str, sql: str) -> None:
    try:
        df = con.execute(sql).fetch_df()
        print(f"OK   {label}: cols={list(df.columns)} rows={len(df)}")
        print(df.head(3).to_string())
    except Exception as e:
        print(f"FAIL {label}: {type(e).__name__}: {str(e)[:300]}")
    print("-" * 70)


def main() -> None:
    con = duckdb.connect()
    t(con, "view list param", f"CREATE VIEW raw AS SELECT * FROM read_parquet(['{P}'], union_by_name=true)")
    t(con, "count distinct multi", "SELECT count(DISTINCT (afm_aps, codigo, item)) AS chaves FROM raw")
    t(con, "count distinct subquery", "SELECT count(*) FROM (SELECT DISTINCT afm_aps, codigo, item FROM raw)")
    t(con, "median", "SELECT median(valor_total) AS m FROM raw")
    t(con, "quantile", "SELECT quantile_cont(valor_total, 0.1) AS p10 FROM raw")
    t(con, "year(date)", "SELECT year(data_geracao_afm_aps) AS y, count(*) FROM raw GROUP BY 1 ORDER BY 1")
    t(con, "filter agg", "SELECT count(*) FILTER (WHERE valor_total < 0) AS neg FROM raw")
    t(con, "greatest", "SELECT greatest(0.05, 0.01*100) AS g")
    t(con, "try_cast", "SELECT count(*) FILTER (WHERE try_cast(trim(cast(prazo_entrega AS VARCHAR)) AS DOUBLE) IS NOT NULL) AS n FROM raw")
    t(con, "or NULLIF", "SELECT quantile_cont(r,0.5) AS p50 FROM (SELECT valor_unitario/nullif(valor_estimado,0) AS r FROM raw) x")
    t(con, "describe", "DESCRIBE raw")
    print(con.execute("SELECT * FROM raw LIMIT 2").fetch_df().T.to_string()[:3000])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
