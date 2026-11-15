"""Montagem do painel HTML único: CSS + esqueleto + dados + ECharts + JS.

Fachada usada por `stages/build.py` (via `nicho_bahia.panel_html.render`).
Os dados viajam num `<script type="application/json">` inerte: o parser não executa 1,6 MB
de objeto literal antes do primeiro paint (V8 — orçamento de FCP).
"""

from __future__ import annotations

import json
from typing import Any

from .body import BODY
from .js_charts import JS_CHARTS
from .js_core import JS_CORE
from .tokens_css import CSS

__all__ = ["CSS", "BODY", "JS_CORE", "JS_CHARTS", "render"]


def render(dados: dict[str, Any], echarts_js: str, *, versao: str = "1.0", gerado: str = "") -> str:
    """Monta o HTML final, com dados e biblioteca embutidos (zero requisições externas)."""
    payload = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    # `</` dentro do JSON encerraria o <script>; escapar como \u003c é inofensivo para o parse
    payload = payload.replace("</", "\\u003c/")
    core = JS_CORE.replace("__DATA__", "")
    return (
        "<!DOCTYPE html>\n<html lang=\"pt-BR\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        "<meta name=\"color-scheme\" content=\"light\">\n"
        "<title>Painel de decisão de nicho — compras públicas da Bahia 2021–2025</title>\n"
        f"<!-- nicho-bahia · versão {versao} · gerado em {gerado} · 100% offline, sem requisições externas -->\n"
        f"<style>{CSS}</style>\n</head>\n<body>\n{BODY}\n"
        f"<script type=\"application/json\" id=\"dados\">{payload}</script>\n"
        f"<script>{echarts_js}</script>\n"
        f"<script>{core}</script>\n"
        f"<script>{JS_CHARTS}</script>\n"
        "</body>\n</html>\n"
    )
