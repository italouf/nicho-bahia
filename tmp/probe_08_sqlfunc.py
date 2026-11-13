"""Testa funções de normalização disponíveis no DuckDB."""
from __future__ import annotations

import sys

import duckdb


def main() -> None:
    c = duckdb.connect()
    exprs = {
        "strip_accents": "strip_accents('Região São José')",
        "upper+strip": "upper(strip_accents('Região São José'))",
        "collapse": r"regexp_replace(upper(strip_accents('Região  São José ')), '\s+', ' ', 'g')",
        "trim": r"trim(regexp_replace(upper(strip_accents('  x  y ')), '\s+', ' ', 'g'))",
        "strftime": "strftime(DATE '2024-03-05', '%Y-%m')",
        "cnpj_digits": r"regexp_replace('12.345.678/0001-99', '[^0-9]', '', 'g')",
        "printf": "printf('%d:%d', 2021, 42)",
        "median": "median(x) FROM (SELECT 1 AS x UNION ALL SELECT 3)",
    }
    for name, e in exprs.items():
        try:
            print(f"OK   {name}: {c.execute('SELECT ' + e).fetchone()}")
        except Exception as ex:
            print(f"FAIL {name}: {type(ex).__name__}: {str(ex)[:150]}")
    print("\nversão:", duckdb.__version__)
    print("tem strip_accents?", "strip_accents" in c.execute("SELECT * FROM duckdb_functions()").fetch_df()["function_name"].values)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
