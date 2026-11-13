"""F0 — Inventário: arquivos brutos, ambiente e ferramentas.

Saídas:
- data/_meta/inventory.json   (inventário completo, com sha256)
- logs/inventory.md           (versão legível para o gate)
"""

from __future__ import annotations

import hashlib
import platform
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from python_calamine import CalamineWorkbook

from .. import paths
from ..columns import RAW_FILES, CANONICAL
from ..logging_utils import RunLog, write_json

TRACKED_PACKAGES = (
    "pandas",
    "duckdb",
    "pyarrow",
    "polars",
    "numpy",
    "pandera",
    "pytest",
    "openpyxl",
    "python-calamine",
    "charset-normalizer",
    "jinja2",
    "rapidfuzz",
)


def sha256_of(path: Path, *, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def pkg_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def environment() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "packages": {p: pkg_version(p) for p in TRACKED_PACKAGES},
    }


def tools_registry() -> dict[str, Any]:
    """Ferramentas MCP/plugins efetivamente disponíveis na sessão (registrado em STATE.md).

    Os nomes reais foram verificados no início da sessão; ausências têm fallback declarado.
    """
    return {
        "filesystem_mcp": {"available": False, "fallback": "pwsh + read/write do harness"},
        "duckdb_mcp": {"available": False, "fallback": "duckdb via Python (instalado)"},
        "playwright_mcp": {"available": False, "fallback": "QA headless via playwright Python (a instalar no venv)"},
        "context7_mcp": {"available": False, "fallback": "help()/dir() da versão instalada"},
        "sequential_thinking": {"available": False, "fallback": "PLAN.md + TASKS.md"},
        "terminal_python": {"available": True, "fallback": ""},
        "web_search_fetch": {"available": True, "fallback": ""},
    }


def inspect_file(year: int, filename: str) -> dict[str, Any]:
    path = paths.RAW_DIR / filename
    if not path.exists():
        return {"year": year, "file": filename, "exists": False}
    st = path.stat()
    wb = CalamineWorkbook.from_path(str(path))
    sheets = list(wb.sheet_names)
    sh = wb.get_sheet_by_name(sheets[0])
    header_raw = next(iter(sh.iter_rows()))
    header = [("" if c is None else str(c)) for c in header_raw]
    return {
        "year": year,
        "file": filename,
        "exists": True,
        "size_bytes": st.st_size,
        "size_mb": round(st.st_size / 1024 / 1024, 2),
        "mtime_iso": datetime.fromtimestamp(st.st_mtime, tz=UTC).isoformat(),
        "sha256": sha256_of(path),
        "sheets": sheets,
        "n_sheets": len(sheets),
        "height_cells": sh.height,
        "n_rows_data_estimate": max(sh.height - 1, 0),
        "n_cols": len(header),
        "header": header,
        "header_blanks": [i for i, h in enumerate(header) if not h.strip()],
    }


def run(log: RunLog) -> dict[str, Any]:
    paths.ensure_dirs()
    log.section("F0 — INVENTÁRIO DE ARQUIVOS E AMBIENTE")
    env = environment()
    log(f"python {env['python']} | {env['platform']}")
    for p, v in env["packages"].items():
        log(f"  {p}: {v}")

    log(f"\npasta bruta (somente leitura): {paths.RAW_DIR}")
    extrapaths = sorted(p.name for p in paths.RAW_DIR.glob("*") if p.is_file())
    log(f"  arquivos na pasta: {len(extrapaths)}")
    for n in extrapaths:
        log(f"    - {n}")

    files = [inspect_file(r.year, r.filename) for r in RAW_FILES]
    log("\nplanilhas do contrato:")
    for f in files:
        if not f.get("exists"):
            log(f"  ! AUSENTE: {f['file']}")
            continue
        log(
            f"  {f['year']} | {f['file']} | {f['size_mb']} MB | abas={f['sheets']} | "
            f"linhas≈{f['n_rows_data_estimate']:,} | colunas={f['n_cols']}"
        )
        if f["header_blanks"]:
            log(f"      cabeçalhos em branco nas posições: {f['header_blanks']}")

    # drift de schema: compara conjuntos de rótulos normalizados
    from ..columns import norm_header

    labels_by_year = {f["year"]: {norm_header(h) for h in f["header"] if h.strip()} for f in files if f.get("exists")}
    years = sorted(labels_by_year)
    base_year = years[-1]
    drift: dict[str, Any] = {"base_year": base_year, "vs": {}}
    for y in years:
        if y == base_year:
            continue
        drift["vs"][str(y)] = {
            "ausentes_relativo_a_base": sorted(labels_by_year[base_year] - labels_by_year[y]),
            "extras_relativo_a_base": sorted(labels_by_year[y] - labels_by_year[base_year]),
        }
    log("\ndrift de schema (relativo a %d):" % base_year)
    for y, d in drift["vs"].items():
        log(f"  {y}: ausentes={d['ausentes_relativo_a_base']} extras={d['extras_relativo_a_base']}")

    missing_labels = [c.label for c in CANONICAL if norm_header(c.label) not in labels_by_year.get(base_year, set())]
    log(f"\nrótulos do contrato não encontrados em {base_year}: {missing_labels or 'nenhum'}")

    tools = tools_registry()
    log("\nferramentas da sessão:")
    for name, t in tools.items():
        log(f"  {name}: disponível={t['available']}" + (f" | fallback={t['fallback']}" if t["fallback"] else ""))

    inventory = {
        "generated_at": datetime.now(UTC).isoformat(),
        "raw_dir": str(paths.RAW_DIR),
        "workspace": str(paths.WORKSPACE),
        "raw_dir_extra_files": extrapaths,
        "environment": env,
        "files": files,
        "schema_drift": drift,
        "contract_labels_missing_in_base": missing_labels,
        "tools": tools,
    }
    out = paths.META / "inventory.json"
    write_json(out, inventory)
    log(f"\n[ok] {paths.relative(out)}")

    # versão markdown enxuta
    md = ["# Inventário F0 — arquivos brutos", ""]
    md.append("| Ano | Arquivo | MB | Linhas (aprox.) | Colunas | sha256 (12) |")
    md.append("|---|---|---|---|---|---|")
    for f in files:
        if not f.get("exists"):
            md.append(f"| {f['year']} | `{f['file']}` | - | - | - | AUSENTE |")
            continue
        md.append(
            f"| {f['year']} | `{f['file']}` | {f['size_mb']} | {f['n_rows_data_estimate']:,} | "
            f"{f['n_cols']} | `{f['sha256'][:12]}` |"
        )
    md += ["", f"Total de linhas (aprox.): **{sum(f.get('n_rows_data_estimate', 0) for f in files):,}**", ""]
    (paths.LOGS / "inventory.md").write_text("\n".join(md), encoding="utf-8")
    return inventory
