"""Valida que o mapa de canais do config.yaml cobre 100% dos rótulos observados na base."""
from __future__ import annotations

import sys

import duckdb
import yaml

FILES = [
    rf"C:\Users\Micro\source\repos\PL\nicho-bahia\data\_meta\staging\raw_{y}.parquet"
    for y in (2021, 2022, 2023, 2024, 2025)
]


def main() -> None:
    cfg = yaml.safe_load(open(r"C:\Users\Micro\source\repos\PL\nicho-bahia\config.yaml", encoding="utf-8"))
    mapa = cfg["dispensa"]["mapa_canal"]
    c = duckdb.connect()
    lista = "[" + ", ".join(f"'{f}'" for f in FILES) + "]"
    c.execute(f"CREATE VIEW raw AS SELECT * FROM read_parquet({lista}, union_by_name=true)")
    df = c.execute(
        "SELECT coalesce(forma_contratacao,'(NULO)') AS v, count(*) AS n FROM raw GROUP BY 1 ORDER BY n DESC"
    ).fetch_df()
    print(f"rótulos distintos observados: {len(df)}")
    faltando = []
    for r in df.to_dict("records"):
        v = r["v"]
        ok = v in mapa
        if not ok:
            faltando.append(v)
        print(f"  {'OK  ' if ok else 'FALTA'} {v!r:62s} n={r['n']:,} -> {mapa.get(v)}")
    print("\nfaltando:", faltando or "nenhum")
    # valores do config que não existem na base
    extra = [k for k in mapa if k not in set(df["v"])]
    print("no config sem uso na base:", extra or "nenhum")

    # valida regiões
    reg = c.execute(
        "SELECT coalesce(regiao_local_entrega,'(NULO)') AS v, count(*) AS n FROM raw GROUP BY 1 ORDER BY n DESC"
    ).fetch_df()
    dentro = set(cfg["logistica"]["regioes_dentro_raio"])
    indef = set(cfg["logistica"]["regioes_indefinidas"])
    print("\nregiões observadas:", len(reg))
    for r in reg.to_dict("records"):
        v = r["v"]
        b = "DENTRO" if v in dentro else ("INDEF" if v in indef else "FORA")
        print(f"  {b:6s} {v!r:58s} n={r['n']:,}")
    print("\nconfig DENTRO sem match:", sorted(dentro - set(reg["v"])))
    print("config INDEF sem match:", sorted(indef - set(reg["v"])))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
