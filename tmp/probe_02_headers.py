"""F0 probe 2: cabecalhos completos por arquivo + tipos de celula + contagem de linhas.

Objetivo: detectar drift de schema entre os 5 arquivos antes de qualquer tratamento.
"""
from __future__ import annotations

import json
import os
import sys
from glob import glob

from python_calamine import CalamineWorkbook

RAW_DIR = r"C:\Users\Micro\source\repos\PL\compras 2021-2025"
OUT = r"C:\Users\Micro\source\repos\PL\nicho-bahia\tmp\headers_raw.json"

# colunas cujo tipo de celula queremos testar
PROBE_COLS = [
    "COD. SECRETARIA",
    "QTD CONTRATADA",
    "VALOR DETALHE",
    "VALOR UNITÁRIO",
    "VALOR TOTAL",
    "CNPJ",
    "DATA GERAÇÃO da AFM/APS ",
    "Assinatura da AFM/APS",
    "VALOR ESTIMADO",
    "ANO GERAÇÃO da AFM/APS",
    "MES GERAÇÃO da AFM/APS",
]


def cell_repr(v: object) -> str:
    return f"{type(v).__name__}:{v!r}"


def main() -> None:
    files = sorted(glob(os.path.join(RAW_DIR, "*.xlsx")))
    all_info: dict[str, dict] = {}
    headers_by_file: dict[str, list[str]] = {}

    for f in files:
        base = os.path.basename(f)
        if base.startswith("~$"):
            continue
        wb = CalamineWorkbook.from_path(f)
        sname = wb.sheet_names[0]
        sh = wb.get_sheet_by_name(sname)
        hdr = None
        sample = []
        n = 0
        for i, row in enumerate(sh.iter_rows()):
            if i == 0:
                hdr = [("" if c is None else str(c)) for c in row]
                continue
            if len(sample) < 3:
                sample.append(row)
            n += 1
        assert hdr is not None
        headers_by_file[base] = hdr

        # posicoes das colunas de interesse e tipos observados
        idx = {h.strip(): i for i, h in enumerate(hdr) if h.strip()}
        probes = {}
        for cn in PROBE_COLS:
            i = idx.get(cn.strip())
            if i is None:
                probes[cn] = "AUSENTE"
                continue
            probes[cn] = [cell_repr(r[i]) if i < len(r) else "<sem celula>" for r in sample]

        all_info[base] = {
            "sheet": sname,
            "n_cols": len(hdr),
            "n_rows_dados": n,
            "header": hdr,
            "header_vazios": [i for i, h in enumerate(hdr) if not h.strip()],
            "header_duplicados": sorted({h.strip() for h in hdr if h.strip() and [x.strip() for x in hdr].count(h.strip()) > 1}),
            "probes_tipos": probes,
        }
        print(f"{base}: sheet={sname!r} ncols={len(hdr)} linhas_dados={n}")
        if all_info[base]["header_vazios"]:
            print(f"   header vazios nas posicoes: {all_info[base]['header_vazios']}")
        if all_info[base]["header_duplicados"]:
            print(f"   header DUPLICADOS: {all_info[base]['header_duplicados']}")

    # comparacao de conjuntos de header
    print("\n=== COMPARACAO DE SCHEMAS ===")
    names = list(headers_by_file)
    stripped = {k: [h.strip() for h in v] for k, v in headers_by_file.items()}
    base_set = set(stripped[names[0]])
    for k in names[1:]:
        s = set(stripped[k])
        print(f"{names[0]}  vs  {k}:")
        print(f"   so em A: {sorted(base_set - s)}")
        print(f"   so em B: {sorted(s - base_set)}")

    print("\n=== TIPOS OBSERVADOS (3 linhas) ===")
    for k, v in all_info.items():
        print(f"\n-- {k}")
        for cn, t in v["probes_tipos"].items():
            print(f"   {cn!r}: {t}")

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(all_info, fh, ensure_ascii=False, indent=1)
    print(f"\n[ok] {OUT}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
