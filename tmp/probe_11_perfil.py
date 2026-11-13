"""Confere o rótulo de perfil de uso e o top-20 do score."""
from __future__ import annotations

import sys

import pandas as pd

from nicho_bahia import paths


def main() -> None:
    df = pd.read_parquet(paths.AGGREGATES / "agg_score.parquet")
    cols = ["rank", "familia_catalogo", "score", "perfil_uso", "share_duravel",
            "valor_2024_2025_real", "n_fornecedores", "hhi"]
    print("=== TOP 10 ===")
    print(df.nsmallest(10, "rank")[cols].to_string(index=False))
    print("\n=== distribuição do perfil ===")
    print(df["perfil_uso"].value_counts().to_string())
    print("\n=== NÃO consumíveis no top 20 ===")
    top20 = df.nsmallest(20, "rank")
    print(top20[top20["perfil_uso"] != "consumo recorrente"][cols].to_string(index=False))
    print("\n=== famílias de consumo recorrente que ficaram de fora do top 10 ===")
    rec = df[(df["perfil_uso"] == "consumo recorrente")].nsmallest(15, "rank")
    print(rec[cols].to_string(index=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
