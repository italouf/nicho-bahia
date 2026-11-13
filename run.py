#!/usr/bin/env python
"""Ponto de entrada do pipeline nicho-bahia.

Uso:
    uv run python run.py --stage inventory
    uv run python run.py --stage ingest
    uv run python run.py --stage all
"""

from __future__ import annotations

import sys

from nicho_bahia.cli import main

if __name__ == "__main__":
    sys.exit(main())
