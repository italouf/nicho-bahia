"""F0 probe: inventario dos XLSX brutos (somente leitura).

Le abas, dimensoes, cabecalho e primeiras linhas. Nao escreve na pasta de dados brutos.
"""
from __future__ import annotations

import json
import os
import sys
from glob import glob

from python_calamine import CalamineWorkbook

RAW_DIR = r"C:\Users\Micro\source\repos\PL\compras 2021-2025"


def main() -> None:
    files = sorted(glob(os.path.join(RAW_DIR, "*.xlsx")))
    out = []
    for f in files:
        base = os.path.basename(f)
        if base.startswith("~$"):
            continue
        info = {
            "file": base,
            "size_mb": round(os.path.getsize(f) / 1024 / 1024, 2),
            "sheets": [],
        }
        print("=" * 100)
        print(f"ARQUIVO: {base}  ({info['size_mb']} MB)")
        wb = CalamineWorkbook.from_path(f)
        print(f"  abas: {wb.sheet_names}")
        for sname in wb.sheet_names:
            sh = wb.get_sheet_by_name(sname)
            dims = {
                "height": sh.height,
                "width": sh.width,
                "total_height": sh.total_height,
                "start": sh.start,
                "end": sh.end,
            }
            head = []
            for i, r in enumerate(sh.iter_rows()):
                if i >= 4:
                    break
                head.append(r)
            ncols = max((len(r) for r in head), default=0)
            meta = {
                "name": sname,
                "dimensions": dims,
                "ncols": ncols,
                "header_preview": [[str(c) for c in r] for r in head[:3]],
            }
            info["sheets"].append(meta)
            print(f"  -- aba '{sname}' dims={dims} ncols(header visto)={ncols}")
            for k, r in enumerate(head[:3]):
                cells = [str(c) for c in r]
                print(f"     [L{k}] {json.dumps(cells, ensure_ascii=False)[:1200]}")
        out.append(info)
    print("\n" + "=" * 100)
    with open(r"C:\Users\Micro\source\repos\PL\nicho-bahia\tmp\inventory_raw.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
