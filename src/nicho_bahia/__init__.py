"""nicho-bahia: seleção de nicho em compras públicas da Bahia (2021-2025)."""

from __future__ import annotations

__version__ = "0.1.0"


def main() -> None:
    from .cli import main as _main

    raise SystemExit(_main())
