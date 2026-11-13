"""Substitui o bloco JS do panel_html.py pelo novo (tmp/new_js.js)."""
from __future__ import annotations

import io
import sys
from pathlib import Path

ALVO = Path(r"C:\Users\Micro\source\repos\PL\nicho-bahia\src\nicho_bahia\panel_html.py")
NOVO = Path(r"C:\Users\Micro\source\repos\PL\nicho-bahia\tmp\new_js.js")


def main() -> None:
    src = io.open(ALVO, encoding="utf-8").read()
    ini = src.index('JS = r"""')
    fim = src.index('"""', ini + len('JS = r"""'))
    js = io.open(NOVO, encoding="utf-8").read()
    if '"""' in js:
        raise SystemExit("o novo JS contém tripla aspa — não pode ser embutido como raw string")
    novo = src[: ini + len('JS = r"""')] + "\n" + js + src[fim:]
    io.open(ALVO, "w", encoding="utf-8").write(novo)
    print(f"JS substituído: {len(src)} -> {len(novo)} bytes")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
