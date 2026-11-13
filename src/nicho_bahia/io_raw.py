"""Leitura dos XLSX brutos e materialização em parquet de staging.

Regras:
- A pasta de dados brutos é aberta SOMENTE PARA LEITURA.
- O cabeçalho é resolvido por alias (columns.resolve_header) e as colunas em branco
  por override posicional declarado.
- Toda conversão de tipo é feita aqui, com contagem de falhas por coluna e por arquivo.
- Nada é descartado em silêncio: colunas não mapeadas e linhas problemáticas são logadas.

O staging preserva 1 linha de planilha = 1 linha de parquet (nenhuma deduplicação aqui).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
from python_calamine import CalamineWorkbook

from . import paths
from .columns import CANONICAL, KIND_BY_NAME, RAW_FILES, RawFile, resolve_header
from .logging_utils import RunLog

TYPE_MAP: dict[str, pa.DataType] = {
    "text": pa.string(),
    "num": pa.float64(),
    "int": pa.int32(),
    "date": pa.date32(),
}

META_FIELDS: tuple[pa.Field, ...] = (
    pa.field("_src_file", pa.string()),
    pa.field("_src_sheet", pa.string()),
    pa.field("_src_row", pa.int32()),
    pa.field("_src_year", pa.int16()),
)

STAGING_SCHEMA: pa.Schema = pa.schema(
    list(META_FIELDS) + [pa.field(c.name, TYPE_MAP[c.kind]) for c in CANONICAL]
)

CHUNK_ROWS = 50_000

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%d-%m-%Y",
    "%d/%m/%y",
    "%Y/%m/%d",
)

# strings que representam ausência
_EMPTY_TOKENS = frozenset({"", "-", "--", "nan", "none", "null", "n/a", "na"})


# --- conversores elementares ---------------------------------------------------------
def as_text(v: Any) -> str | None:
    """Converte qualquer célula em texto limpo (sem espaços nas pontas)."""
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        if s == "":
            return None
        return s
    if isinstance(v, bool):
        return "Sim" if v else "Não"
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        if v.is_integer():
            return str(int(v))
        return repr(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()[:10]
    return str(v).strip() or None


def parse_br_number(s: str) -> float | None:
    """Converte texto numérico brasileiro/americano em float.

    Aceita '1.234,56' (BR), '1234.56' (US), '1,234.56' (US com milhar).
    """
    t = s.strip()
    if t.lower() in _EMPTY_TOKENS:
        return None
    t = t.replace("R$", "").replace(" ", "").replace("\u00a0", "")
    if t.count(",") and t.count("."):
        # o último separador é o decimal
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif t.count(","):
        # vírgula decimal (padrão BR) -> 1,5 ; mas '1,234' é ambíguo: assume decimal
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def as_num(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    if isinstance(v, str):
        return parse_br_number(v)
    return None


def as_int(v: Any) -> int | None:
    f = as_num(v)
    if f is None:
        return None
    return int(f)


def as_date(v: Any) -> date | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        t = v.strip()
        if t.lower() in _EMPTY_TOKENS:
            return None
        t = t.split(" ")[0].split("T")[0] if (t[:4].isdigit() or "/" in t) else t
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(t, fmt).date()
            except ValueError:
                continue
        return None
    return None


CONVERTERS = {"text": as_text, "num": as_num, "int": as_int, "date": as_date}


@dataclass
class ColumnStats:
    """Contagens de conversão por coluna (auditoria de perda de informação)."""

    converted_ok: int = 0
    empty_in: int = 0
    coercion_failed: int = 0
    failed_samples: list[str] = field(default_factory=list)


@dataclass
class StageResult:
    year: int
    file: str
    sheet: str
    n_rows: int
    n_cols_source: int
    n_cols_mapped: int
    dropped_columns: list[dict[str, object]]
    resolution: list[dict[str, object]]
    per_column: dict[str, ColumnStats]
    output: Path
    size_mb: float


def _stage_schema() -> pa.Schema:
    return STAGING_SCHEMA


def read_header_and_rows(path: Path) -> tuple[list[str], str, list[str], Iterator[Any]]:
    """Abre o XLSX e devolve (header, nome_aba, abas, iterador de linhas de dados)."""
    wb = CalamineWorkbook.from_path(str(path))
    sheet_names = list(wb.sheet_names)
    if not sheet_names:
        raise ValueError(f"{path.name}: arquivo sem abas")
    sheet = sheet_names[0]
    sh = wb.get_sheet_by_name(sheet)
    it = sh.iter_rows()
    header_raw = next(it)
    header = [("" if c is None else str(c)) for c in header_raw]
    return header, sheet, sheet_names, it


def stage_file(raw: RawFile, log: RunLog) -> StageResult:
    """Converte um XLSX em parquet de staging com esquema canônico explícito."""
    src = paths.RAW_DIR / raw.filename
    if not src.exists():
        raise FileNotFoundError(f"arquivo bruto não encontrado: {src}")
    dest = paths.STAGED_FILES[raw.year]

    header, sheet, sheet_names, rows = read_header_and_rows(src)
    mapping, events = resolve_header(header, raw)

    mapped = [m for m in mapping if m is not None]
    missing = [c.name for c in CANONICAL if c.name not in set(mapped)]
    dropped = [e for e in events if e["canonical"] is None and str(e["raw_label"]).strip() != ""]

    log(f"\n[{raw.year}] {raw.filename}")
    log(f"  aba={sheet!r} abas_no_arquivo={sheet_names}")
    log(f"  colunas na planilha={len(header)} mapeadas={len(mapped)} ausentes_do_arquivo={len(missing)}")
    for e in events:
        if e["canonical"] is not None and e["resolved_by"] == "posicional":
            log(f"  ! mapeamento POSICIONAL: índice {e['index']} (rótulo em branco) -> {e['canonical']}")
    for d in dropped:
        log(f"  ! coluna descartada: índice {d['index']} rótulo={d['raw_label']!r}")
    if missing:
        log(f"  ! colunas canônicas ausentes neste arquivo: {missing}")

    # colunas de dados efetivamente presentes (na ordem canônica) -> índice na planilha
    col_index: dict[str, int] = {str(m): i for i, m in enumerate(mapping) if m is not None}

    stats: dict[str, ColumnStats] = {c.name: ColumnStats() for c in CANONICAL}
    schema = _stage_schema()
    n_rows = 0
    writer = pq.ParquetWriter(dest, schema, compression="snappy")

    def flush(buf: dict[str, list[Any]]) -> None:
        arrays = []
        for f in schema:
            arrays.append(pa.array(buf[f.name], type=f.type))
        writer.write_table(pa.Table.from_arrays(arrays, schema=schema))

    buf: dict[str, list[Any]] = {name: [] for name in schema.names}
    src_row = 0
    try:
        for row in rows:
            src_row += 1
            for name in schema.names[4:]:
                st = stats[name]
                if name not in col_index:
                    buf[name].append(None)
                    st.empty_in += 1
                    continue
                i = col_index[name]
                v = row[i] if i < len(row) else None
                conv = CONVERTERS[KIND_BY_NAME[name]](v)
                if conv is None:
                    if v is None or (isinstance(v, str) and v.strip() == ""):
                        st.empty_in += 1
                    else:
                        st.coercion_failed += 1
                        if len(st.failed_samples) < 5:
                            st.failed_samples.append(f"{src_row}:{v!r}")
                    buf[name].append(None)
                else:
                    st.converted_ok += 1
                    buf[name].append(conv)
            buf["_src_file"].append(raw.filename)
            buf["_src_sheet"].append(sheet)
            buf["_src_row"].append(src_row)
            buf["_src_year"].append(raw.year)
            n_rows += 1
            if n_rows % CHUNK_ROWS == 0:
                flush(buf)
                buf = {name: [] for name in schema.names}
                log(f"  ... {n_rows:,} linhas processadas")
        if any(buf[name] for name in schema.names):
            flush(buf)
    finally:
        writer.close()

    n_fail = sum(s.coercion_failed for s in stats.values())
    log(f"  linhas de dados: {n_rows:,}")
    log(f"  falhas de conversão (todas as colunas): {n_fail:,}")
    for name, s in stats.items():
        if s.coercion_failed:
            log(f"    - {name}: {s.coercion_failed:,} falhas, ex.: {s.failed_samples}")
    size_mb = dest.stat().st_size / 1024 / 1024
    log(f"  -> {paths.relative(dest)} ({size_mb:.1f} MB)")

    return StageResult(
        year=raw.year,
        file=raw.filename,
        sheet=sheet,
        n_rows=n_rows,
        n_cols_source=len(header),
        n_cols_mapped=len(mapped),
        dropped_columns=dropped,
        resolution=events,
        per_column=stats,
        output=dest,
        size_mb=round(size_mb, 2),
    )


def stage_all(log: RunLog) -> list[StageResult]:
    """Processa todos os arquivos brutos (idempotente: sobrescreve o staging)."""
    results = []
    for raw in RAW_FILES:
        results.append(stage_file(raw, log))
    return results


def iter_raw_headers() -> Iterable[tuple[int, str, list[str], list[str]]]:
    """Itera (ano, arquivo, abas, header) de cada arquivo bruto, sem ler o corpo."""
    for raw in RAW_FILES:
        src = paths.RAW_DIR / raw.filename
        header, _sheet, sheet_names, _rows = read_header_and_rows(src)
        yield raw.year, raw.filename, sheet_names, header
