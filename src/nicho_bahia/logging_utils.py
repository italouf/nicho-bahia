"""Utilitários de log e serialização determinística.

Todo log técnico vai para logs/ (linha do tempo) e para stdout resumido.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from . import paths


def _json_default(o: Any) -> Any:
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, Path):
        return str(o)
    if hasattr(o, "item"):  # numpy scalars
        return o.item()
    raise TypeError(f"não serializável: {type(o)!r}")


def dumps(obj: Any, *, indent: int | None = None) -> str:
    """JSON estável (chaves ordenadas) — usado para hashes e comparação."""
    return json.dumps(obj, ensure_ascii=False, indent=indent, sort_keys=True, default=_json_default)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(obj, indent=2), encoding="utf-8")


class RunLog:
    """Log de execução: acumula linhas e grava em logs/<nome>.log ao finalizar."""

    def __init__(self, name: str, *, echo: bool = True) -> None:
        paths.LOGS.mkdir(parents=True, exist_ok=True)
        self.path = paths.LOGS / f"{name}.log"
        self.echo = echo
        self.lines: list[str] = []
        self._fh = self.path.open("w", encoding="utf-8")

    def __call__(self, msg: str = "") -> None:
        self.lines.append(msg)
        self._fh.write(msg + "\n")
        self._fh.flush()
        if self.echo:
            print(msg)

    def kv(self, key: str, value: Any) -> None:
        self(f"  {key}: {value}")

    def section(self, title: str) -> None:
        self("")
        self("=" * 78)
        self(title)
        self("=" * 78)

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "RunLog":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def configure_stdout() -> None:
    """Força UTF-8 no stdout (Windows console costuma usar cp1252)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:  # pragma: no cover - ambientes sem reconfigure
        pass
