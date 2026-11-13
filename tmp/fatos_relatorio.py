"""Fatos exatos dos nichos recomendados e alternativas (para o relatório executivo)."""
from __future__ import annotations

import json
import sys

import pandas as pd

from nicho_bahia import paths

ESCOLHIDOS = ["89.55", "75.10", "85.40"]
ALTERNATIVAS = ["41.10", "41.20", "84.15", "89.20", "81.05"]


def main() -> None:
    d = json.loads((paths.AGGREGATES / "panel_data.json").read_text(encoding="utf-8"))
    F = {f["k"]: f for f in d["familias"]}
    MET = {"v2425": 0, "vtotal": 1, "cagr": 2, "rec": 3, "afms": 4, "ticket": 5, "teto": 6,
           "nforn": 7, "hhi": 8, "top3": 9, "disp": 10, "raio": 11, "cv": 12, "desc": 13,
           "pand": 14, "penal": 15, "tetoHist": 16, "prazo": 17, "novos": 18, "linhas": 19}

    def linha(prefixo: str) -> dict:
        chave = next(k for k in F if k.startswith(prefixo))
        info = F[chave]
        m = d["metricas"][str(info["i"])]
        saz = d["saz"].get(str(info["i"]), [])
        picos = [(mes + 1, v) for mes, v in enumerate(saz) if v and v >= 1.2]
        picos.sort(key=lambda x: -x[1])
        return {
            "familia": info["n"], "score": info["s"], "rank": info["r"], "perfil": info["pu"],
            "valor_ano": m[MET["v2425"]], "cagr": m[MET["cagr"]], "rec": m[MET["rec"]],
            "afms": m[MET["afms"]], "ticket": m[MET["ticket"]], "teto": m[MET["teto"]],
            "nforn": m[MET["nforn"]], "hhi": m[MET["hhi"]], "top3": m[MET["top3"]],
            "disp": m[MET["disp"]], "raio": m[MET["raio"]], "prazo": m[MET["prazo"]],
            "picos": picos[:3], "penal": m[MET["penal"]],
        }

    print("=== RECOMENDADOS ===")
    for p in ESCOLHIDOS:
        r = linha(p)
        print(json.dumps(r, ensure_ascii=False))
    print("\n=== ALTERNATIVAS ===")
    for p in ALTERNATIVAS:
        r = linha(p)
        print(json.dumps(r, ensure_ascii=False))

    print("\n=== ÓRGÃOS-ALVO (top 5 de cada recomendado) ===")
    score = pd.read_parquet(paths.AGGREGATES / "agg_score.parquet")
    for p in ESCOLHIDOS:
        k = score[score["familia_key"].str.startswith(p)]["familia_key"].iloc[0]
        og = pd.read_parquet(paths.AGGREGATES / "agg_ug_periodo.parquet")
        sub = og[og["familia_key"] == k].nlargest(5, "valor_real")
        print(f"\n-- {p}")
        for _, r in sub.iterrows():
            print(f"   {r['ug_fiplan'][:52]:52s} {r['secretaria'][:34]:34s} "
                  f"R$ {r['valor_real']:>12,.2f} disp={r['share_dispensa']:.2f} ticket={r['ticket_mediano']:,.0f}")

    print("\n=== ITENS-ÂNCORA (top 3 de cada) ===")
    ti = pd.read_csv(paths.WORKSPACE / "top_itens.csv", sep=";", decimal=",", encoding="utf-8-sig")
    for p in ESCOLHIDOS:
        sub = ti[ti["familia_key"].str.startswith(p)].nlargest(3, "ancora_score")
        print(f"\n-- {p}")
        for _, r in sub.iterrows():
            print(f"   {r['nome_basico'][:24]:24s} {str(r['um'])[:5]:5s} R$ {r['valor_real']:>12,.2f} "
                  f"p50={r['preco_mediano']:>9,.2f} p25-p75={r['preco_p25']:,.2f}-{r['preco_p75']:,.2f} "
                  f"meses={int(r['meses'])} forn={int(r['fornecedores'])} comum={r['pct_comum']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
