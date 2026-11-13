"""F0 probe 3: alinhamento posicional dos cabecalhos (2021 vs 2022 vs 2025)."""
from __future__ import annotations

import json
import sys

P = r"C:\Users\Micro\source\repos\PL\nicho-bahia\tmp\headers_raw.json"


def main() -> None:
    d = json.load(open(P, encoding="utf-8"))
    k25 = "SIMPAS_VOLUME_DE_COMPRAS_ANO_2025 1 (1).xlsx"
    k21 = "SIMPAS_VOLUME_DE_COMPRAS_GERAL_2021.xlsx"
    k22 = "SIMPAS_VOLUME_DE_COMPRAS_GERAL_2022.xlsx"
    k23 = "SIMPAS_VOLUME_DE_COMPRAS_GERAL_2023 1.xlsx"
    k24 = "SIMPAS_VOLUME_DE_COMPRAS_GERAL_2024 2.xlsx"

    h25 = [h.strip() for h in d[k25]["header"]]
    print("TOTAL 2025:", len(h25))
    for i, h in enumerate(h25):
        print(f"{i:3d} | {h}")

    print("\n=== posicionais divergentes ===")
    for k in (k21, k22, k23, k24):
        hk = [h.strip() for h in d[k]["header"]]
        print(f"\n-- {k} (n={len(hk)})")
        for i in range(max(len(hk), len(h25))):
            a = h25[i] if i < len(h25) else "<FIM>"
            b = hk[i] if i < len(hk) else "<FIM>"
            if a != b:
                print(f"   [{i}] 2025={a!r:55s} | este={b!r}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
