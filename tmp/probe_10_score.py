"""Auditoria do score: decomposição por dimensão e comparação com famílias grandes."""
from __future__ import annotations

import sys

import pandas as pd

from nicho_bahia import paths

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_colwidth", 44)


def main() -> None:
    df = pd.read_parquet(paths.AGGREGATES / "agg_score.parquet")
    cols = ["familia_catalogo", "score", "rank", "valor_total_real", "valor_2024_2025_real",
            "p_demanda", "p_crescimento", "p_recorrencia", "p_fit_dispensa", "p_fragmentacao",
            "p_estabilidade_preco", "p_logistica", "penalidades"]
    print("=== TOP 12 ===")
    print(df.sort_values("score", ascending=False).head(12)[cols].to_string(index=False))

    print("\n=== famílias de grande volume que NÃO estão no top 20 ===")
    grandes = df[df["valor_total_real"] >= 3e8].sort_values("valor_total_real", ascending=False)
    top20 = set(df.sort_values("score", ascending=False).head(20)["familia_key"])
    fora = grandes[~grandes["familia_key"].isin(top20)]
    print(fora[cols].to_string(index=False))

    print("\n=== checagem de dados ausentes nas dimensões (entre elegíveis) ===")
    el = df[df["elegivel"]]
    for c in ["p_demanda", "p_crescimento", "p_recorrencia", "p_fit_dispensa",
              "p_fragmentacao", "p_estabilidade_preco", "p_logistica"]:
        print(f"  {c}: min={el[c].min():.1f} max={el[c].max():.1f} media={el[c].mean():.1f} zeros={(el[c] == 0).sum()}")

    print("\n=== métricas-chave das 10 primeiras ===")
    tcols = ["familia_catalogo", "valor_2024_2025_real", "cagr_real", "recorrencia", "n_afm",
             "ticket_p50", "pct_afm_ate_teto", "n_fornecedores", "hhi", "share_dispensa",
             "pct_valor_no_raio", "cv_mediano", "dependencia_pandemia"]
    print(df.sort_values("score", ascending=False).head(10)[tcols].to_string(index=False))

    print("\n=== sensibilidade ===")
    s = pd.read_parquet(paths.AGGREGATES / "agg_sensibilidade.parquet")
    print(s[s["presenca_no_top10_ref"]].sort_values("rank_ref").to_string(index=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
