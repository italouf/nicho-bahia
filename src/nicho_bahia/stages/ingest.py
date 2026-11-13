"""F0/F1 — Ingestão: XLSX -> parquet de staging (camada crua tipada).

Não deduplica, não filtra, não corrige valores: apenas mapeia colunas e converte tipos.
Gera data/_meta/staging_manifest.json com contagens por arquivo/coluna e sha256 do parquet.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .. import io_raw, paths
from ..logging_utils import RunLog, write_json


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(log: RunLog) -> dict[str, Any]:
    paths.ensure_dirs()
    log.section("F0/F1 — INGESTÃO: XLSX -> PARQUET (staging)")
    results = io_raw.stage_all(log)

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "chunk_rows": io_raw.CHUNK_ROWS,
        "schema": [{"name": f.name, "type": str(f.type)} for f in io_raw.STAGING_SCHEMA],
        "files": [],
    }
    total = 0
    for r in results:
        total += r.n_rows
        manifest["files"].append(
            {
                "year": r.year,
                "file": r.file,
                "sheet": r.sheet,
                "n_rows": r.n_rows,
                "n_cols_source": r.n_cols_source,
                "n_cols_mapped": r.n_cols_mapped,
                "dropped_columns": r.dropped_columns,
                "resolution": r.resolution,
                "coercion_failures": {
                    k: {
                        "coercion_failed": v.coercion_failed,
                        "empty_in": v.empty_in,
                        "converted_ok": v.converted_ok,
                        "samples": v.failed_samples,
                    }
                    for k, v in r.per_column.items()
                    if v.coercion_failed or v.empty_in
                },
                "output": paths.relative(r.output),
                "size_mb": r.size_mb,
                "sha256": _sha256(r.output),
            }
        )
    manifest["total_rows"] = total

    out = paths.META / "staging_manifest.json"
    write_json(out, manifest)
    log(f"\ntotal de linhas em staging: {total:,}")
    log(f"[ok] {paths.relative(out)}")
    return manifest
