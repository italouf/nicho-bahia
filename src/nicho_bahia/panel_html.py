"""Shim de compatibilidade: o painel agora vive em `nicho_bahia.panel`.

Mantido para que `build.py` (e qualquer import externo) continue funcionando com
`from nicho_bahia import panel_html; panel_html.render(...)`. Permite rollback em uma linha:
basta restaurar a versão anterior deste arquivo.
"""

from __future__ import annotations

from .panel import BODY, CSS, JS_CHARTS, JS_CORE, render

__all__ = ["render", "CSS", "BODY", "JS_CORE", "JS_CHARTS"]
